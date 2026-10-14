"""Summarize contract capabilities that can affect taxes and sellability.

This is a capability audit. A function name in an ABI does not prove who is
authorized to call it or what the function does; the report keeps those facts
separate from the detected surface.
"""


CONTROL_GROUPS = {
    "tax_and_fee_changes": {
        "settax", "settaxes", "settaxrate", "settaxesrate", "setbuytax",
        "setselltax", "setbuytaxrate", "setselltaxrate", "updatetax",
        "updatetaxes", "updatebuytax", "updateselltax", "setfee", "setfees",
        "setfeerate", "setbuyfee", "setsellfee", "setbuyfeerate",
        "setsellfeerate", "updatefee", "updatefees", "setbuytotalfees",
        "setselltotalfees", "settotalfees",
        "settaxpercent", "settaxrates", "updatetaxrates", "updatebuytax",
        "updateselltax", "setfeepercent", "setbuyfeerate", "setsellfeerate",
    },
    "fee_recipient_changes": {
        "settaxwallet", "setfeewallet", "setfeereceiver", "settaxrecipient",
    },
    "blacklist_and_allowlist": {
        "blacklist", "addblacklist", "addtoblacklist", "blacklistaddress",
        "setblacklist", "setblackliststatus", "setblacklisted", "unblacklist",
        "removeblacklist", "removefromblacklist", "whitelist",
        "addwhitelist", "addtowhitelist", "setwhitelist", "setwhitelisted",
        "removewhitelist", "removefromwhitelist", "setbotstatus",
    },
    "trading_and_pause": {
        "settrading", "settradingenabled", "settradingopen", "settradingactive",
        "enabletrading", "disabletrading", "opentrading", "closetrading",
        "stoptrading", "pause", "unpause", "freeze",
        "unfreeze", "setpaused",
    },
    "launch_controls": {
        "starttrading", "launch",
    },
    "limits_and_cooldowns": {
        "setmaxtxamount", "setmaxtxnamount", "setmaxtransactionamount",
        "setmaxtransaction", "setmaxbuyamount", "setmaxsellamount",
        "setmaxtransferamount", "setmaxwallet", "setmaxwalletamount",
        "setmaxwalletsize", "setmaxholdingamount", "setlimits",
        "setlimitsineffect", "removelimits", "setcooldown", "setcooldownenabled",
        "setcooldowntime", "settransferdelay", "settransferdelayenabled",
        "updatetradecoldowntime",
    },
    "router_and_pair_changes": {
        "setrouter", "updaterouter", "setpair", "setautomatedmarketmakerpair",
        "setamm pair", "setuniswaprouter",
    },
    "fee_or_limit_exemptions": {
        "excludefromfees", "includefees", "excludefromfee", "includefee",
        "setfeeexempt", "setlimitexempt", "excludefromlimits",
        "includefromlimits", "setisexcludedfromfees",
    },
    "ownership_and_authority_changes": {
        "transferownership", "safetransferownership", "renounceownership",
        "setowner", "changeowner", "transferadmin", "setadmin", "setauthority",
    },
}

ROLE_SURFACE = {
    "hasrole", "grantrole", "revokerole", "renouncerole", "getroleadmin",
    "getrolemember", "getrolemembercount", "defaultadminrole", "admin",
    "getadmin", "setadmin", "transferadmin", "setauthority",
}

UPGRADE_FUNCTIONS = {
    "upgradeto", "upgradetoandcall", "upgrade", "upgradeandcall",
    "changeadmin", "upgradebeacontoandcall", "diamondcut",
    "setimplementation", "setbeacon",
}


def _function_names(abi):
    if not isinstance(abi, list):
        return set()
    return {
        str(item["name"])
        for item in abi
        if isinstance(item, dict)
        and item.get("type") == "function"
        and item.get("name")
    }


def _bytecode_function_names(bytecode_report):
    groups = bytecode_report.get("groups", {}) if isinstance(bytecode_report, dict) else {}
    names = set()
    selectors = bytecode_report.get("detected_selectors", []) if isinstance(bytecode_report, dict) else []
    if isinstance(selectors, list):
        for entry in selectors:
            if isinstance(entry, dict):
                value = entry.get("function", entry.get("selector"))
                if value:
                    names.add(str(value).split("(", 1)[0])
    if not isinstance(groups, dict):
        return names
    for entries in groups.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict):
                value = entry.get("function", entry.get("selector"))
                if value:
                    names.add(str(value).split("(", 1)[0])
    return names


