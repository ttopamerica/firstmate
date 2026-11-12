"""Notify Firstmate once when Start Firstmate authorizes a new unbound task."""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bridge.odoo import Json2, ReadOnly  # noqa: E402

SEEN = ROOT / "state" / "start-notified.json"
REPLIES = ROOT / "state" / "reply-notified.json"
SOURCE = "https://app.teatop82ranch.com/odoo/project/3/tasks/"


def env():
    out = {}
    for line in (ROOT / "config.env").read_text().splitlines():
        if not line.strip() or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key] = value.strip().strip('"').strip("'")
    return out


def bound(props):
    if isinstance(props, dict):
        return bool(props.get("fm_task_id"))
    return any(isinstance(p, dict) and p.get("name") == "fm_task_id" and p.get("value")
               for p in props or [])


def load_seen():
    try:
        data = json.loads(SEEN.read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_json(path, data):
    path.parent.mkdir(mode=0o700, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, sort_keys=True) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def save_seen(data):
    save_json(SEEN, data)


def plain(html):
    text = re.sub(r"<[^>]+>", " ", html or "")
    return " ".join(text.split())


def new_replies(client, seen_ids):
    rows = client.call(
        "mail.message", "search_read",
        domain=[["model", "=", "project.task"], ["message_type", "=", "comment"],
                ["id", ">", max(seen_ids or [0])]],
        fields=["id", "res_id", "author_id", "body"], limit=30, order="id asc")
    fresh = []
    for row in rows:
        author = row.get("author_id") or [None, ""]
        if author[0] in (None, 90) or "Firstmate" in str(author[1]):
            seen_ids.append(row["id"])
            continue
        task = client.call("project.task", "read", ids=[row["res_id"]],
                            fields=["name", "project_id", "task_properties"])
        task = task[0] if task else {}
        if (task.get("project_id") or [None])[0] != 3 or bound(task.get("task_properties")):
            seen_ids.append(row["id"])
            continue
        fresh.append((row, task))
    return fresh, seen_ids


def main():
    config = env()
    key = Path(config["ODOO_API_KEY_FILE"]).read_text().strip()
    client = ReadOnly(Json2(config["ODOO_URL"], config["ODOO_DB"], key))
    rows = client.call(
        "project.task", "search_read",
        domain=[["project_id", "=", 3], ["firstmate_start_date", "!=", False]],
        fields=["id", "name", "firstmate_start_digest", "task_properties"],
        limit=50)
    seen = load_seen()
    fresh = []
    for row in rows:
        if bound(row.get("task_properties")):
            continue
        digest = row.get("firstmate_start_digest") or ""
        if seen.get(str(row["id"])) == digest:
            continue
        fresh.append(row)
    reply_seen = load_json(REPLIES)
    replies, reply_seen = new_replies(client, reply_seen if isinstance(reply_seen, list) else [])
    if not fresh and not replies:
        save_json(REPLIES, reply_seen)
        return 0
    for row in fresh:
        name = " ".join(str(row.get("name") or "").split())[:120]
        print(f"odoo-start task {row['id']} authorized: {name} {SOURCE}{row['id']}")
        seen[str(row["id"])] = row.get("firstmate_start_digest") or ""
    for row, task in replies:
        text = plain(row.get("body"))[:240]
        print(f"odoo-reply task {row['res_id']} {text} {SOURCE}{row['res_id']}")
        reply_seen.append(row["id"])
    save_seen(seen)
    save_json(REPLIES, reply_seen)
    return 0


def load_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return []


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print("odoo-start scan-error; source preserved; retry/reconcile required")
        raise SystemExit(0)
