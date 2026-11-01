# 🛡️ Scam Kavach

**Got a strange SMS, WhatsApp message or phone call? Scam Kavach tells you, in your own language and out loud, whether it's a scam and exactly what to do.**

Built on [Sarvam AI](https://docs.sarvam.ai) for Indian languages.

## MVP

| | |
|---|---|
| **User** | A non-technical person, often a parent or grandparent, who reads and listens best in their own Indian language |
| **Problem** | Scam messages (fake KYC, electricity disconnection, `.apk` "reward" apps, digital arrest, task/job scams) arrive in English, Hindi or code-mixed text. The people they target can't tell if they're real, and warnings are rarely in their language. |
| **Input** | A screenshot/photo/PDF of the message, the pasted text, **or** a short call recording / voice note, plus the language to explain in |
| **Result** | A red / amber / green verdict, the scam type, the exact phrases that give it away, what to do now, what to do if you already clicked or paid (1930, cybercrime.gov.in), all translated and **read aloud** |

## How each step maps to a Sarvam API

```
screenshot ──► Sarvam Vision (Document Intelligence) ──┐
recording  ──► Saaras v3 speech-to-text ───────────────┤
text ──────────────────────────────────────────────────┤
                                                       ▼
                         Text language identification  ┐  (in parallel)
                         Sarvam-105B (chat, JSON mode) ┘  verdict, red flags, actions
                                                       ▼
                         Sarvam Translate (parallel per sentence) → user's language
                                                       ▼
                         Bulbul v3 text-to-speech (MP3) → spoken warning
```

| Task | API | Model |
|---|---|---|
| Read text from a screenshot / photo / PDF | Document Intelligence | Sarvam Vision |
| Transcribe a call recording (any Indian language, code-mixed) | Speech-to-Text | `saaras:v3` |
| Detect the message's language | Text → identify language | Mayura LID |
| Decide scam vs safe, quote red flags, extract links/APKs/numbers | Chat completions | `sarvam-105b-conversations` |
| Explain in the user's language | Text → translate | `sarvam-translate:v1` |
| Read the warning aloud | Text-to-Speech | `bulbul:v3` |

Output languages: Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, English.

## Run locally

```bash
pip install -r requirements.txt
echo "SARVAM_API_KEY=your_key" > .env
uvicorn app.main:app --port 8000
# open http://127.0.0.1:8000
```

## Test

```bash
python tests/run_samples.py                 # pipeline on 5 text samples (4 scams + 1 genuine bank alert)
python tests/run_samples.py path/to/img.png # any real screenshot or recording
python tests/make_samples.py                # regenerate the sample screenshots + call clip
python tests/api_check.py [base_url]        # end-to-end over HTTP (local or deployed)
```

Typical end-to-end time: 9–16 s (Vision ≈ 5 s, 105B ≈ 1.5 s, Translate ≈ 1 s, Bulbul ≈ 3–5 s).

## Deploy (Docker + Cloudflare Tunnel)

```bash
docker compose up -d --build   # serves on 127.0.0.1:8010, reads SARVAM_API_KEY from .env
```

In Cloudflare Zero Trust → Tunnels → your tunnel → **Public Hostname**: add the subdomain → service `http://localhost:8010`
(or `http://scam-kavach:8000` if `cloudflared` runs in the same Docker network).

`RATE_LIMIT_PER_HOUR` (default 20) caps checks per visitor IP, read from Cloudflare's `CF-Connecting-IP` header.

## Privacy & limits

- Messages, images and recordings are processed in memory and temp files, then discarded. Nothing is stored or logged.
- Recordings should be under 30 seconds (synchronous Saaras limit).
- AI can be wrong. The page always points to 1930 and to calling your bank on the number printed on your card.
