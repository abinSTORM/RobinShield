from core.abi import get_abi
from core.function_index import build_function_index

from detectors.mint_detector import scan as mint_scan
from detectors.tax_detector import scan as tax_scan
from detectors.ownership_detector import scan as ownership_scan
from detectors.blacklist_detector import scan as blacklist_scan
from detectors.pause_detector import scan as pause_scan


def security_scan(address):

    abi = get_abi(address)

    if abi is None:
        return None

    functions = build_function_index(abi)

    report = []

    report.append(mint_scan(functions))
    report.append(tax_scan(functions))
    report.append(ownership_scan(functions))
    report.append(blacklist_scan(functions))
    report.append(pause_scan(functions))

    return report