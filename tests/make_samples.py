"""Generate test inputs: WhatsApp-style screenshots (headless Edge) and a spoken scam-call clip (Bulbul).

Real screenshots / recordings from your own phone are better: drop them into tests/samples/ and run
    python tests/run_samples.py tests/samples/<file>
"""

import base64
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import kavach  # noqa: E402

OUT = Path(__file__).parent / "samples"
OUT.mkdir(exist_ok=True)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

SCREENSHOTS = {
    "whatsapp_ta_kyc.png": ("+91 70xxx xxx21",
        "அன்புள்ள வாடிக்கையாளரே, உங்கள் வங்கி KYC காலாவதியாகிவிட்டது. இன்று இரவுக்குள் புதுப்பிக்கவில்லை என்றால் "
        "உங்கள் கணக்கு முடக்கப்படும். உடனே இந்த செயலியை நிறுவவும்: http://kyc-update-bank.in.net/KYC_Update.apk"),
    "whatsapp_hi_job.png": ("+84 9xx xxx 712",
        "नमस्ते! मैं Priya, Amazon HR से। हमारे पास पार्ट-टाइम जॉब है, घर बैठे YouTube वीडियो लाइक करें और रोज़ "
        "₹3000-₹8000 कमाएँ। पहले टास्क के लिए ₹200 मिलेंगे। जुड़ने के लिए Telegram पर मैसेज करें: t.me/amz_task_hr"),
}

CALL_SCRIPT = ("हेलो, मैं मुंबई साइबर क्राइम ब्रांच से इंस्पेक्टर राठौर बोल रहा हूँ। आपके आधार कार्ड से एक सिम लिया गया है "
               "जिससे मनी लॉन्ड्रिंग हुई है। आप अभी डिजिटल अरेस्ट में हैं। कॉल काटिए मत और किसी को मत बताइए। "
               "जाँच के लिए अपने खाते का पैसा RBI के सुरक्षित खाते में ट्रांसफर करना होगा।")


def screenshot(name: str, sender: str, text: str) -> None:
    html = OUT / (name + ".html")
    html.write_text(f"""<!doctype html><meta charset="utf-8"><body style="margin:0;background:#efe7dd;
        font-family:'Nirmala UI',sans-serif"><div style="background:#075e54;color:#fff;padding:14px 18px;font-size:20px">
        {sender}</div><div style="margin:18px;max-width:520px;background:#fff;padding:12px 14px;border-radius:0 10px 10px 10px;
        font-size:19px;line-height:1.5;box-shadow:0 1px 1px #0002">{text}<div style="text-align:right;color:#999;
        font-size:13px">10:42 am</div></div></body>""", encoding="utf-8")
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--hide-scrollbars", "--window-size=600,420",
                    f"--screenshot={OUT / name}", html.as_uri()], check=True, capture_output=True)
    html.unlink()
    print("wrote", OUT / name)


def call_clip() -> None:
    resp = kavach.client.text_to_speech.convert(text=CALL_SCRIPT, language_code="hi-IN", model="bulbul:v3")
    path = OUT / "call_hi_digital_arrest.wav"
    path.write_bytes(base64.b64decode(resp.audios[0]))
    print("wrote", path)


if __name__ == "__main__":
    for n, (s, t) in SCREENSHOTS.items():
        screenshot(n, s, t)
    call_clip()
