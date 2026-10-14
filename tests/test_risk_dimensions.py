import unittest

from engines.overall_risk import _risk_dimensions


class RiskDimensionTests(unittest.TestCase):
    def test_thin_market_and_unlock_risk_is_separate_from_successful_swap_tests(self):
        dimensions = _risk_dimensions(
            {
                "Liquidity": 35,
                "Holder concentration": 25,
                "LP safety": 25,
                "Trade simulation": 12,
                "Admin control surface": 2,
            },
            {"status": "PASS"},
            {"status": "PASS"},
            {"status": "REVIEW"},
        )

        market = dimensions["market_and_exit_risk"]
        contract = dimensions["contract_and_sellability"]
        self.assertEqual(market["status"], "HIGH")
        self.assertEqual(market["severity_points"], 97)
        self.assertEqual(contract["status"], "REVIEW")
        self.assertEqual(contract["tested_honeypot_status"], "PASS")
        self.assertEqual(contract["deep_router_swap_status"], "PASS")
        self.assertEqual(contract["risk_components"], {"Admin control surface": 2})

    def test_failed_sellability_check_is_reported_separately(self):
        dimensions = _risk_dimensions(
            {"Liquidity": 5, "Honeypot / sellability": 40},
            {"status": "FAIL"},
            {"status": "PASS"},
            {"status": "REVIEW"},
        )

        self.assertEqual(
            dimensions["contract_and_sellability"]["status"],
            "FAIL",
        )


if __name__ == "__main__":
    unittest.main()
