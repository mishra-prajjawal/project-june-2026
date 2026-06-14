# BUILD_PLAYBOOK.md — The Phased Doctrine

We build FoodConnect in repeating cycles. **Build → Battle-test → Optimize → repeat until "satisfied."** Do not collapse phases; each has an exit bar.

---

## Phase 0 — Scaffold (one time, before the loop)
- Django project + apps: `accounts`, `donations`, `events`, `analytics`, `core`.
- Connect to **Aiven MySQL** via `.env`; run initial migration; confirm a real round-trip query.
- Tailwind CLI build pipeline + base layout/template + custom CSS layer + theme tokens (green/white/orange).
- Internal event-bus skeleton (signals) + the **SSE** push endpoint stub (decided transport — do not use WebSockets in v1).
- `README.md`, `.env.example`, `requirements.txt`, `package.json`, `PROGRESS.md`, `LICENSE` (Apache 2.0).
- Seed/fixtures command.
- **Exit bar:** app boots locally, talks to Aiven MySQL, serves a styled page, `pytest`/`manage.py test` runs (even if near-empty).

## Phase 1 — Build (per vertical slice)
Build slices end-to-end in this order, each slice = model → event → service → API/view → reactive UI → tests:
1. **Auth & roles** (register/login/logout, role-aware, password hashing, NGO starts unverified).
2. **Admin verification & user management** (verify/reject NGO, ban user) + `ngo_verified` / `user_banned` events.
3. **Donor: post donation** (form, image, geolocation prefill, validation) + `donation_posted` event + live feed push.
4. **NGO: browse + claim** (concurrency-safe claim service, lock item, contact reveal + Call Now) + `donation_claimed` event.
5. **Collect + feedback + impact points + leaderboard** + `donation_collected` event.
6. **Analytics/impact report** (servings/KG saved, scores, charts).
7. **Polish screens:** landing/leaderboard, empty/error/404 states, animated thank-you.

**Rules during Phase 1**
- Write human comments and tests **as you build**, not after.
- Every slice ends with the relevant rows ticked in `PROGRESS.md`.
- Post a short plan before the slice and a report after (with test output).
- **Exit bar for the phase:** the slice works through the UI, reactively where specified, with green tests.

## Phase 2 — Battle-test (end-to-end, heavy)
Test the backend until it cannot be broken:
- **Unit tests:** every service/model method incl. invalid input — negative quantity, blank fields, past expiry, wrong role, unverified NGO claiming, banned user acting.
- **Integration tests:** full flows register → verify → post → claim → collect → feedback.
- **Concurrency/race test:** N simultaneous claims on one donation → assert exactly one wins, others get a clean "already claimed" response.
- **Endpoint stress test:** hammer the busy endpoints (feed, claim) — measure response times, watch for N+1 queries, deadlocks, and integrity errors. Use a script under `/tests/stress/` and paste real numbers.
- **Dry runs:** seed realistic data, walk every screen on a mobile viewport.
- **Security checks:** attempt SQLi on inputs, attempt cross-role access, confirm CSRF + auth gates hold.
- **Exit bar:** all tests green, no race condition, no SQLi, documented latency numbers, zero unhandled 500s in the happy + key-failure paths.

## Phase 3 — Optimize & refine
- **UI/UX:** tighten spacing, motion, contrast, mobile ergonomics; refine the donate flow toward ≤30s; verify accessibility (screen reader + contrast).
- **Logic:** simplify, de-duplicate, harden the state machine, improve error messages.
- **Performance:** kill N+1 queries (`select_related`/`prefetch_related`), add indexes, cache the leaderboard/feed where safe, profile the **SSE** push (connection count, reconnects, payload size).
- **Bugs:** triage and fix everything found in Phase 2; add a regression test for each bug fixed.
- **Exit bar:** measurably faster/cleaner than the previous cycle, no known open bugs, tests still green.

## Repeat
Go back to Phase 1 for the next improvement set. Continue the loop until the user explicitly says **"satisfied."**

---

## Reporting format (use every phase)
```
### Phase X report — <slice/area>
- Built/changed: <bullet list, files touched>
- Events wired: <which signals emit/consume>
- Tests: <counts> | command: <cmd> | result: <PASTE REAL OUTPUT>
- Stress/concurrency (Phase 2+): <numbers>
- PROGRESS.md updated: <yes, which items>
- Open risks / decisions: <DESIGN NOTEs, questions>
- Next: <what comes next>
```

## Definition of Done reminder (gate for every feature)
Implemented per spec · reachable + aesthetic + responsive · event-wired + reactive · tested (happy + key failures) · secure · documented + ticked in PROGRESS.md. **A red or skipped test means NOT done.**
