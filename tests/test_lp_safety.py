from core.lp_safety import calculate_lp_safety


PAIR = "0xB3f32340Dd9F23402D0FAC6244150e96117853c5"

LP_TOTAL_SUPPLY = 31622776601683793319988

result = calculate_lp_safety(
    PAIR,
    LP_TOTAL_SUPPLY,
)

print()
print("🔒 RobinShield LP Safety Intelligence")
print("=" * 40)

print(f"Pair: {PAIR}")
print(f"LP total supply: {result['lp_total_supply']}")
print(f"Burned LP: {result['burned_lp']}")
print(f"Burn percentage: {result['burn_percentage']}%")
print(f"Active LP: {result['active_lp']}")
print(f"Safety: {result['safety']}")
print(f"Reason: {result['reason']}")