"""Evidence-only deployer history from the configured Blockscout API."""

from datetime import datetime, timezone
import os

import requests

from config import BLOCKSCOUT_API


TIMEOUT_SECONDS = 8
MAX_HISTORY_PAGES = 3
RECENT_FUNDING_HOURS = 24


def _address(value):
    if isinstance(value, dict):
        value = value.get("hash")
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        return None
    try:
        int(value[2:], 16)
    except ValueError:
        return None
    return value


def _timestamp(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _get_json(path, params=None):
    base = str(BLOCKSCOUT_API or "").rstrip("/")
    if not base:
        return None
    request_params = dict(params or {})
    api_key = os.environ.get("BLOCKSCOUT_API_KEY")
    if api_key:
        # Blockscout's keyed API accepts the key as an `apikey` parameter.
        request_params["apikey"] = api_key
    try:
        response = requests.get(
            f"{base}/{path.lstrip('/')}",
            params=request_params or None,
            timeout=TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            return None
        payload = response.json()
        return payload if isinstance(payload, dict) else None
    except (requests.RequestException, ValueError):
        return None


def _from_address(transaction):
    return _address(transaction.get("from"))


def _to_address(transaction):
    return _address(transaction.get("to"))


def analyze_deployer_history(token_address, now=None):
    """Trace contract creation, prior contract deployments and recent funding.

    This reports observable relationships only. A shared funder or prior
    contract deployment is not, by itself, evidence of fraud or coordination.
    """
    result = {
        "status": "UNAVAILABLE",
        "source": "Blockscout API",
        "token_address": token_address,
        "creation_transaction": None,
        "creation_block": None,
        "deployer": None,
        "deployer_type": "UNKNOWN",
        "prior_contract_creations": None,
        "history_complete": False,
        "recent_funding": None,
        "funding_history_complete": False,
        "signals": [],
        "warnings": [],
    }

    token_address = _address(token_address)
    if not token_address:
        result["warnings"].append("Token address is invalid; deployer history was not queried.")
        return result

    address_info = _get_json(f"addresses/{token_address}")
    creation_hash = None
    if isinstance(address_info, dict):
        creation_hash = address_info.get("creation_tx_hash")

    creation_tx = _get_json(f"transactions/{creation_hash}") if creation_hash else None
    if not isinstance(creation_tx, dict):
        result["warnings"].append(
            "Explorer did not provide a readable contract-creation transaction; deployer history is unknown."
        )
        return result

    deployer = _from_address(creation_tx)
    creation_block = creation_tx.get("block")
    if isinstance(creation_block, dict):
        creation_block = creation_block.get("number")
    try:
        creation_block = int(creation_block)
    except (TypeError, ValueError):
        creation_block = None

    if not deployer:
        result["warnings"].append("Creation transaction sender was unavailable.")
        return result

    from_info = creation_tx.get("from") if isinstance(creation_tx.get("from"), dict) else {}
    deployer_type = "CONTRACT" if from_info.get("is_contract") is True else "EOA"
    result.update({
        "status": "PARTIAL",
        "creation_transaction": creation_hash,
        "creation_block": creation_block,
        "deployer": deployer,
        "deployer_type": deployer_type,
    })

    if deployer_type == "CONTRACT":
        result["warnings"].append(
            "The creation transaction was sent by a contract/factory; the originating wallet was not resolved."
        )
        return result

    pages = 0
    next_params = None
    prior_creations = []
    reached_creation = False
    while pages < MAX_HISTORY_PAGES:
        payload = _get_json(
            f"addresses/{deployer}/transactions",
            params={"filter": "from", **(next_params or {})},
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            break
        pages += 1
        items = payload["items"]
        if not items:
            reached_creation = True
            break
        for transaction in items:
            block = transaction.get("block")
            if isinstance(block, dict):
                block = block.get("number")
            try:
                block = int(block)
            except (TypeError, ValueError):
                continue
            if creation_block is not None and block >= creation_block:
                continue
            # Transactions are returned newest first. Anything before the
            # token's creation is eligible evidence; it is not a reason to
            # stop scanning the current page.
            created = transaction.get("created_contract")
            created_address = _address(created)
            if created_address:
                prior_creations.append({
                    "address": created_address,
                    "transaction": transaction.get("hash"),
                    "block": block,
                })
        next_params = payload.get("next_page_params")
        if not next_params:
            reached_creation = True
            break

    result["prior_contract_creations"] = len(prior_creations)
    result["prior_contract_samples"] = prior_creations[:10]
    result["history_complete"] = reached_creation

    now = now or datetime.now(timezone.utc)
    funding = None
    funding_complete = False
    funding_next_params = None
    funding_pages = 0
    funding_query_failed = False
    while funding_pages < MAX_HISTORY_PAGES and not funding:
        funding_payload = _get_json(
            f"addresses/{deployer}/transactions",
            params={"filter": "to", **(funding_next_params or {})},
        )
        if not isinstance(funding_payload, dict) or not isinstance(funding_payload.get("items"), list):
            funding_query_failed = True
            break
        funding_pages += 1
        funding_items = funding_payload["items"]
        if not funding_items:
            funding_complete = True
            break
        for transaction in funding_items:
            if _to_address(transaction) != deployer:
                continue
            value = transaction.get("value")
            try:
                value_wei = int(value or 0)
            except (TypeError, ValueError):
                continue
            tx_block = transaction.get("block")
            if isinstance(tx_block, dict):
                tx_block = tx_block.get("number")
            try:
                tx_block = int(tx_block)
            except (TypeError, ValueError):
                continue
            if creation_block is not None and tx_block >= creation_block:
                continue
            tx_time = _timestamp(transaction.get("timestamp"))
            if not tx_time:
                continue
            age_hours = (now - tx_time).total_seconds() / 3600
            if age_hours > RECENT_FUNDING_HOURS:
                funding_complete = True
                break
            if 0 <= age_hours <= RECENT_FUNDING_HOURS and value_wei > 0:
                funding = {
                    "from": _from_address(transaction),
                    "transaction": transaction.get("hash"),
                    "block": tx_block,
                    "timestamp": tx_time.isoformat(),
                    "value_wei": str(value_wei),
                    "hours_before_scan": round(age_hours, 2),
                }
                funding_complete = True
                break

        if funding or funding_complete:
            break
        funding_next_params = funding_payload.get("next_page_params")
        if not funding_next_params:
            funding_complete = True
            break
        # If a page has no usable timestamps, we cannot safely infer that the
        # next page is outside the 24-hour window; continue only within the cap.

    result["recent_funding"] = funding
    result["funding_history_complete"] = funding_complete and not funding_query_failed
    result["status"] = "COMPLETE" if reached_creation else "PARTIAL"

    if prior_creations:
        result["signals"].append(
            f"The deployer wallet created {len(prior_creations)} other contract(s) in the history pages examined before this token."
        )
        if not reached_creation:
            result["warnings"].append(
                "Deployer history was paginated and is incomplete; the count is a lower bound."
            )
    elif reached_creation:
        result["signals"].append(
            "No earlier contract creations were found in the indexed deployer history. This is not proof the wallet has no other activity."
        )
    else:
        result["warnings"].append(
            "Deployer transaction history could not be fully read; prior deployment count may be incomplete."
        )

    if funding:
        result["signals"].append(
            "The deployer received native-asset funding within 24 hours before the token deployment. This is a traceable relationship, not proof of coordination or wrongdoing."
        )
    elif funding_query_failed or not funding_complete:
        result["warnings"].append("Recent inbound deployer funding could not be fully checked; no-funding result is inconclusive.")

    return result
