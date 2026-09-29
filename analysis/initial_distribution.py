"""
RobinShield Initial Mint / Distribution Analysis

Reports observed ERC-20 mint transfers originating from the zero address.

Important:
- This is observed mint/distribution activity.
- It is NOT proof of the token deployer.
- Concentrated initial issuance is reported as information.
- Concentration alone does not imply an unsafe mint mechanism.
"""

from typing import Any, Dict, List

from analysis.holders import _alchemy_request


ZERO_ADDRESS = (
    "0x0000000000000000000000000000000000000000"
)


def _normalize(address: Any) -> str:

    if not address:
        return ""

    return str(
        address
    ).lower()


def _hex_int(value: Any) -> int:

    if value is None:
        return 0

    if isinstance(value, int):
        return value

    try:

        return int(
            str(value),
            0,
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0


def analyze_initial_distribution(
    token_address: str,
) -> Dict[str, Any]:

    if not token_address:

        return {
            "status": "UNKNOWN",
            "risk": "UNKNOWN",
            "confidence": "LOW",
            "coverage": "UNKNOWN",
            "mint_found": False,
            "mint_transfer_count": 0,
            "recipient_count": 0,
            "total_minted": 0,
            "largest_recipient": None,
            "largest_percentage": None,
            "top5_percentage": None,
            "earliest_block": None,
            "earliest_transaction": None,
            "warnings": [
                "Token address was unavailable."
            ],
            "signals": [],
        }

    params = {
        "fromBlock": "0x0",
        "toBlock": "latest",
        "fromAddress": ZERO_ADDRESS,
        "contractAddresses": [
            token_address
        ],
        "category": [
            "erc20"
        ],
        "withMetadata": False,
        "excludeZeroValue": True,
        "order": "asc",
        "maxCount": "0x64",
    }

    try:

        result = _alchemy_request(
            "alchemy_getAssetTransfers",
            [
                params
            ],
        )

    except Exception as e:

        return {
            "status": "UNKNOWN",
            "risk": "UNKNOWN",
            "confidence": "LOW",
            "coverage": "UNAVAILABLE",
            "mint_found": False,
            "mint_transfer_count": 0,
            "recipient_count": 0,
            "total_minted": 0,
            "largest_recipient": None,
            "largest_percentage": None,
            "top5_percentage": None,
            "earliest_block": None,
            "earliest_transaction": None,
            "warnings": [
                "Initial mint analysis failed: "
                f"{e}"
            ],
            "signals": [],
        }

    if not isinstance(
        result,
        dict,
    ):

        return {
            "status": "UNKNOWN",
            "risk": "UNKNOWN",
            "confidence": "LOW",
            "coverage": "UNAVAILABLE",
            "mint_found": False,
            "mint_transfer_count": 0,
            "recipient_count": 0,
            "total_minted": 0,
            "largest_recipient": None,
            "largest_percentage": None,
            "top5_percentage": None,
            "earliest_block": None,
            "earliest_transaction": None,
            "warnings": [
                "Alchemy returned an invalid transfer response."
            ],
            "signals": [],
        }

    transfers = result.get(
        "transfers",
        [],
    )

    if not isinstance(
        transfers,
        list,
    ):

        transfers = []

    recipients = {}

    earliest_block = None
    earliest_transaction = None

    for transfer in transfers:

        if not isinstance(
            transfer,
            dict,
        ):

            continue

        from_address = _normalize(
            transfer.get(
                "from"
            )
        )

        if from_address != ZERO_ADDRESS.lower():

            continue

        to_address = transfer.get(
            "to"
        )

        if not to_address:

            continue

        to_normalized = _normalize(
            to_address
        )

        if (
            not to_normalized
            or to_normalized == ZERO_ADDRESS.lower()
        ):

            continue

        raw_contract = transfer.get(
            "rawContract",
            {},
        )

        if not isinstance(
            raw_contract,
            dict,
        ):

            raw_contract = {}

        amount = _hex_int(
            raw_contract.get(
                "value"
            )
        )

        if amount <= 0:

            continue

        recipients[
            to_normalized
        ] = (
            recipients.get(
                to_normalized,
                0,
            )
            + amount
        )

        block_number = _hex_int(
            transfer.get(
                "blockNum"
            )
        )

        if (
            earliest_block is None
            or (
                block_number > 0
                and block_number < earliest_block
            )
        ):

            earliest_block = block_number

            earliest_transaction = (
                transfer.get(
                    "hash"
                )
            )

    if not recipients:

        return {
            "status": "PASS",
            "risk": "LOW",
            "confidence": "MEDIUM",
            "coverage": "COMPLETE",
            "mint_found": False,
            "mint_transfer_count": 0,
            "recipient_count": 0,
            "total_minted": 0,
            "largest_recipient": None,
            "largest_percentage": None,
            "top5_percentage": None,
            "earliest_block": None,
            "earliest_transaction": None,
            "warnings": [],
            "signals": [
                "No observed ERC-20 mint transfer from "
                "the zero address was found in the "
                "available Alchemy transfer data."
            ],
        }

    ordered = sorted(
        recipients.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    total_minted = sum(
        amount
        for _, amount in ordered
    )

    largest_address = ordered[0][0]
    largest_amount = ordered[0][1]

    largest_percentage = (
        largest_amount
        / total_minted
        * 100
    )

    top5_amount = sum(
        amount
        for _, amount in ordered[:5]
    )

    top5_percentage = (
        top5_amount
        / total_minted
        * 100
    )

    warnings: List[str] = []
    signals: List[str] = []

    signals.append(
        "Observed ERC-20 mint transfers originating "
        "from the zero address."
    )

    signals.append(
        f"Earliest observed mint block: "
        f"{earliest_block}."
    )

    signals.append(
        f"Observed mint recipient count: "
        f"{len(recipients)}."
    )

    signals.append(
        f"Largest observed mint recipient: "
        f"{largest_address}."
    )

    if largest_percentage >= 50:

        warnings.append(
            "Observed mint distribution is highly "
            "concentrated; this alone does not prove "
            "an unsafe or still-mintable token."
        )

    elif largest_percentage >= 25:

        warnings.append(
            "Observed mint distribution is concentrated."
        )

    return {
        "status": (
            "WARNING"
            if warnings
            else "PASS"
        ),
        "risk": "LOW",
        "confidence": "MEDIUM",
        "coverage": "PARTIAL",
        "mint_found": True,
        "mint_transfer_count": len(
            transfers
        ),
        "recipient_count": len(
            recipients
        ),
        "total_minted": total_minted,
        "largest_recipient": largest_address,
        "largest_percentage": largest_percentage,
        "top5_percentage": top5_percentage,
        "earliest_block": earliest_block,
        "earliest_transaction": earliest_transaction,
        "warnings": warnings,
        "signals": signals,
    }