def _read_admin_state(address, abi, check_address=None, bytecode_report=None):
    result = {"owner_getters": {}, "admin_getters": {}, "role_admins": [], "address_checks": {}, "errors": []}
    read_abi = list(abi) if isinstance(abi, list) else []
    selector_entries = bytecode_report.get("detected_selectors", []) if isinstance(bytecode_report, dict) else []
    selector_names = {
        str(item.get("function", "")).split("(", 1)[0]
        for item in selector_entries
        if isinstance(item, dict) and item.get("function")
    } if isinstance(selector_entries, list) else set()
    minimal_getters = {
        "owner": ([], "address"), "admin": ([], "address"),
        "getAdmin": ([], "address"),
        "isBlacklisted": (["address"], "bool"),
        "isBlackListed": (["address"], "bool"),
        "blacklisted": (["address"], "bool"),
        "isWhitelisted": (["address"], "bool"),
        "isWhiteListed": (["address"], "bool"),
        "whitelisted": (["address"], "bool"),
        "isExcludedFromFees": (["address"], "bool"),
        "isExcludedFromLimits": (["address"], "bool"),
        "isFeeExempt": (["address"], "bool"),
    }
    existing_names = _function_names(read_abi)
    for name, (input_types, output_type) in minimal_getters.items():
        if name in selector_names and name not in existing_names:
            read_abi.append({
                "type": "function", "name": name,
                "inputs": [{"name": f"arg{index}", "type": kind} for index, kind in enumerate(input_types)],
                "outputs": [{"name": "", "type": output_type}],
                "stateMutability": "view",
            })
    names = _function_names(read_abi)
    if not names:
        return result
    try:
        from web3 import Web3
        from config import RPC_URL

        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            raise ConnectionError("RPC unavailable")
        token = w3.eth.contract(address=Web3.to_checksum_address(address), abi=read_abi)

        for getter in ("owner", "getOwner"):
            if getter in names:
                try:
                    value = getattr(token.functions, getter)().call()
                    result["owner_getters"][getter] = Web3.to_checksum_address(value)
                except Exception as exc:
                    result["errors"].append(f"{getter}(): {exc}")

        for getter in ("admin", "getAdmin"):
            if getter in names:
                try:
                    value = getattr(token.functions, getter)().call()
                    result["admin_getters"][getter] = Web3.to_checksum_address(value)
                except Exception as exc:
                    result["errors"].append(f"{getter}(): {exc}")

        roles = [b"\x00" * 32]
        if "DEFAULT_ADMIN_ROLE" in names:
            try:
                role = token.functions.DEFAULT_ADMIN_ROLE().call()
                if isinstance(role, str):
                    role = bytes.fromhex(role[2:] if role.startswith("0x") else role)
                if role not in roles:
                    roles.append(role)
            except Exception as exc:
                result["errors"].append(f"DEFAULT_ADMIN_ROLE(): {exc}")

        if "getRoleMemberCount" in names and "getRoleMember" in names:
            for role in roles:
                try:
                    count = min(int(token.functions.getRoleMemberCount(role).call()), 50)
                    for index in range(count):
                        member = token.functions.getRoleMember(role, index).call()
                        result["role_admins"].append(Web3.to_checksum_address(member))
                except Exception as exc:
                    result["errors"].append(f"Role enumeration failed: {exc}")
                    continue
        result["role_admins"] = sorted(set(result["role_admins"]))

        if check_address:
            checked = Web3.to_checksum_address(check_address)
            getters = (
                "isBlacklisted", "isBlackListed", "blacklisted",
                "isWhitelisted", "isWhiteListed", "whitelisted",
                "isExcludedFromFees", "isExcludedFromLimits", "isFeeExempt",
            )
            for getter in getters:
                if getter not in names:
                    continue
                try:
                    value = getattr(token.functions, getter)(checked).call()
                    result["address_checks"][getter] = bool(value)
                except Exception as exc:
                    result["errors"].append(f"{getter}(address): {exc}")
    except Exception as exc:
        result["errors"].append(f"Admin-state reads unavailable: {exc}")
    return result


