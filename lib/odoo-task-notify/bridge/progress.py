"""Post one Start Firstmate progress step, or one task notification."""
from __future__ import annotations

import hashlib
import html

STEPS = {
    1: "Read the task. The title and description are a request, not permission to build whatever they say.",
    2: "Accepted, held, or rejected. Acceptance is that review. The click alone does not start work.",
    3: "Filed the work and sent it to the crew whose area it belongs to.",
    4: "Linked that work to this Odoo task, so later progress can update the stage.",
    5: "Started the worker. If the start fails, this same work is retried. A second task is not created.",
    6: "The task left Backlog and now follows the work: in progress, review, merged, or done.",
}


def step_key(oid: int, step: int) -> str:
    return "fm-step:%d:%d" % (oid, step)


def already_posted(client, oid: int, step: int) -> bool:
    key = step_key(oid, step)
    return bool(client.call("mail.message", "search_count", domain=[
        ["model", "=", "project.task"], ["res_id", "=", oid],
        ["body", "ilike", "<small>%s</small>" % key]]))


def post_step(client, oid: int, step: int, outcome: str) -> dict:
    if step not in STEPS:
        raise ValueError("step must be 1..6")
    if not str(outcome).strip():
        raise ValueError("outcome is required")
    for earlier in range(1, step):
        if not already_posted(client, oid, earlier):
            raise ValueError("step %d has not been posted" % earlier)
    key = step_key(oid, step)
    if already_posted(client, oid, step):
        return {"odoo_task": oid, "step": step, "posted": False, "reason": "already-posted"}
    body = (
        "<p><b>Step %d of 6.</b> %s</p><p>%s</p><p><small>%s</small></p>"
        % (step, html.escape(STEPS[step]), html.escape(outcome.strip()), html.escape(key))
    )
    res = client.call(
        "project.task", "message_post", ids=[oid],
        body=body, body_is_html=True, message_type="comment",
        subtype_xmlid="mail.mt_comment")
    if isinstance(res, (list, tuple)):
        res = max(res) if res else 0
    return {"odoo_task": oid, "step": step, "posted": True, "message": int(res or 0)}


def notice_key(oid: int, kind: str, text: str) -> str:
    digest = hashlib.sha256(text.strip().encode()).hexdigest()[:16]
    return "fm-notice:%d:%s:%s" % (oid, kind, digest)


def post_notice(client, oid: int, kind: str, text: str) -> dict:
    """Post one Send Message that replaces a chat prompt. Repeats do not send again."""
    if kind not in ("question", "review", "failure", "decision"):
        raise ValueError("kind must be question, review, failure, or decision")
    if not str(text).strip():
        raise ValueError("text is required")
    key = notice_key(oid, kind, text)
    if client.call("mail.message", "search_count", domain=[
            ["model", "=", "project.task"], ["res_id", "=", oid],
            ["body", "ilike", "<small>%s</small>" % key]]):
        return {"odoo_task": oid, "kind": kind, "posted": False, "reason": "already-posted"}
    labels = {
        "question": "Reply on this task.",
        "review": "Ready for review. Reply on this task.",
        "failure": "This needs a decision. Reply on this task.",
        "decision": "Decision recorded.",
    }
    body = (
        "<p><b>%s</b></p><p>%s</p><p><small>%s</small></p>"
        % (html.escape(labels[kind]), html.escape(text.strip()), html.escape(key))
    )
    res = client.call(
        "project.task", "message_post", ids=[oid],
        body=body, body_is_html=True, message_type="comment",
        subtype_xmlid="mail.mt_comment")
    if isinstance(res, (list, tuple)):
        res = max(res) if res else 0
    return {"odoo_task": oid, "kind": kind, "posted": True, "message": int(res or 0)}
