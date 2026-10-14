"""Small local HTTP API for RobinShield token scans.

Run with ``python3 api_server.py``. The server binds to localhost by default;
scans can take several minutes in deep mode.
"""

import argparse
from contextlib import redirect_stdout
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import scanner


MAX_REQUEST_BYTES = 16 * 1024
_scan_lock = threading.Lock()


class RobinShieldAPIHandler(BaseHTTPRequestHandler):
    server_version = "RobinShieldAPI/1.0"

    def _send_json(self, status, payload):
        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            default=scanner._json_default,
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/") in ("/health", "/v1/health"):
            self._send_json(200, {"status": "ok", "service": "RobinShield"})
            return
        self._send_json(404, {"error": "Endpoint not found."})

    def do_POST(self):
        if self.path.rstrip("/") not in ("/scan", "/v1/scan"):
            self._send_json(404, {"error": "Endpoint not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length."})
            return

        if content_length <= 0 or content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Request body must be between 1 byte and 16 KiB."})
            return

        try:
            request = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON."})
            return

        if not isinstance(request, dict):
            self._send_json(400, {"error": "Request JSON must be an object."})
            return

        token = request.get("token_address", request.get("token"))
        deep = request.get("deep", False)
        expected_name = request.get("expected_name")
        expected_symbol = request.get("expected_symbol")
        check_address = request.get("check_address")
        if not isinstance(token, str) or not token.strip():
            self._send_json(400, {"error": "Provide token_address as a string."})
            return
        if not isinstance(deep, bool):
            self._send_json(400, {"error": "deep must be true or false."})
            return
        if expected_name is not None and not isinstance(expected_name, str):
            self._send_json(400, {"error": "expected_name must be a string."})
            return
        if expected_symbol is not None and not isinstance(expected_symbol, str):
            self._send_json(400, {"error": "expected_symbol must be a string."})
            return
        if check_address is not None and not isinstance(check_address, str):
            self._send_json(400, {"error": "check_address must be a string."})
            return
        if check_address is not None:
            try:
                check_address = scanner.Web3.to_checksum_address(check_address.strip())
            except (ValueError, TypeError):
                self._send_json(400, {"error": "Invalid check_address."})
                return

        try:
            token = scanner.Web3.to_checksum_address(token.strip())
        except (ValueError, TypeError):
            self._send_json(400, {"error": "Invalid token address."})
            return

        # scanner.DEEP_SCAN is shared process state; do not let overlapping
        # requests mix normal and deep analysis stages.
        with _scan_lock:
            previous_mode = scanner.DEEP_SCAN
            scanner.DEEP_SCAN = deep
            try:
                with redirect_stdout(io.StringIO()):
                    report = scanner.scan_token(
                        token,
                        expected_name=expected_name,
                        expected_symbol=expected_symbol,
                        check_address=check_address,
                    )
            except Exception as exc:
                self._send_json(500, {"error": "Scan failed.", "detail": str(exc)})
                return
            finally:
                scanner.DEEP_SCAN = previous_mode

        self._send_json(200, report)

    def log_message(self, format_string, *args):
        # Keep HTTP access logs useful without logging request bodies.
        super().log_message(format_string, *args)


def main():
    parser = argparse.ArgumentParser(description="Run the RobinShield scan API.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: localhost).")
    parser.add_argument("--port", type=int, default=8787, help="Port (default: 8787).")
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    server = ThreadingHTTPServer((args.host, args.port), RobinShieldAPIHandler)
    print(f"RobinShield API listening at http://{args.host}:{args.port}")
    print("Health: GET /health | Scan: POST /scan")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping RobinShield API.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
