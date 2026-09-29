"""
RobinShield Supply / Mint Analysis

Detects externally callable mechanisms that may change token supply.

Important:
- view/pure getters such as totalSupply() and maxSupply()
  are NOT treated as supply-control mechanisms.
- State-changing mint/supply functions are treated as relevant.
- Missing ABI/bytecode results in UNKNOWN.
"""

from typing import Any, Dict, List, Optional


MINT_NAMES = {
    "mint",
    "mintto",
    "minttokens",
    "issuetokens",
    "issue",
    "createsupply",
    "increasesupply",
    "addtokens",
}

SUPPLY_CHANGE_NAMES = {
    "setmaxsupply",
    "settotalsupply",
    "setsupply",
    "changesupply",
    "updatesupply",
    "increasesupply",
    "decreasesupply",
    "reducesupply",
}

BURN_NAMES = {
    "burn",
    "burnfrom",
}


READ_ONLY = {
    "view",
    "pure",
}


def _normalize_name(name: Any) -> str:

    if not name:
        return ""

    return (
        str(name)
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
        .lower()
    )


def _is_burn(name: str) -> bool:

    normalized = _normalize_name(name)

    return (
        normalized in BURN_NAMES
        or normalized.startswith("burn")
    )


def _is_mint(name: str) -> bool:

    normalized = _normalize_name(name)

    if normalized in MINT_NAMES:
        return True

    if normalized.startswith("mint"):
        return True

    if "increasesupply" in normalized:
        return True

    if "createsupply" in normalized:
        return True

    if "issuetoken" in normalized:
        return True

    return False


def _is_supply_change(name: str) -> bool:

    normalized = _normalize_name(name)

    return (
        normalized in SUPPLY_CHANGE_NAMES
        or normalized.startswith("setmaxsupply")
        or normalized.startswith("settotalsupply")
    )


def _is_admin_function(name: str) -> bool:

    normalized = _normalize_name(name)

    return normalized in {
        "owner",
        "admin",
        "getowner",
        "administrator",
        "defaultadmin",
        "transferownership",
        "renounceownership",
        "grantrole",
        "revokerole",
        "hasrole",
        "getroleadmin",
    }


def analyze_supply(
    abi: Optional[List[Dict[str, Any]]] = None,
    bytecode: Optional[Any] = None,
) -> Dict[str, Any]:

    signals = []
    warnings = []

    if not abi and not bytecode:

        return {
            "status": "UNKNOWN",
            "risk": "UNKNOWN",
            "confidence": "LOW",
            "mintable": None,
            "mint_functions": [],
            "supply_controls": [],
            "burn_functions": [],
            "signals": [],
            "warnings": [
                "ABI and bytecode were unavailable; "
                "supply expansion could not be analyzed."
            ],
        }

    mint_functions = []
    supply_controls = []
    burn_functions = []
    admin_functions = []

    # -----------------------------------------------------
    # ABI analysis
    # -----------------------------------------------------

    if abi:

        for item in abi:

            if not isinstance(item, dict):
                continue

            if item.get("type") != "function":
                continue

            name = item.get("name")

            if not name:
                continue

            mutability = (
                str(
                    item.get(
                        "stateMutability",
                        "",
                    )
                )
                .lower()
            )

            normalized = _normalize_name(
                name
            )

            # ---------------------------------------------
            # Read-only functions
            # ---------------------------------------------

            if mutability in READ_ONLY:

                # Getter functions are informational only.
                # Do NOT classify totalSupply/maxSupply as
                # supply-changing controls.

                continue

            # ---------------------------------------------
            # Burn
            # ---------------------------------------------

            if _is_burn(name):

                burn_functions.append(
                    name
                )

            # ---------------------------------------------
            # Mint
            # ---------------------------------------------

            if _is_mint(name):

                mint_functions.append(
                    name
                )

            # ---------------------------------------------
            # Supply-changing controls
            # ---------------------------------------------

            if _is_supply_change(name):

                supply_controls.append(
                    name
                )

            # ---------------------------------------------
            # Ownership / admin
            # ---------------------------------------------

            if _is_admin_function(name):

                admin_functions.append(
                    name
                )

    mint_functions = sorted(
        set(mint_functions)
    )

    supply_controls = sorted(
        set(supply_controls)
    )

    burn_functions = sorted(
        set(burn_functions)
    )

    admin_functions = sorted(
        set(admin_functions)
    )

    # -----------------------------------------------------
    # No supply expansion mechanism found
    # -----------------------------------------------------

    if not mint_functions and not supply_controls:

        signals.append(
            "No recognized state-changing mint or "
            "supply-expansion functions were found "
            "in the available ABI."
        )

        if burn_functions:

            signals.append(
                "Recognized burn functions: "
                + ", ".join(
                    burn_functions
                )
                + "."
            )

        return {
            "status": "PASS",
            "risk": "LOW",
            "confidence": (
                "MEDIUM"
                if abi
                else "LOW"
            ),
            "mintable": False,
            "mint_functions": [],
            "supply_controls": [],
            "burn_functions": burn_functions,
            "signals": signals,
            "warnings": [],
        }

    # -----------------------------------------------------
    # Minting detected
    # -----------------------------------------------------

    if mint_functions:

        signals.append(
            "Recognized state-changing mint "
            "functions: "
            + ", ".join(
                mint_functions
            )
            + "."
        )

        if admin_functions:

            signals.append(
                "Ownership/admin functions are "
                "also exposed; mint authorization "
                "may be administrator-controlled."
            )

            warnings.append(
                "A state-changing mint function was "
                "detected and administrator-related "
                "functions are also present."
            )

            return {
                "status": "WARNING",
                "risk": "HIGH",
                "confidence": "MEDIUM",
                "mintable": True,
                "mint_functions": mint_functions,
                "supply_controls": supply_controls,
                "burn_functions": burn_functions,
                "signals": signals,
                "warnings": warnings,
            }

        warnings.append(
            "A state-changing mint function was "
            "detected, but its authorization could "
            "not be fully determined from the ABI."
        )

        return {
            "status": "WARNING",
            "risk": "MEDIUM",
            "confidence": "MEDIUM",
            "mintable": True,
            "mint_functions": mint_functions,
            "supply_controls": supply_controls,
            "burn_functions": burn_functions,
            "signals": signals,
            "warnings": warnings,
        }

    # -----------------------------------------------------
    # Other state-changing supply control
    # -----------------------------------------------------

    signals.append(
        "Recognized state-changing supply-management "
        "functions: "
        + ", ".join(
            supply_controls
        )
        + "."
    )

    warnings.append(
        "State-changing supply-management functions "
        "were detected, but their exact effect and "
        "authorization could not be fully determined "
        "from the available ABI."
    )

    return {
        "status": "WARNING",
        "risk": "MEDIUM",
        "confidence": "MEDIUM",
        "mintable": None,
        "mint_functions": [],
        "supply_controls": supply_controls,
        "burn_functions": burn_functions,
        "signals": signals,
        "warnings": warnings,
    }