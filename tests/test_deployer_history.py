import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from analysis.deployer_history import analyze_deployer_history


TOKEN = "0x1111111111111111111111111111111111111111"
DEPLOYER = "0x2222222222222222222222222222222222222222"
OLDER_TOKEN = "0x3333333333333333333333333333333333333333"
FUNDER = "0x4444444444444444444444444444444444444444"


class DeployerHistoryTests(unittest.TestCase):
    def test_reports_prior_creation_and_recent_funding_as_context(self):
        now = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)
        payloads = {
            f"addresses/{TOKEN}": {"creation_tx_hash": "0xcreate"},
            "transactions/0xcreate": {
                "from": {"hash": DEPLOYER, "is_contract": False},
                "block": {"number": 100},
            },
            f"addresses/{DEPLOYER}/transactions": {
                "items": [
                    {"block": {"number": 100}},
                    {
                        "block": {"number": 50},
                        "created_contract": {"hash": OLDER_TOKEN},
                        "hash": "0xolder",
                    },
                ],
                "next_page_params": None,
            },
        }

        def fake_get(path, params=None):
            if path.endswith("/transactions") and params == {"filter": "to"}:
                return {"items": [{
                    "to": {"hash": DEPLOYER},
                    "from": {"hash": FUNDER},
                    "block": {"number": 90},
                    "timestamp": "2026-10-14T02:00:00Z",
                    "value": "1000000000000000000",
                    "hash": "0xfund",
                }]}
            return payloads.get(path)

        with patch("analysis.deployer_history._get_json", side_effect=fake_get):
            result = analyze_deployer_history(TOKEN, now=now)

        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["prior_contract_creations"], 1)
        self.assertEqual(result["prior_contract_samples"][0]["address"], OLDER_TOKEN)
        self.assertEqual(result["recent_funding"]["from"], FUNDER)
        self.assertTrue(any("not proof" in signal for signal in result["signals"]))

    def test_factory_sender_does_not_guess_originating_wallet(self):
        payloads = {
            f"addresses/{TOKEN}": {"creation_tx_hash": "0xcreate"},
            "transactions/0xcreate": {
                "from": {"hash": DEPLOYER, "is_contract": True},
                "block": {"number": 100},
            },
        }
        with patch("analysis.deployer_history._get_json", side_effect=lambda path, params=None: payloads.get(path)):
            result = analyze_deployer_history(TOKEN)

        self.assertEqual(result["deployer_type"], "CONTRACT")
        self.assertIsNone(result["prior_contract_creations"])
        self.assertTrue(any("factory" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
