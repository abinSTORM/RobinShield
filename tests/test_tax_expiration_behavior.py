import unittest
from unittest.mock import Mock, patch

from engines.tax_analysis import (
    _classify_expiration_getters,
    analyze_tax_expiration_behavior,
)
from engines.liquidity_engine import analyze_v3_pool
from detectors.swap_simulator import (
    UNISWAP_V3_ROUTER,
    approve_router,
    analyze_swap_simulation,
)


class TaxExpirationBehaviorTests(unittest.TestCase):
    def test_normal_mode_skips_forked_expiration_swaps(self):
        result = analyze_tax_expiration_behavior(
            "0x0000000000000000000000000000000000000001",
            [],
            2_000_000_000,
            enabled=False,
        )

        self.assertFalse(result["tested"])
        self.assertEqual(result["status"], "SKIPPED")
        self.assertIn("deep mode", result["reason"])

    def test_normal_mode_does_not_start_v3_expiration_fork(self):
        liquidity = {
            "found": True,
            "dex": "Uniswap V3",
            "version": "V3",
            "pair": "0x0000000000000000000000000000000000000002",
            "quote_token": "0x0000000000000000000000000000000000000003",
            "fee": 3000,
        }
        with patch("engines.tax_analysis.start_anvil") as start_anvil:
            result = analyze_tax_expiration_behavior(
                "0x0000000000000000000000000000000000000001",
                [],
                2_000_000_000,
                liquidity=liquidity,
                enabled=False,
            )

        self.assertFalse(result["tested"])
        self.assertEqual(result["status"], "SKIPPED")
        start_anvil.assert_not_called()

    def test_deep_v3_expiration_requires_supported_fee_tier(self):
        liquidity = {
            "found": True,
            "dex": "Uniswap V3",
            "version": "V3",
            "pair": "0x0000000000000000000000000000000000000002",
            "quote_token": "0x0000000000000000000000000000000000000003",
            "fee": 2500,
        }
        with patch("engines.tax_analysis.start_anvil") as start_anvil:
            result = analyze_tax_expiration_behavior(
                "0x0000000000000000000000000000000000000001",
                [],
                2_000_000_000,
                liquidity=liquidity,
                enabled=True,
            )

        self.assertFalse(result["tested"])
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertIn("fee tier", result["reason"])
        start_anvil.assert_not_called()

    def test_v3_approval_verifies_allowance_for_v3_router(self):
        holder = "0x0000000000000000000000000000000000000001"
        token = Mock()
        token.functions.allowance.return_value.call.return_value = 100
        token.functions.approve.return_value.build_transaction.return_value = {}
        w3 = Mock()
        w3.eth.gas_price = 1
        w3.eth.get_transaction_count.return_value = 0
        w3.eth.send_transaction.return_value = Mock(hex=lambda: "0xabc")

        with patch(
            "detectors.swap_simulator.wait_for_receipt",
            return_value={"status": 1},
        ):
            result = approve_router(
                w3,
                token,
                holder,
                100,
                router_address=UNISWAP_V3_ROUTER,
            )

        self.assertEqual(result["allowance"], 100)
        token.functions.allowance.assert_called_once_with(
            holder,
            UNISWAP_V3_ROUTER,
        )

    def test_deep_v3_router_tests_skip_zero_active_liquidity(self):
        liquidity = {
            "found": True,
            "dex": "Uniswap V3",
            "version": "V3",
            "pair": "0x0000000000000000000000000000000000000002",
            "quote_token": "0x0000000000000000000000000000000000000003",
            "fee": 3000,
            "best_pool_data": {"v3_liquidity": 0},
        }
        with patch("detectors.swap_simulator.get_web3") as get_web3:
            result = analyze_swap_simulation(
                "0x0000000000000000000000000000000000000001",
                liquidity,
                deep=True,
            )

        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertFalse(result["tested"])
        self.assertIn("zero active liquidity", result["warnings"][0])
        get_web3.assert_not_called()

    def test_deep_expiration_swaps_skip_zero_active_v3_pool(self):
        liquidity = {
            "found": True,
            "dex": "Uniswap V3",
            "version": "V3",
            "pair": "0x0000000000000000000000000000000000000002",
            "quote_token": "0x0000000000000000000000000000000000000003",
            "fee": 3000,
            "best_pool_data": {"v3_liquidity": 0},
        }
        with patch("engines.tax_analysis.start_anvil") as start_anvil:
            result = analyze_tax_expiration_behavior(
                "0x0000000000000000000000000000000000000001",
                [],
                2_000_000_000,
                liquidity=liquidity,
                enabled=True,
            )

        self.assertFalse(result["tested"])
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertIn("zero active liquidity", result["reason"])
        start_anvil.assert_not_called()

    def test_zero_v3_liquidity_reason_is_not_overwritten(self):
        pool_contract = Mock()
        pool_contract.functions.token0.return_value.call.return_value = (
            "0x0000000000000000000000000000000000000003"
        )
        pool_contract.functions.token1.return_value.call.return_value = (
            "0x0000000000000000000000000000000000000001"
        )
        pool_contract.functions.liquidity.return_value.call.return_value = 0
        pool_contract.functions.slot0.return_value.call.return_value = (1, 0, 0, 0, 0, 0, True)
        w3 = Mock()
        w3.eth.contract.return_value = pool_contract

        result = analyze_v3_pool(
            "0x0000000000000000000000000000000000000002",
            3000,
            w3,
            token_address="0x0000000000000000000000000000000000000001",
        )

        self.assertEqual(result["v3_liquidity"], 0)
        self.assertEqual(result["active_liquidity_status"], "ZERO_AT_CURRENT_PRICE")
        self.assertIn("zero active liquidity", result["reason"])

    def test_deep_mode_without_pair_is_inconclusive(self):
        result = analyze_tax_expiration_behavior(
            "0x0000000000000000000000000000000000000001",
            [],
            2_000_000_000,
            liquidity={},
            enabled=True,
        )

        self.assertFalse(result["tested"])
        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertIn("liquidity pair", result["reason"])

    def test_missing_getters_are_not_classified_as_no_change(self):
        behavior, status, reason = _classify_expiration_getters(
            (None, None, None),
            (None, None, None),
        )

        self.assertEqual(behavior, "GETTER_DATA_UNAVAILABLE")
        self.assertEqual(status, "INCONCLUSIVE")
        self.assertIn("successful swaps alone", reason)


if __name__ == "__main__":
    unittest.main()
