# RobinShield Roadmap

RobinShield is an active research tool, not a finished or production-certified
scanner. The roadmap separates working scanner features from the product work
still needed.

## Implemented

- Normal CLI scans and deep scans.
- Contract ABI, ownership, tax, blacklist, pause, trading-control, proxy, and
  bytecode-pattern analysis.
- Liquidity pool discovery and token holder distribution analysis.
- LP custody checks using indexed holders cross-checked against on-chain LP
  balances; incomplete holder coverage remains unknown.
- Router quote checks, transfer-level sellability checks, and deep buy/sell
  execution tests on temporary local forks.
- Deployer creation and funding context when the configured explorer exposes
  the required history.
- JSON reports and a local HTTP scan API.
- Overall risk reporting that distinguishes market/exit risk from
  contract/sellability evidence.
- Focused tests for LP holder coverage, deployer history, and risk dimensions.

## Next: usability and reliability

1. Build a beginner-friendly web dashboard that calls the existing local scan
   API and explains evidence and unknown checks.
2. Upgrade the existing Telegram bot to run the full RobinShield scan and
   return a concise risk summary.
3. Diagnose and improve deployer-history coverage when Blockscout does not
   return a readable creation transaction.
4. Compare known legitimate and malicious examples against other scanners and
   calibrate scoring without presenting risk severity as scam probability.
5. Add end-to-end checks for the API, website, Telegram bot, and normal/deep
   scan workflows.

## Before public hosting

- Add API authentication or suitable abuse controls, request limits, and
  operational logging that does not expose secrets.
- Choose a hosting provider and configure HTTPS, environment secrets, and
  service monitoring.
- Review dependency setup and document installation for a clean machine.

## Later

- Historical scan comparisons and change alerts.
- More pool/router coverage and scanner performance improvements.
- Multi-chain support after Robinhood Chain coverage is validated.
