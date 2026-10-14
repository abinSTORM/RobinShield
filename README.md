# RobinShield

RobinShield is an actively developed token-risk scanner for Robinhood Chain.
It combines on-chain contract, liquidity, holder, LP-custody, and swap evidence
in a CLI report and JSON API.

It is a research tool, not a guarantee that a token is safe or a determination
that its creator committed fraud. A high score describes the severity of
observed risk; it is not the probability that a token is a scam.

## Current features

- Normal and deep scans from the command line.
- Contract ABI, ownership, tax, trading-control, proxy, and bytecode-pattern
  analysis.
- Liquidity pool and holder distribution analysis.
- LP custody checks that compare indexed LP holders with on-chain balances.
- Deployer history and funding context when explorer data is available.
- Router quote and transfer checks; deep router buy/sell tests run in temporary
  local Anvil forks and do not broadcast transactions.
- JSON reports and a local HTTP API.
- Separate market/exit risk and contract/sellability summaries.

Some explorer data may be unavailable or incomplete. In that case RobinShield
reports the check as unknown or inconclusive. ABI and bytecode rules are
heuristics and cannot prove who can call every function or detect every custom
or obfuscated behavior.

## Current status

The CLI scanner and local JSON API are implemented. `bot.py` is currently a
basic Telegram token-info bot; it is **not yet connected to the full scanner**.
A web dashboard has not been built. See [ROADMAP.md](ROADMAP.md) for remaining
work and [CHANGELOG.md](CHANGELOG.md) for implemented changes.

## Requirements

- Python 3.10 or newer.
- An RPC endpoint for Robinhood Chain. The scanner has a default endpoint, but
  a reliable archive-capable RPC is recommended for historical and deep checks.
- Foundry's `anvil` executable on your `PATH` for deep router fork tests.
- A Telegram bot token only if you want to run the current basic Telegram bot.

## Install

```bash
git clone https://github.com/abinSTORM/RobinShield.git
cd RobinShield
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Optional settings can be placed in a local `.env` file. Never commit or share
that file. Supported settings include:

```text
ROBINHOOD_RPC_URL=<your Robinhood Chain RPC URL>
ROBINHOOD_RPC_WSS_URL=<your Robinhood Chain WebSocket URL>
BLOCKSCOUT_API=https://robinhoodchain.blockscout.com/api/v2
BLOCKSCOUT_API_KEY=<your Blockscout API key, if available>
ALCHEMY_API_KEY=<your Alchemy API key, if used>
TELEGRAM_BOT_TOKEN=<your Telegram bot token, only for bot use>
```

Values above are placeholders. Keep real credentials in your local `.env`; do
not paste them into chat, screenshots, source files, or GitHub.

## Run a scan

Replace `TOKEN_ADDRESS` with a real token contract address:

```bash
python3 scanner.py TOKEN_ADDRESS
python3 scanner.py TOKEN_ADDRESS --deep
python3 scanner.py TOKEN_ADDRESS --json-output reports/scan.json
python3 scanner.py TOKEN_ADDRESS --deep --json-output reports/deep-scan.json
```

Deep scans may take several minutes and require `anvil` to be installed and
available on `PATH`.

Optional comparisons need a name or symbol from a source you trust:

```bash
python3 scanner.py TOKEN_ADDRESS --expect-name 'Official Token Name' --expect-symbol 'TKN'
python3 scanner.py TOKEN_ADDRESS --check-address WALLET_ADDRESS
```

## Local HTTP API

Start the API:

```bash
python3 api_server.py
```

It listens on `127.0.0.1:8787` by default. Check its health:

```bash
curl http://127.0.0.1:8787/health
```

Request a normal scan:

```bash
curl -X POST http://127.0.0.1:8787/scan \
  -H 'Content-Type: application/json' \
  -d '{"token_address":"TOKEN_ADDRESS","deep":false}'
```

Set `"deep":true` to run the deep scan. Deep requests can take several
minutes. The API binds to localhost by default; exposing it publicly requires
separate hosting, HTTPS, authentication or abuse controls, and secret
management.

## Current Telegram bot

After setting `TELEGRAM_BOT_TOKEN` in your local `.env`, run:

```bash
python3 bot.py
```

The current bot only returns basic token information. Full scanner results from
Telegram are planned but are not implemented yet.

## Tests

Run the focused offline tests for the recent reporting and evidence changes:

```bash
python3 -m unittest tests.test_lp_holder_analysis tests.test_deployer_history tests.test_risk_dimensions -v
```

Other test files may call live RPC or explorer services.

## License

MIT License. See [LICENSE](LICENSE).
