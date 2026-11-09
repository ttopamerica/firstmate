---
name: secondmate-handoff
description: >-
  Load on every intake of project-specific work to route it to a fitting registered secondmate, or provision one before handing off when none fits.
user-invocable: false
metadata:
  internal: true
---

# Secondmate handoff

This local workflow selects secondmate handoff as the primary firstmate's default for project-specific coding, investigation, planning, reproduction, and audit requests.
It replaces the optional main-home fallback when no registered scope fits.
In a secondmate home, follow the existing charter and worker dispatch lifecycle rather than recursively provisioning another secondmate for each intake.

Keep firstmate-home operational work on main: wakes, locks, session management, and local Firstmate configuration do not warrant a new secondmate.
A current explicit redirect to main wins for its stated scope.
Preserve the existing `local-only` placement restriction in [secondmate-provisioning](../secondmate-provisioning/SKILL.md); this workflow does not change delivery modes to make a handoff possible.

1. Resolve the project through [AGENTS.md section 7](../../../AGENTS.md#7-task-lifecycle), then match the work against registered secondmates' natural-language scopes, not their clone lists.
   Reuse the startup digest's registry evidence unless targeted inspection is needed.
2. Load [secondmate-provisioning](../secondmate-provisioning/SKILL.md) before provisioning, recovery, or handoff.
   If a registered scope fits, route to that secondmate; recover an unavailable endpoint under that skill instead of creating a duplicate mate.
   A blocked route stays a reported blocker rather than silently becoming a main-home ship.
3. If no scope fits, create a persistent secondmate with a charter covering the project's domain, then hand off the request.
   Use secondmate-provisioning's existing seed, validation, launch, and backlog-handoff procedures, and load [harness-adapters](../harness-adapters/SKILL.md) before launching or recovering it.
   Preserve configured harness, account, and backend choices and existing publication-consent boundaries.
   Do not ask whether to create a mate merely because none exists; creation is the requested default.
   If required information or a provisioning guard prevents creation, report the concrete blocker and retain the work for that route.
4. Complete the durable backlog handoff and routed instruction under secondmate-provisioning, preserving the request's intent and delivery authority.
   Supervise the secondmate as a direct report through its marked replies; it owns its workers and project delivery.

This skill changes intake routing only; the existing provisioning, backlog, supervision, and landing owners retain their safety and authorization contracts.
