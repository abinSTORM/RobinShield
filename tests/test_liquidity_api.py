import unittest
import requests


class TestLiquidityAPI(unittest.TestCase):

    ADDRESS = (
        "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"
    )

    URL = (
        "https://robinhoodchain.blockscout.com/api/v2/tokens/"
        + ADDRESS
    )

    def test_liquidity_api_is_reachable(self):

        try:

            response = requests.get(
                self.URL,
                timeout=10,
            )

        except requests.RequestException:

            self.skipTest(
                "Blockscout API is unavailable from this environment."
            )

        # Cloudflare / WAF protection is an external dependency
        # and should not make the test suite fail.
        if response.status_code in (
            403,
            429,
        ):

            self.skipTest(
                f"Blockscout API returned HTTP {response.status_code}."
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        try:

            data = response.json()

        except ValueError:

            self.fail(
                "Blockscout API returned a non-JSON response."
            )

        self.assertIsInstance(
            data,
            dict,
        )


if __name__ == "__main__":
    unittest.main()