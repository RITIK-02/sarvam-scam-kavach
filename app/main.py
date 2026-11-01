import logging
import os
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app import kavach

log = logging.getLogger("kavach")
logging.basicConfig(level=logging.INFO)

STATIC = Path(__file__).parent / "static"
MAX_UPLOAD = 4 * 1024 * 1024  # Vercel request body limit is 4.5 MB
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_HOUR", "20"))  # checks per IP per hour
_hits: dict[str, deque] = defaultdict(deque)

app = FastAPI(title="Scam Kavach", docs_url=None, redoc_url=None)


def _client_ip(request: Request) -> str:
    # Behind Cloudflare Tunnel the real visitor IP arrives in CF-Connecting-IP.
    fwd = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return request.headers.get("cf-connecting-ip") or fwd or (request.client.host if request.client else "unknown")


def _rate_limit(ip: str) -> None:
    now, window = time.time(), _hits[ip]
    while window and now - window[0] > 3600:
        window.popleft()
    if len(window) >= RATE_LIMIT:
        raise HTTPException(429, "Too many checks from your network. Please try again in an hour.")
    window.append(now)


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/languages")
def languages():
    return kavach.OUTPUT_LANGUAGES


@app.post("/api/check")
def check(request: Request, language: str = Form("hi-IN"), text: str = Form(""),
          image: UploadFile | None = File(None), audio: UploadFile | None = File(None)):
    if language not in kavach.OUTPUT_LANGUAGES:
        raise HTTPException(400, "Please choose a supported language.")

    def read(upload: UploadFile | None):
        if not upload or not upload.filename:
            return None
        data = upload.file.read(MAX_UPLOAD + 1)
        if len(data) > MAX_UPLOAD:
            raise HTTPException(413, "File is too large (max 4 MB).")
        return (data, upload.filename) if data else None

    img, aud = read(image), read(audio)
    if not (img or aud or text.strip()):
        raise HTTPException(400, "Add a screenshot, a recording, or paste the message.")
    if len(text) > 5000:
        raise HTTPException(400, "Message is too long (max 5000 characters).")

    _rate_limit(_client_ip(request))
    started = time.time()
    try:
        result = kavach.run(language, text=text, image=img, audio=aud)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        log.exception("check failed")
        raise HTTPException(502, "Could not analyse this message right now. Please try again.")
    log.info("check ok kind=%s verdict=%s lang=%s %.1fs", "image" if img else "audio" if aud else "text",
             result["verdict"], language, time.time() - started)
    return JSONResponse(result)
