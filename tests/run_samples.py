"""Run the full Scam Kavach pipeline on sample messages and print a compact report.

Usage: python tests/run_samples.py [path-to-image-or-audio ...]
With no args, runs the built-in text samples (patterns from widely reported Indian scams + one genuine alert).
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import kavach  # noqa: E402

TEXT_SAMPLES = [
    ("hi-IN", "scam", "प्रिय उपभोक्ता, आपकी बिजली आज रात 9:30 बजे काट दी जाएगी क्योंकि आपका पिछले महीने का बिल अपडेट नहीं है। "
              "कृपया तुरंत हमारे बिजली अधिकारी 8597xxxxxx से संपर्क करें। धन्यवाद"),
    ("ta-IN", "scam", "Dear customer, your SBI YONO reward points Rs.7250 will expire today. Redeem now by installing "
              "SBI Rewards app: http://sbi-rewards-points.xyz/SBI_REWARDS.apk"),
    ("en-IN", "scam", "Sir main CBI officer bol raha hoon, aapke Aadhaar se ek parcel Mumbai customs pe pakda gaya hai jisme "
              "drugs hai. Aap abhi digital arrest mein hain, Skype video call pe aaiye aur kisi ko mat bataiye, "
              "verification ke liye RBI account mein paise transfer karne honge."),
    ("bn-IN", "scam", "আপনার পার্সেল ডেলিভারি করা যায়নি কারণ ঠিকানা অসম্পূর্ণ। ২৪ ঘণ্টার মধ্যে ঠিকানা আপডেট করুন: "
              "https://indiapost-track.top/in নইলে পার্সেল ফেরত যাবে।"),
    ("hi-IN", "likely_safe", "Rs.500.00 debited from A/c XX1234 on 01-11-26 to VPA zomato@icici. UPI Ref 4123xxxx. "
              "Not you? Call 1800-111-109 -SBI"),
]


def report(r: dict, secs: float) -> None:
    print(f"  verdict={r['verdict']} ({r['confidence']}) type={r['english'].get('scam_type')} "
          f"src={r['source_language']} -> {r['target_language']}  [{secs:.1f}s]")
    print(f"  one_line: {r['local']['one_line']}")
    for f in r["local"]["red_flags"][:3]:
        print(f"  flag: «{f['quote']}» — {f['why']}")
    print(f"  do_now[0]: {(r['local']['do_now'] or [''])[0]}")
    print(f"  audio bytes(b64): {len(r['audio_mp3_b64'])}  steps: {' > '.join(r['steps'])}")


def main() -> None:
    if len(sys.argv) > 1:
        for p in map(Path, sys.argv[1:]):
            data = p.read_bytes()
            kind = "audio" if p.suffix.lower() in (".wav", ".mp3", ".ogg", ".opus", ".m4a", ".webm", ".aac") else "image"
            print(f"\n== {p.name} ({kind})")
            t = time.time()
            r = kavach.run("hi-IN", **{kind: (data, p.name)})
            print(f"  extracted: {r['message'][:200]!r}")
            report(r, time.time() - t)
        return
    ok = 0
    for target, expected, msg in TEXT_SAMPLES:
        print(f"\n== expected={expected}: {msg[:70]}...")
        t = time.time()
        r = kavach.run(target, text=msg)
        report(r, time.time() - t)
        ok += (r["verdict"] == expected) or (expected == "scam" and r["verdict"] == "suspicious")
    print(f"\n{ok}/{len(TEXT_SAMPLES)} verdicts as expected")


if __name__ == "__main__":
    main()
