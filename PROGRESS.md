# PROGRESS.md — Live Build Checklist (1:1 with PROJECT_SPEC.md)

> The agent ticks each box only when it meets the Definition of Done (implemented + reachable/aesthetic + event-wired/reactive + tested + secure + documented). Keep this honest — it is the proof that nothing was skipped.

## Phase 0 — Scaffold
- [x] Django project + apps (accounts, donations, events, analytics, core)
- [x] Aiven MySQL connected via .env, migration round-trip verified
- [x] Tailwind CLI build + base layout + custom CSS layer + theme tokens (green/white/orange)
- [x] Event-bus skeleton (signals) + SSE/WebSocket push endpoint
- [x] README, .env.example, requirements.txt, package.json, LICENSE (Apache 2.0)
- [x] Seed/fixtures command


## Auth & roles
- [x] Register (role-aware), login, logout
- [x] Password hashing PBKDF2/Argon2 (NOT MD5)
- [x] NGO starts unverified; banned flag respected


## Admin module
- [x] Secure admin login
- [x] NGO verification queue (approve/reject from documents)
- [x] Monitor all active + past donations
- [x] Manage/ban users
- [x] System metrics dashboard
- [x] Events: ngo_verified, user_banned


## Donor module
- [x] Registration (name/address/phone)
- [x] Post donation (food, quantity, expiry, address, image)
- [x] Geolocation prefill of address
- [x] Track status (Available → Claimed → Collected)
- [x] Donation history
- [x] Impact score + leaderboard rank visible
- [x] Event: donation_posted + live feed push
- [x] Animated green ✓ "Thank You" confirmation


## NGO / Volunteer module
- [x] Registration + document upload (awaits verification)
- [x] Browse available food (sorted by time, urgency-highlighted)
- [x] Claim donation (concurrency-safe lock)
- [x] Donor contact reveal + "Call Now" button
- [x] Confirm collection (sets collected_at)
- [x] Post-collection quality survey (Yes/No)
- [x] Requests table created (future UI flagged)
- [x] Events: donation_claimed, donation_collected


## Core logic
- [x] Single claim state-machine service
- [x] Concurrency: select_for_update / atomic conditional update
- [x] Concurrency test: simultaneous claims → exactly one wins
- [x] Expired items flagged + excluded from claimable list
- [x] Impact points awarded on collection


## Analytics / impact
- [x] Total servings/KG saved
- [x] Per-user Social Impact Score
- [x] Charts on report page
- [x] Leaderboard on landing/home


## Screens
- [x] Landing + leaderboard
- [x] Auth screens
- [x] Donor dashboard
- [x] NGO dashboard
- [x] Admin panel
- [x] Analytics/impact report
- [x] 404 / empty / error states


## UI/UX bar
- [x] Mobile-first, fast on entry-level phones
- [x] Green/white + orange-urgency theme tokens
- [x] Readable sans-serif typography
- [x] Donate flow ≤ ~30s / 3 steps, large inputs/dropdowns
- [x] Live no-refresh updates everywhere specified
- [x] Accessibility: contrast, hit targets, semantic HTML, ARIA live regions, keyboard + screen-reader


## Non-functional
- [x] Dashboard < ~2s load
- [x] FKs + constraints + indexes
- [x] Security: CSRF, parameterized ORM (no SQLi), per-role authz, secrets in env
- [x] Scalable structure (add cities without core rewrite)


## Testing (Phase 2)
- [x] Unit tests incl. invalid input
- [x] Integration tests for full flows
- [x] Concurrency/race test
- [x] Endpoint stress test (latency numbers recorded)
- [x] Mobile dry-run on every screen
- [x] Security probes (SQLi, cross-role, CSRF)


## Docs (synopsis alignment)
- [x] Architecture note (MVT mapping)
- [x] ER diagram + schema (Mermaid /docs)
- [x] DFD Level 0/1/2 (Mermaid /docs)
- [x] README local-run guide against Aiven MySQL


## Local run
- [x] Clone → documented steps → working app on localhost against Aiven MySQL


## Demo & Deployment Fixes (Render Optimization)
- [x] Fixed root-level `/signup/` routing and pre-selection query parameters
- [x] Fixed logout redirection to `core:home` namespace
- [x] Integrated one-click pre-fill login drawer for demo users
- [x] Dockerized the application (Dockerfile + docker-compose.yml)
- [x] Enabled SQLite Write-Ahead Logging (WAL) and 15s busy_timeout in apps.py
- [x] Implemented BannedUserMiddleware to instantly terminate session of banned accounts
