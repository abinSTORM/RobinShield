from engines.security_engine import security_scan
from engines.risk_engine import calculate_score
from engines.risk_engine import get_risk

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

report = security_scan(address)

score = calculate_score(report)

risk = get_risk(score)

print()
print("🛡 RobinShield Security Report")
print("=" * 40)

print(f"Overall Score : {score}/100")
print(f"Risk Level    : {risk}")

print("=" * 40)

for item in report:

    icon = "✅"

    if item["status"] == "INFO":
        icon = "ℹ️"

    elif item["status"] == "WARNING":
        icon = "⚠️"

    elif item["status"] == "FAIL":
        icon = "❌"

    print()
    print(f"{icon} {item['check']}")
    print(f"Status : {item['status']}")
    print(f"Reason : {item['reason']}")