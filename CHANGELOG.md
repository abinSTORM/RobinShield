# Changelog

RobinShield is under active development. This file records implemented work;
planned items are tracked in [ROADMAP.md](ROADMAP.md).

## Unreleased

### Added

- Normal and deep token scans with JSON report output.
- Local HTTP API for running normal and deep scans.
- Liquidity pool discovery, holder distribution, and token identity reporting.
- LP holder analysis that verifies indexed LP balances against the pair contract
  and identifies directly withdrawable LP when holder coverage accounts for the
  full supply.
- Deployer history checks for creation sender, earlier contract deployments,
  and recent inbound native-asset funding when explorer data is available.
- Separate market/exit risk and contract/sellability summaries in the overall
  risk report.
- Admin-control, proxy, bytecode-pattern, tax, ownership, holder, and deep swap
  analysis.
- Focused tests for LP holder coverage, deployer-history evidence, and risk
  dimension reporting.

### Changed

- Risk scores are described as severity scores, not probabilities that a token
  is a scam.
- Missing or incomplete evidence is reported as unknown or inconclusive rather
  than treated as proof of safety.
- Deep router buy/sell tests run only in temporary local forks; they do not
  broadcast transactions to Robinhood Chain.

### Known limitations

- Explorer indexing may not provide contract-creation history or all deployer
  transactions, so deployer findings can be unavailable or partial.
- ABI and bytecode rules are heuristic and cannot prove who can call a function
  or detect every custom or obfuscated behavior.
- Router simulations reflect the tested state and sizes; they do not guarantee
  future trades, other wallets, or available market depth.
- The full website dashboard and full-scan Telegram bot have not been built.
