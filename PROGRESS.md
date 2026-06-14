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
- [ ] Register (role-aware), login, logout
- [ ] Password hashing PBKDF2/Argon2 (NOT MD5)
- [ ] NGO starts unverified; banned flag respected

## Admin module
- [ ] Secure admin login
- [ ] NGO verification queue (approve/reject from documents)
- [ ] Monitor all active + past donations
- [ ] Manage/ban users
- [ ] System metrics dashboard
- [ ] Events: ngo_verified, user_banned

## Donor module
- [ ] Registration (name/address/phone)
- [ ] Post donation (food, quantity, expiry, address, image)
- [ ] Geolocation prefill of address
- [ ] Track status (Available → Claimed → Collected)
- [ ] Donation history
- [ ] Impact score + leaderboard rank visible
- [ ] Event: donation_posted + live feed push
- [ ] Animated green ✓ "Thank You" confirmation

## NGO / Volunteer module
- [ ] Registration + document upload (awaits verification)
- [ ] Browse available food (sorted by time, urgency-highlighted)
- [ ] Claim donation (concurrency-safe lock)
- [ ] Donor contact reveal + "Call Now" button
- [ ] Confirm collection (sets collected_at)
- [ ] Post-collection quality survey (Yes/No)
- [ ] Requests table created (future UI flagged)
- [ ] Events: donation_claimed, donation_collected

## Core logic
- [ ] Single claim state-machine service
- [ ] Concurrency: select_for_update / atomic conditional update
- [ ] Concurrency test: simultaneous claims → exactly one wins
- [ ] Expired items flagged + excluded from claimable list
- [ ] Impact points awarded on collection

## Analytics / impact
- [ ] Total servings/KG saved
- [ ] Per-user Social Impact Score
- [ ] Charts on report page
- [ ] Leaderboard on landing/home

## Screens
- [ ] Landing + leaderboard
- [ ] Auth screens
- [ ] Donor dashboard
- [ ] NGO dashboard
- [ ] Admin panel
- [ ] Analytics/impact report
- [ ] 404 / empty / error states

## UI/UX bar
- [ ] Mobile-first, fast on entry-level phones
- [ ] Green/white + orange-urgency theme tokens
- [ ] Readable sans-serif typography
- [ ] Donate flow ≤ ~30s / 3 steps, large inputs/dropdowns
- [ ] Live no-refresh updates everywhere specified
- [ ] Accessibility: contrast, hit targets, semantic HTML, ARIA live regions, keyboard + screen-reader

## Non-functional
- [ ] Dashboard < ~2s load
- [ ] FKs + constraints + indexes
- [ ] Security: CSRF, parameterized ORM (no SQLi), per-role authz, secrets in env
- [ ] Scalable structure (add cities without core rewrite)

## Testing (Phase 2)
- [ ] Unit tests incl. invalid input
- [ ] Integration tests for full flows
- [ ] Concurrency/race test
- [ ] Endpoint stress test (latency numbers recorded)
- [ ] Mobile dry-run on every screen
- [ ] Security probes (SQLi, cross-role, CSRF)

## Docs (synopsis alignment)
- [ ] Architecture note (MVT mapping)
- [ ] ER diagram + schema (Mermaid /docs)
- [ ] DFD Level 0/1/2 (Mermaid /docs)
- [ ] README local-run guide against Aiven MySQL

## Local run
- [ ] Clone → documented steps → working app on localhost against Aiven MySQL
