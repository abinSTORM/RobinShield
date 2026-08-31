from engines.risk_engine import calculate_score, get_risk


report = [
    {
        "check": "Mint Function",
        "status": "PASS",
    },
    {
        "check": "Ownership",
        "status": "PASS",
    },
    {
        "check": "Blacklist",
        "status": "PASS",
    },
    {
        "check": "Tax Functions",
        "status": "PASS",
    },
]


score = calculate_score(report)
risk = get_risk(score)


print()
print("🛡️ RobinShield Security Risk Engine")
print("=" * 40)
print(f"Security score: {score}")
print(f"Risk: {risk}")