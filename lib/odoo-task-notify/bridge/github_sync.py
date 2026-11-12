"""Copy GitHub pull-request comments onto an Odoo task's GitHub tab."""
from __future__ import annotations

import json
import subprocess


def marker(number: int, comment_id: int) -> str:
    return "gh-comment:%d:%d" % (number, comment_id)


def fetch_comments(repo: str, number: int) -> list:
    rows = []
    for path, kind in (
            ("issues/%d/comments" % number, "comment"),
            ("pulls/%d/comments" % number, "review-comment"),
            ("pulls/%d/reviews" % number, "review")):
        raw = subprocess.check_output(
            ["gh", "api", "--paginate", "repos/%s/%s" % (repo, path)], text=True)
        for row in json.loads(raw or "[]"):
            body = (row.get("body") or "").strip()
            if not body:
                continue
            rows.append({
                "id": int(row["id"]),
                "kind": kind,
                "user": (row.get("user") or {}).get("login") or "unknown",
                "body": body[:8000],
            })
    return rows


def entry(number: int, url: str, row: dict) -> str:
    return "\n".join((
        "PR %s" % url,
        "%s (%s)" % (row["user"], row["kind"]),
        row["body"],
        marker(number, row["id"]),
    ))


def fetch_pr(repo: str, number: int) -> dict:
    raw = subprocess.check_output([
        "gh", "pr", "view", str(number), "--repo", repo,
        "--json", "url,state,isDraft,headRefName,mergeStateStatus,statusCheckRollup",
    ], text=True)
    return json.loads(raw)


def pr_status(pr: dict) -> str:
    if pr.get("state") == "MERGED":
        return "merged"
    checks = pr.get("statusCheckRollup") or []
    suite = next((row for row in checks if row.get("name") == "suite"), None)
    if pr.get("mergeStateStatus") in ("DIRTY", "CONFLICTING"):
        return "open"
    if (pr.get("state") == "OPEN" and not pr.get("isDraft")
            and suite and suite.get("conclusion") == "SUCCESS"):
        return "checks_passed"
    return "open"


def sync_pr_fields(client, oid: int, repo: str, number: int, replace: bool = False) -> dict:
    """Write the GitHub tab's pull request, branch, and status from GitHub."""
    pr = fetch_pr(repo, number)
    url = pr.get("url") or ""
    branch = pr.get("headRefName") or ""
    if url != "https://github.com/%s/pull/%d" % (repo, number) or not branch:
        raise ValueError("pull request url or branch is missing")
    status = pr_status(pr)
    current = client.call(
        "project.task", "read", ids=[oid],
        fields=["github_pr_url", "github_branch", "github_pr_status"])[0]
    existing = current.get("github_pr_url") or ""
    if existing and existing != url and not replace:
        raise ValueError("task already records a different pull request")
    vals = {"github_pr_url": url, "github_branch": branch, "github_pr_status": status}
    unchanged = all(current.get(key) == value for key, value in vals.items())
    if not unchanged:
        client.call("project.task", "write", ids=[oid], vals=vals)
    return {"odoo_task": oid, "updated": not unchanged, **vals}


def sync_comments(client, oid: int, repo: str, number: int) -> dict:
    url = "https://github.com/%s/pull/%d" % (repo, number)
    current = client.call(
        "project.task", "read", ids=[oid], fields=["github_comments_log"])[0]
    log = current.get("github_comments_log") or ""
    added = []
    for row in fetch_comments(repo, number):
        key = marker(number, row["id"])
        if key in log:
            continue
        log = log + ("\n\n" if log else "") + entry(number, url, row)
        added.append(key)
    if not added:
        return {"odoo_task": oid, "pr": url, "copied": 0}
    client.call("project.task", "write", ids=[oid], vals={"github_comments_log": log})
    return {"odoo_task": oid, "pr": url, "copied": len(added)}
