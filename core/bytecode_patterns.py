"""Explainable bytecode risk-pattern rules used by RobinShield.

These local heuristics are not a copied third-party signature database and
must not be interpreted as proof that a token is malicious or safe.
"""


PATTERN_DATABASE_VERSION = "2026.10.1"


def _functions(groups, group_names):
    found = []
    for group_name in group_names:
        for item in (groups or {}).get(group_name, []):
            if isinstance(item, dict):
                name = item.get("function")
                if name:
                    found.append(str(name))
    return found


def match_bytecode_patterns(groups=None, behavior=None, proxy=None):
    """Return explainable indicators from selector and opcode evidence."""
    groups = groups if isinstance(groups, dict) else {}
    behavior = behavior if isinstance(behavior, dict) else {}
    proxy = proxy if isinstance(proxy, dict) else {}

    matched = []

    def add(pattern_id, title, severity, confidence, description, evidence):
        matched.append({
            "id": pattern_id,
            "title": title,
            "severity": severity,
            "confidence": confidence,
            "description": description,
            "evidence": evidence,
        })

    tax_functions = _functions(groups, ["tax"])
    tax_setters = [
        name for name in tax_functions
        if any(word in name.lower() for word in ("set", "update", "change"))
    ]
    if tax_setters:
        add(
            "RS-TAX-001", "Potentially mutable buy/sell fees", "HIGH", "MEDIUM",
            "Tax-setting selectors appear in the bytecode. Their presence does not prove they are callable by an owner or that they change transfer behavior.",
            tax_setters,
        )

    # State getters and one-way launch functions can appear in selector
    # scans, but do not establish a capability to stop later sells.
    non_restrictive_trading_names = {
        "tradingenabled", "tradingopen", "istradingenabled",
        "istradingopen", "tradingactive", "tradingstatus",
        "tradingstate", "starttrading", "opentrading", "launch",
    }
    restriction_functions = [
        name for name in _functions(groups, ["blacklist", "pause", "trading"])
        if name.split("(", 1)[0].lower() not in non_restrictive_trading_names
    ]
    if restriction_functions:
        add(
            "RS-SELL-001", "Potential sell or transfer restrictions", "MEDIUM", "MEDIUM",
            "Selectors associated with pausing, blacklisting, or trading controls were found. Contract logic and authorization need review to determine their effect.",
            restriction_functions,
        )

    limit_functions = _functions(groups, ["limits"])
    if limit_functions:
        add(
            "RS-LIMIT-001", "Transfer or wallet limits", "LOW", "MEDIUM",
            "Selectors associated with transaction limits or cooldowns were found; they can affect trading availability or size.",
            limit_functions,
        )

    mint_functions = [
        item.get("function")
        for entries in groups.values()
        for item in entries if isinstance(item, dict)
        and "mint" in str(item.get("function", "")).lower()
    ]
    if mint_functions:
        add(
            "RS-MINT-001", "Potential supply expansion", "MEDIUM", "LOW",
            "Mint-related selectors were found. This does not prove minting is enabled or identify who can call it.",
            mint_functions,
        )

    if behavior.get("delegatecall") and not proxy.get("detected"):
        add(
            "RS-BC-001", "Delegatecall outside a recognized proxy", "HIGH", "MEDIUM",
            "DELEGATECALL can execute code using this contract's storage. The proxy detector did not recognize a standard proxy pattern.",
            ["DELEGATECALL opcode"],
        )

    if behavior.get("selfdestruct"):
        add(
            "RS-BC-002", "Selfdestruct opcode present", "MEDIUM", "MEDIUM",
            "SELFDESTRUCT appears in executable bytecode. Its practical effect depends on chain rules and whether the instruction is reachable.",
            ["SELFDESTRUCT opcode"],
        )

    if behavior.get("tx_origin"):
        add(
            "RS-AUTH-001", "Transaction-origin authorization signal", "LOW", "LOW",
            "TX.origin is read by the bytecode. This opcode alone does not establish an authorization flaw.",
            ["TX.origin opcode"],
        )

    if proxy.get("detected") and proxy.get("implementation"):
        add(
            "RS-PROXY-001", "Execution depends on a proxy implementation", "MEDIUM", "HIGH",
            "Calls are routed to an implementation contract. Review implementation identity and who can change the routing before relying on the token.",
            [
                str(proxy.get("type") or "recognized proxy"),
                "implementation: " + str(proxy["implementation"]),
            ],
        )

    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    matched.sort(key=lambda item: severity_order.get(item["severity"], 4))
    return {
        "database_version": PATTERN_DATABASE_VERSION,
        "matches": matched,
        "match_count": len(matched),
        "disclaimer": "Pattern matches are indicators for review, not a definitive scam verdict. Selector names may be absent, misleading, or present as data rather than active dispatch logic.",
    }
