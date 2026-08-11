from core.price import get_eth_price_usd


price = get_eth_price_usd()

print()
print("💵 RobinShield ETH Price")
print("=" * 40)
print(f"ETH/USD: ${price:,.2f}")