def analyze_admin_controls(address, abi=None, ownership=None, proxy=None, bytecode_report=None, check_address=None):
    """Report mutable-risk capabilities without claiming authorization proof."""
    names = _function_names(abi) | _bytecode_function_names(bytecode_report)
    normalized = {name.replace("_", "").replace(" ", "").lower(): name for name in names}

    controls = {}
    for group, candidates in CONTROL_GROUPS.items():
        controls[group] = sorted(
            normalized[candidate]
            for candidate in candidates
            if candidate.replace("_", "").replace(" ", "").lower() in normalized
        )

    role_functions = sorted(
        original for normalized_name, original in normalized.items()
        if normalized_name in {name.replace("_", "").replace(" ", "").lower() for name in ROLE_SURFACE}
    )
    abi_upgrade_functions = sorted(
        original for normalized_name, original in normalized.items()
        if normalized_name in UPGRADE_FUNCTIONS
    )
    metadata_mutators = sorted(
        original for normalized_name, original in normalized.items()
        if normalized_name in {
            "setname", "settokenname", "updatename", "changename",
            "setsymbol", "settokensymbol", "updatesymbol", "changesymbol",
            "setmetadata", "updatemetadata",
        }
    )

    owner_data = ownership if isinstance(ownership, dict) else {}
    proxy_data = proxy if isinstance(proxy, dict) else {}
    proxy_admin = proxy_data.get("admin")
    upgradeable = proxy_data.get("upgradeable") is True
    upgrade_functions = proxy_data.get("upgrade_functions") or []
    live_admin_state = _read_admin_state(address, abi, check_address, bytecode_report)
    owner = owner_data.get("owner") or next(iter(live_admin_state["owner_getters"].values()), None)
    owner_known = bool(owner_data.get("owner_readable")) or bool(live_admin_state["owner_getters"])
    owner_active = owner_known and bool(owner) and str(owner).lower() != "0x0000000000000000000000000000000000000000"
    address_blocked = any(
        bool(value) and "blacklist" in getter.lower()
        for getter, value in live_admin_state["address_checks"].items()
    )

    detected = {key: value for key, value in controls.items() if value}
    has_mutable_controls = bool(detected or role_functions or upgradeable or abi_upgrade_functions or upgrade_functions or metadata_mutators)
    warnings = []
    if has_mutable_controls:
        warnings.append(
            "Potentially security-relevant control surfaces were detected. ABI/selector names do not prove their implementation or caller permissions."
        )
        warnings.append(
            "A successful swap only verifies the tested address and state at scan time; an authorized account may be able to change behavior later."
        )
    if owner_active and has_mutable_controls:
        warnings.append(f"A readable non-zero owner exists ({owner}); its exact authority over each function was not proven.")
    if upgradeable and not proxy_admin:
        warnings.append("Upgradeable proxy storage was detected, but the controlling admin could not be read.")
    if role_functions:
        warnings.append("Role-management or administrator functions were detected. Enumerable role members are shown when available, but role-to-function permissions were not proven.")
    for getter, value in live_admin_state["address_checks"].items():
        if value and ("blacklist" in getter.lower()):
            warnings.append(f"The supplied address is marked blacklisted by {getter}().")
        elif value and ("whitelist" in getter.lower()):
            warnings.append(f"The supplied address is explicitly whitelisted by {getter}(); check whether ordinary buyers have the same trading access.")
        elif value and ("exempt" in getter.lower()):
            warnings.append(f"The supplied address has a special fee/limit exemption according to {getter}().")
    if not has_mutable_controls:
        warnings.append("No recognized mutable-control functions were found. Custom, obfuscated, or selector-only controls may still exist.")
    if address_blocked:
        warnings.append("The supplied address currently returns true from a recognized blacklist getter.")

    return {
        "status": "ADDRESS_BLACKLISTED" if address_blocked else ("REVIEW" if has_mutable_controls else "NO_RECOGNIZED_CONTROLS"),
        "risk": "HIGH" if address_blocked else ("ELEVATED" if has_mutable_controls else "UNKNOWN"),
        "confidence": "MEDIUM" if abi else "LOW",
        "address": address,
        "controls": controls,
        "role_functions": role_functions,
        "role_admins": live_admin_state["role_admins"],
        "admin_getters": live_admin_state["admin_getters"],
        "owner_getters": live_admin_state["owner_getters"],
        "address_check": {
            "address": check_address,
            "results": live_admin_state["address_checks"],
            "blocked": address_blocked,
        } if check_address else None,
        "read_errors": live_admin_state["errors"],
        "owner": owner,
        "owner_readable": owner_known,
        "owner_active": owner_active if owner_known else None,
        "proxy_upgradeable": upgradeable,
        "proxy_admin": proxy_admin,
        "proxy_beacon": proxy_data.get("beacon"),
        "proxy_implementation": proxy_data.get("implementation"),
        "upgrade_functions": sorted(set(abi_upgrade_functions) | set(upgrade_functions) | set(proxy_data.get("upgrade_functions") or [])),
        "metadata_mutators": metadata_mutators,
        "authorization": "NOT_PROVEN_FROM_ABI_OR_SELECTORS",
        "warnings": warnings,
    }
