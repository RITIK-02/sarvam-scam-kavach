"""End-to-end test against a running server (local or deployed).

Usage: python tests/api_check.py [base_url]     default http://127.0.0.1:8000
"""

import json
import sys
import time
import urllib.request
import uuid
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
SAMPLES = Path(__file__).parent / "samples"

CASES = [
    ("image", "whatsapp_ta_kyc.png", "ta-IN", "scam"),
    ("image", "whatsapp_hi_job.png", "en-IN", "scam"),
    ("audio", "call_hi_digital_arrest.wav", "mr-IN", "scam"),
    ("text", "Rs.500.00 debited from A/c XX1234 on 01-11-26 to VPA zomato@icici. UPI Ref 4123xxxx. "
             "Not you? Call 1800-111-109 -SBI", "hi-IN", "likely_safe"),
]


def post(fields: dict, files: dict) -> dict:
    b = uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, p in files.items():
        body += (f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{p.name}"\r\n'
                 "Content-Type: application/octet-stream\r\n\r\n").encode() + p.read_bytes() + b"\r\n"
    body += f"--{b}--\r\n".encode()
    req = urllib.request.Request(f"{BASE}/api/check", body, {"Content-Type": f"multipart/form-data; boundary={b}",
                                                             "User-Agent": "scam-kavach-test"})
    return json.load(urllib.request.urlopen(req, timeout=180))


def main() -> None:
    passed = 0
    for kind, value, lang, expected in CASES:
        fields, files = {"language": lang}, {}
        if kind == "text":
            fields["text"] = value
        else:
            files[kind] = SAMPLES / value
        t = time.time()
        d = post(fields, files)
        ok = d["verdict"] == expected
        passed += ok
        print(f"\n{'PASS' if ok else 'FAIL'} {kind} -> {lang} [{time.time() - t:.1f}s] "
              f"verdict={d['verdict']} ({d['confidence']}) {d['english']['scam_type']}")
        print("  steps:", " > ".join(d["steps"]))
        print("  says:", d["headings"][d["verdict"]], "|", d["local"]["one_line"])
    print(f"\n{passed}/{len(CASES)} passed")
    sys.exit(0 if passed == len(CASES) else 1)


if __name__ == "__main__":
    main()
