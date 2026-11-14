# NOTES.md — overnight crew checkpoint (not for commit)

## Team Rules (read before acting)

Set by Nick, 2026-11-14 02:10 UTC.

1. **Scope / done**: the crew hunts for real defects. An issue exists only once a
   failing test proves it. Done = failing-then-passing test, green full suite,
   reviewed diff, draft PR. Maximum 4 fixes tonight.
2. **Off-limits**: nothing beyond the standing rules — no secrets, production
   data, migrations, billing or anything public without Nick's yes.
3. **Proof gate (mirror CI)**: `pip install -e ".[dev]"`, `pytest -q` (full
   suite), and the ruff check from `.github/workflows/ci.yml`. No live LLM or
   market-data calls.
4. **Budget**: brief due 07:30 UTC. Max 4 parallel builders. Stuck 20 minutes →
   write one question, park, move on.

Standing rules: never weaken, skip or delete a test. No new dependency without a
reason in the PR. No refactors beyond the issue. Smallest change that turns the
test green wins. Handoffs use ISSUE / TEST / EVIDENCE / NEXT STEP.

## Status

- 02:10 UTC — intake complete. Waiting for Nick's go. Nothing mapped, no
  baseline run yet.
