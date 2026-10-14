# 🛡 RobinShield

An AI-powered smart contract security scanner built for Robinhood Chain.

RobinShield helps traders and developers analyze smart contracts by checking ownership, mint capabilities, blacklist functions, holder distribution, and overall contract risk.

---

## ✨ Features

### Security Analysis
- ✅ Mint Function Detection
- ✅ Ownership Analysis
- ✅ Blacklist Detection
- ✅ Pause Function Detection
- ✅ Tax Function Detection

### Holder Analysis
- ✅ Largest Wallet Analysis
- ✅ Top 5 Holder Percentage
- ✅ Top 10 Holder Percentage
- ✅ Holder Risk Assessment

### Contract Analysis
- ✅ ABI Analysis
- ✅ Contract Metadata
- ✅ Proxy Detection
- ✅ Verification Status

### Performance
- ✅ ABI Cache System
- ✅ Modular Architecture
- ✅ Risk Engine

### Reports
- ✅ JSON scan report export with full analysis and holder records

### REST API
- ✅ Local HTTP API for normal and deep token scans
- ✅ Admin-control and proxy-upgrade review
- ✅ On-chain token name/symbol reporting with optional trusted comparison

---

## 🚀 Project Structure

```
RobinShield/

analysis/
core/
detectors/
engines/
tests/

README.md
ROADMAP.md
CHANGELOG.md
LICENSE
requirements.txt
```

---

## 🏗 Current Status

Current Version:

**v0.1.0**

Completed

- Security Engine
- Risk Engine
- Holder Analysis
- Developer Analysis
- Package Architecture

In Progress

- Liquidity Intelligence

Planned

- Telegram Bot
- Web Dashboard
- Trust Score V2
- Multi-chain Support

---

## 📦 Installation

Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/RobinShield.git
```

Go inside the project

```bash
cd RobinShield
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run

Example

```bash
python3 -m tests.test_security
```

Save a full scan report as JSON:

```bash
python3 scanner.py <TOKEN_ADDRESS> --json-output reports/scan.json
python3 scanner.py <TOKEN_ADDRESS> --deep --json-output reports/deep-scan.json
python3 scanner.py <TOKEN_ADDRESS> --expect-name 'Official Token Name' --expect-symbol 'TKN'
python3 scanner.py <TOKEN_ADDRESS> --check-address <WALLET_ADDRESS>
```

Start the local scan API in another terminal:

```bash
python3 api_server.py
```

Check that it is running:

```bash
curl http://127.0.0.1:8787/health
```

Request a normal or deep scan (deep scans may take several minutes):

```bash
curl -X POST http://127.0.0.1:8787/scan \
  -H 'Content-Type: application/json' \
  -d '{"token_address":"<TOKEN_ADDRESS>","deep":false}'

curl -X POST http://127.0.0.1:8787/scan \
  -H 'Content-Type: application/json' \
  -d '{"token_address":"<TOKEN_ADDRESS>","deep":true,"expected_name":"Official Token Name","expected_symbol":"TKN","check_address":"<WALLET_ADDRESS>"}'
```

The response body is the same versioned JSON report produced by the scanner CLI. An expected name or symbol must come from a trusted source you choose; without one, RobinShield reports the on-chain values but cannot determine whether they impersonate another token. The API binds to `127.0.0.1` by default; use `--host` only when you intentionally want to expose it on another interface.

Admin-control findings list recognized tax/fee, blacklist/allowlist, trading, limit, exemption, role, and upgrade functions. They are capability warnings; function names alone do not prove who can call them or exactly what the code does. Successful deep swaps show the tested swaps worked at scan time and cannot guarantee future sellability.

---

## 🗺 Roadmap

See:

```
ROADMAP.md
```

---

## 📜 License

MIT License

---

## ⚠ Disclaimer

RobinShield is an educational and research project.

Always perform your own research before making financial decisions.
# Bytecode pattern review

RobinShield includes an explainable local rule set for bytecode-derived
indicators such as mutable tax selectors, sell restrictions, limits, mint
selectors, unrecognized delegatecall, selfdestruct, transaction-origin reads,
and proxy implementations. Each match includes an identifier, severity,
confidence, description, and evidence in the JSON report.

These are heuristic signals, not a proprietary third-party signature database
or a definitive scam verdict. Selector bytes can be misleading or appear as
data, and custom or obfuscated behavior can evade these rules. Source review,
on-chain state checks, and swap simulation should be considered together.

The overall report now separates the numeric risk score from evidence
coverage. `INCONCLUSIVE` means important checks were unavailable or incomplete;
it is not a safety verdict and should not be read as low risk.
