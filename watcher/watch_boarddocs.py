"""BoardDocs watcher for Hewlett-Woodmere UFSD.

Polls the district's public BoardDocs site for board meetings, finds agenda
items matching the document categories we track, and downloads their PDF
attachments into archive/<category>/. Already-seen meetings and files are
recorded in seen.json, so the first run backfills everything since EARLIEST
and later runs only fetch what's new.

Usage:  python watch_boarddocs.py [--dry-run] [--limit N]
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import requests

BASE = "https://go.boarddocs.com/ny/hwps/Board.nsf"
COMMITTEE_ID = "A4EP6J588C05"  # Board of Education
EARLIEST = "20230101"  # before 2023 the board posted combined packet PDFs

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "archive"
STATE_FILE = Path(__file__).resolve().parent / "seen.json"

# category -> pattern matched against agenda item title and attachment filename
CATEGORIES = {
    "treasurer": r"treasurer",
    "budget-status": r"budget\s*status",
    "revenue-status": r"revenue\s*status",
    "facilities-tours": r"tour\s*of\s*facilities|facilities\s*tour",
}

REQUEST_PAUSE = 0.4  # seconds between requests; be polite to their server

session = requests.Session()
# BoardDocs 403s non-browser user agents, so send a standard one
session.headers["User-Agent"] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def post(endpoint, data):
    time.sleep(REQUEST_PAUSE)
    r = session.post(f"{BASE}/{endpoint}?open", data=data, timeout=60)
    r.raise_for_status()
    return r.text


def get_meetings():
    text = post("BD-GetMeetingsList", {"current_committee_id": COMMITTEE_ID})
    meetings = json.loads(text)
    meetings = [
        m for m in meetings
        if m.get("numberdate") and m["numberdate"] >= EARLIEST and m.get("unique")
    ]
    meetings.sort(key=lambda m: m["numberdate"])
    return meetings


def get_agenda_items(meeting_id):
    """Return [(item_id, title)] for a meeting's public agenda."""
    html = post("BD-GetAgenda", {"id": meeting_id, "current_committee_id": COMMITTEE_ID})
    return re.findall(
        r'unique="([A-Z0-9]+)"\s+unid="[A-F0-9]{32}"\s+Xtitle="([^"]*)"', html
    )


def get_item_files(item_id):
    """Return [(file_id, href, filename)] attachments on an agenda item."""
    html = post("BD-GetPublicFiles", {"id": item_id})
    out = []
    for m in re.finditer(r'href="([^"]*?/files/([A-Z0-9]+)/\$file/([^"]+))"', html):
        href, file_id, name = m.group(1), m.group(2), unquote(m.group(3))
        out.append((file_id, href, name))
    return out


def categorize(*texts):
    for cat, pattern in CATEGORIES.items():
        for t in texts:
            if t and re.search(pattern, t, re.IGNORECASE):
                return cat
    return None


def safe_filename(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def download(href, dest):
    url = href if href.startswith("http") else f"https://go.boarddocs.com{href}"
    time.sleep(REQUEST_PAUSE)
    r = session.get(url, timeout=120)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF") and not dest.suffix.lower() != ".pdf":
        print(f"    WARNING: {dest.name} does not look like a PDF, saving anyway")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    return len(r.content)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"meetings": {}, "files": {}}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, indent=1, sort_keys=True), encoding="utf-8"
    )


def main():
    dry_run = "--dry-run" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    state = load_state()
    meetings = get_meetings()
    print(f"{len(meetings)} meetings on BoardDocs since {EARLIEST}")

    # A meeting is revisited unless marked final: districts add documents to
    # recent meetings after first posting, so only meetings older than 45 days
    # get frozen once processed.
    new_files = []
    processed = 0
    for m in meetings:
        mid, mdate = m["unique"], m["numberdate"]
        rec = state["meetings"].get(mid)
        if rec and rec.get("final"):
            continue
        if limit is not None and processed >= limit:
            break
        processed += 1

        date_str = f"{mdate[:4]}-{mdate[4:6]}-{mdate[6:]}"
        print(f"[{date_str}] {m['name'][:70]}")
        try:
            items = get_agenda_items(mid)
        except Exception as e:
            print(f"    agenda fetch failed: {e}")
            continue

        for item_id, title in items:
            title_cat = categorize(title)
            if not title_cat:
                continue
            try:
                files = get_item_files(item_id)
            except Exception as e:
                print(f"    files fetch failed for '{title[:50]}': {e}")
                continue
            for file_id, href, name in files:
                if file_id in state["files"]:
                    continue
                cat = categorize(name, title) or title_cat
                dest = ARCHIVE / cat / safe_filename(f"{date_str}_{name}")
                if dry_run:
                    print(f"    would download [{cat}] {name}")
                    continue
                try:
                    size = download(href, dest)
                except Exception as e:
                    print(f"    download failed for {name}: {e}")
                    continue
                state["files"][file_id] = {
                    "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
                    "meeting": mid,
                    "date": date_str,
                    "item": title[:120],
                }
                new_files.append((cat, dest.name, size))
                print(f"    saved [{cat}] {name} ({size // 1024} KB)")

        age_days = (datetime.now() - datetime.strptime(mdate, "%Y%m%d")).days
        state["meetings"][mid] = {
            "date": date_str,
            "name": m["name"][:120],
            "final": age_days > 45,
        }
        if not dry_run:
            save_state(state)  # checkpoint after each meeting

    print()
    if new_files:
        print(f"NEW FILES: {len(new_files)}")
        by_cat = {}
        for cat, name, size in new_files:
            by_cat.setdefault(cat, []).append(name)
        for cat, names in sorted(by_cat.items()):
            print(f"  {cat}: {len(names)}")
    else:
        print("No new documents.")


if __name__ == "__main__":
    main()
