import unittest

from analysis.verifier import (
    get_contract_info,
)


class TestSource(unittest.TestCase):

    ADDRESS = (
        "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"
    )

    def test_contract_info(self):

        info = get_contract_info(
            self.ADDRESS
        )

        # External verification/source services may be
        # temporarily unavailable. That is not a failure
        # of the test framework itself.
        if info is None:

            self.skipTest(
                "Contract verification/source information "
                "is unavailable."
            )

        self.assertIsInstance(
            info,
            dict,
        )


if __name__ == "__main__":
    unittest.main()