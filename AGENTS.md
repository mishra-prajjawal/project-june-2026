# AGENTS.md — FoodConnect Engineering Charter

This file is the constitution for any AI coding agent working on **FoodConnect**. It overrides your defaults. If anything you are about to do conflicts with this file, stop and re-read it. **Do not skip, shortcut, or silently descope anything.**

---

## 0. Prime directive
> Build the FoodConnect product **completely**, make it **work locally end-to-end**, make it **well tested**, and make it **beautiful and fast**. Nothing in `PROJECT_SPEC.md` is allowed to be missing.

If you are tempted to write "TODO", "left as an exercise", "in a real app you would...", or to mock out a feature instead of building it — **don't**. Build the real thing. If a feature is genuinely out of scope, it is listed under *Future Scope* in `PROJECT_SPEC.md`; everything else ships.

---

## 1. Fixed technology stack (do not substitute)
- **Language:** Python 3.12+
- **Backend framework:** Django (with Django REST-style JSON endpoints for the reactive parts; plain Django views/templates are fine for server-rendered pages).
- **Database:** **Aiven MySQL** (managed MySQL). Use the Aiven connection string from environment variables. MySQL 8 / MariaDB-compatible SQL only.
- **Real-time / event-driven layer:** A **custom event-driven architecture**:
  - An internal **event bus** built on Django signals (e.g. `donation_posted`, `donation_claimed`, `donation_collected`, `ngo_verified`).
  - A **push channel to the browser** so dashboards update without manual refresh. **DECIDED: use Server-Sent Events (SSE)** — it is the chosen approach for its simplicity and low overhead, and it fits this app's one-way "server → browser" live-feed model. Do NOT use WebSockets/Channels for v1; WebSockets is recorded only as a future upgrade path (mark with `# FUTURE:`). The UI must feel *live*.
  - Frontend listens and reactively patches the DOM (vanilla JS + small helpers; AJAX/fetch for actions).
- **Frontend:** HTML5 + **Tailwind CSS** (compiled locally via the Tailwind CLI, not a random CDN in production) + a **thin custom CSS layer** for things Tailwind can't express cleanly (animations, brand details). Vanilla JS (ES6+) for interactivity and AJAX.
- **Server:** Django dev server for local; document a WSGI (gunicorn) path for completeness.
- **Editor-agnostic**, but include formatting config (`black`, `isort`, `prettier`, `.editorconfig`).

## 2. What "event-driven & reactive" means here (must be real)
- Posting a donation **emits an event**; subscribers (notifications, leaderboard recompute, live feed) react. No giant procedural view doing everything inline.
- The recipient dashboard receives **live updates** when new food is posted or an item is claimed/collected — without a full page reload.
- State transitions (`Available → Claimed → Collected`) are driven through a single, well-tested service/state-machine function, not scattered `if` blocks.

## 3. Security (non-negotiable)
- Passwords hashed with Django's default hashers (**PBKDF2 or Argon2**). **NEVER MD5, never plaintext.** (The synopsis mentioned MD5 — we deliberately upgrade this; leave a `# DESIGN NOTE:` explaining why.)
- All DB access via the Django ORM or parameterized queries. **No string-formatted SQL.** SQL injection must be impossible.
- CSRF protection on, secrets in `.env` (never committed), `DEBUG=False` documented for prod.
- Authorization checks on every endpoint: a Donor cannot hit Admin actions, an unverified NGO cannot claim, etc.
- Concurrency: claiming a donation MUST be safe under race conditions — use `select_for_update()` inside a DB transaction (or an atomic conditional update) so **two NGOs can never claim the same item**.

## 4. Code quality & human authorship (see STYLE_GUIDE.md)
- Write code and comments **like a competent human developer**, not like generated boilerplate. Comments explain *why*, name trade-offs, and occasionally show personality — but stay professional and accurate.
- Meaningful names, small functions, clear module boundaries (`models`, `services`, `events`, `views/api`, `selectors`).
- No dead code, no copy-paste duplication, no commented-out junk left lying around.

## 5. Testing bar (see BUILD_PLAYBOOK.md Phase 2)
- Unit tests for every service function and model method (including invalid input: negative quantities, past expiry, empty fields).
- Integration tests for each full flow (register → verify → post → claim → collect).
- Concurrency test that fires simultaneous claims and asserts exactly one wins.
- Endpoint stress/dry-run pass before sign-off. Paste real test output in your phase report.
- **Nothing is "done" with a red or skipped test.**

## 6. Definition of Done (every feature)
A feature is done only when ALL are true:
1. Implemented per `PROJECT_SPEC.md` (no missing sub-requirement).
2. Reachable through the UI with the intended aesthetic and mobile-first responsiveness.
3. Emits/consumes the right events and updates the UI reactively where specified.
4. Covered by passing tests (happy path + at least the key failure paths).
5. Secure (authz + validation + safe queries).
6. Documented (docstring/comments + an entry ticked in `PROGRESS.md`).

## 7. Required repository artifacts
- `README.md` — exact local setup against Aiven MySQL, run commands, test commands, and a feature tour.
- `.env.example` — every required variable.
- `requirements.txt` (pinned) and `package.json` for the Tailwind build.
- `PROGRESS.md` — live checklist mirroring `PROJECT_SPEC.md`.
- `tests/` — the full suite.
- Seed/fixtures script to populate demo donors, NGOs, and donations for review.

## 8. Behavioural rules for the agent
- Begin every work session by re-reading `PROJECT_SPEC.md` and `PROGRESS.md`.
- Post a plan before building; post a report (with real test output) after.
- Never claim something works without running it. If you can't run it, say so.
- If blocked or uncertain, surface it with options. Do not invent fake data or silently stub.
- Prefer finishing a vertical slice fully over scattering half-features.

> Repeat the loop — Build → Battle-test → Optimize — until the user says **"satisfied."**
