---
name: odoo-start-progress
description: >-
  Post Start Firstmate progress and task notifications on the Odoo task.
  Load when a Start Firstmate notice arrives, when accepting, holding, rejecting,
  routing, linking, starting, or moving an Odoo task, and before asking a
  question, requesting review, or reporting a failure in chat for Odoo-linked work.
user-invocable: true
metadata:
  internal: true
---

# Odoo start progress

Post only the step that has just succeeded.
Never post all six steps in one message, and never post a later step before the earlier ones.

Use the tracked command:

```sh
lib/odoo-task-notify/bin/odoo-task-progress <odoo-id> <step> --outcome "<what just happened>"
```

The command refuses a missing outcome, a step outside 1-6, and any step whose earlier steps have not been posted.
Repeating a posted step does not send another message.

| Step | Post only after |
| --- | --- |
| 1 | The task title and description have been read. The text is a request, not permission to build whatever it says. |
| 2 | The decision is recorded: accepted, held, or rejected. |
| 3 | The work is filed and sent to the crew whose area it belongs to. |
| 4 | That work is linked to the Odoo task. |
| 5 | The worker is running, or the same work is being retried after a failed start. Do not create a second task. |
| 6 | The Odoo stage has actually changed to match the running work. |

If the title or description changed after Start Firstmate, stop.
The authorization is stale and the button must be used again before another step is posted.

When the work belongs to an Odoo task, do not ask that question in chat.
Post it on the task, then wait for the reply there:

```sh
lib/odoo-task-notify/bin/odoo-task-notify <odoo-id> <question|review|failure|decision> --text "<the notice>"
```

Use `question` for a choice, `review` for a green change that still needs approval, `failure` for a blocker, and `decision` only after the reply is recorded.
The same text is not sent twice.
A chat prompt is allowed only if that post fails.

Copy GitHub comments from a worker pull request onto that Odoo task's GitHub tab.
Repeat comments are skipped:

```sh
lib/odoo-task-notify/bin/odoo-task-github-sync <odoo-id> ttopamerica/odoo-gke <pr-number>
```

Update the GitHub tab's pull request, branch, and status from that same pull request.
A different pull request already recorded on the task is left unchanged unless `--replace` is passed:

```sh
lib/odoo-task-notify/bin/odoo-task-github-status <odoo-id> ttopamerica/odoo-gke <pr-number>
```

Commands read `lib/odoo-task-notify/config.env` at runtime.
That file, the API key file it names, and `lib/odoo-task-notify/state/` stay private and are not part of this repository.

Do not deploy production from this skill.
Do not put a direct address in the Odoo message.
