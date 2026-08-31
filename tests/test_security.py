from engines.security_engine import security_scan
from engines.risk_engine import calculate_score
from engines.risk_engine import get_risk


ADDRESS = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"


report = security_scan(ADDRESS)

score = calculate_score(report)

risk = get_risk(score)


print()
print("🛡 RobinShield Security Report")
print("=" * 40)

print(f"Overall Score : {score}/100")
print(f"Risk Level    : {risk}")

print("=" * 40)


if isinstance(report, dict):

    items = report.get(
        "security",
        []
    )

else:

    items = report


for item in items:

    if not isinstance(item, dict):
        continue

    status = str(
        item.get(
            "status",
            "UNKNOWN"
        )
    ).upper()

    icon = "ℹ️"

    if status == "PASS":
        icon = "✅"

    elif status == "INFO":
        icon = "ℹ️"

    elif status == "WARNING":
        icon = "⚠️"

    elif status == "FAIL":
        icon = "❌"

    print()
    print(
        f"{icon} {item.get('check', 'Unknown')}"
    )
    print(
        f"Status : {status}"
    )
    print(
        f"Reason : {item.get('reason', '')}"
    )
