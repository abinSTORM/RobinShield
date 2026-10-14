import unittest
from unittest.mock import patch

from core.lp_safety import calculate_lp_safety


PAIR = "0x1111111111111111111111111111111111111111"
OWNER = "0x2222222222222222222222222222222222222222"
ZERO = "0x0000000000000000000000000000000000000000"
DEAD = "0x000000000000000000000000000000000000dead"


class FakeCall:
    def __init__(self, value):
        self.value = value

    def call(self):
        return self.value


class FakeFunctions:
    def __init__(self, balances):
        self.balances = balances

    def balanceOf(self, address):
        return FakeCall(self.balances.get(address.lower(), 0))


class FakeContract:
    def __init__(self, balances):
        self.functions = FakeFunctions(balances)


class FakeEth:
    def __init__(self, balances):
        self.balances = balances

    def contract(self, address, abi):
        return FakeContract(self.balances)

    def get_code(self, address):
        return b""


class FakeWeb3:
    def __init__(self, balances):
        self.eth = FakeEth(balances)


class LpHolderAnalysisTests(unittest.TestCase):
    def test_complete_eoa_lp_custody_is_reported_as_withdrawable(self):
        balances = {
            ZERO: 1,
            DEAD: 0,
            OWNER.lower(): 999,
        }
        holder_data = {
            "_source": "test_index",
            "items": [{
                "address": {"hash": OWNER},
                "value": "999",
            }],
        }

        with patch("core.lp_safety._get_web3", return_value=FakeWeb3(balances)), patch(
            "analysis.holders.get_holders", return_value=holder_data
        ):
            result = calculate_lp_safety(PAIR, 1000)

        self.assertEqual(result["safety"], "UNLOCKED")
        self.assertTrue(result["lock_status_verified"])
        self.assertEqual(result["holder_distribution"]["status"], "COMPLETE")
        self.assertAlmostEqual(
            result["holder_distribution"]["eoa_percentage_of_supply"],
            99.9,
        )

    def test_incomplete_holder_coverage_stays_unknown(self):
        balances = {
            ZERO: 1,
            DEAD: 0,
            OWNER.lower(): 500,
        }
        holder_data = {
            "_source": "test_index",
            "items": [{
                "address": {"hash": OWNER},
                "value": "500",
            }],
        }

        with patch("core.lp_safety._get_web3", return_value=FakeWeb3(balances)), patch(
            "analysis.holders.get_holders", return_value=holder_data
        ):
            result = calculate_lp_safety(PAIR, 1000)

        self.assertEqual(result["safety"], "UNKNOWN")
        self.assertFalse(result["lock_status_verified"])
        self.assertEqual(result["holder_distribution"]["status"], "PARTIAL")


if __name__ == "__main__":
    unittest.main()
