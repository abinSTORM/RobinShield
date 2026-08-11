from engines.liquidity_engine import analyze_liquidity


TOKEN = "0xa9a2fbff17ad742383a4ca357c437af661dfee70"


result = analyze_liquidity(TOKEN)

print()
print("💧 RobinShield Liquidity Intelligence")
print("=" * 40)

for key, value in result.items():
    print(f"{key}: {value}")