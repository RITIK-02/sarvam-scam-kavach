"""Tiny evaluation on INDICA call transcripts (https://huggingface.co/datasets/vikrant-vikram/INDICA).

Expects Text_samples extracted under Data/INDICA/Text_samples (Data/ is gitignored; the dataset has no
license tag, so it is not redistributed here). Runs only the analysis step (Sarvam-105B), N per class per language.

Usage: python tests/eval_indica.py [per_class]   default 2
"""

import random
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import kavach  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent / "Data" / "INDICA" / "Text_samples"
LANGS = ["hindi", "tamil", "bengali", "english"]
PER_CLASS = int(sys.argv[1]) if len(sys.argv) > 1 else 2


def pick(lang: str) -> list[tuple[str, str, Path]]:
    out, rng = [], random.Random(7)
    for cls_dir in sorted((ROOT / f"Text_{lang}").iterdir()):
        label = "legit" if cls_dir.name.lower().startswith("legit") else "fraud"
        files = sorted(cls_dir.iterdir())
        out += [(lang, label, f) for f in rng.sample(files, min(PER_CLASS, len(files)))]
    return out


def judge(item):
    lang, label, path = item
    result = kavach.analyse(path.read_text(encoding="utf-8"))
    flagged = result["verdict"] in ("scam", "suspicious")
    return lang, label, result["verdict"], result.get("scam_type"), flagged == (label == "fraud"), path.parent.name


def main() -> None:
    items = [i for lang in LANGS for i in pick(lang)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(judge, items))
    for lang, label, verdict, kind, ok, folder in rows:
        print(f"{'OK  ' if ok else 'MISS'} {lang:8} {folder:12} -> {verdict:12} {kind}")
    tp = sum(r[4] for r in rows if r[1] == "fraud"); fraud = sum(r[1] == "fraud" for r in rows)
    tn = sum(r[4] for r in rows if r[1] == "legit"); legit = sum(r[1] == "legit" for r in rows)
    print(f"\nfraud caught {tp}/{fraud} · legit passed {tn}/{legit} · accuracy {(tp + tn) / len(rows):.0%}")


if __name__ == "__main__":
    main()
