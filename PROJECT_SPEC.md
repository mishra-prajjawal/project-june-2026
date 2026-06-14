# PROJECT_SPEC.md — FoodConnect (Authoritative Scope)

> This is the single source of truth for **what must be built**. Every item here ships. The agent maintains `PROGRESS.md` as a 1:1 checklist against this document. **Nothing here may be skipped.**

---

## 1. One-line definition
FoodConnect is a hyper-local, **time-sensitive** web platform that connects food **donors** (restaurants, event managers, individuals) with **recipients** (orphanages, old-age homes, verified NGOs/volunteers), so that surplus cooked food in the "middle scale" (10–50 servings) is claimed and collected before it spoils — typically within a 5–10 km radius.

The platform owns the **information/handshake**, not the logistics. Recipients arrange their own pickup.

## 2. Objectives (all must be demonstrably met)
- Donors can post food (type, quantity, expiry/best-before, address, image) in **under ~2 minutes**.
- NGO **verification** system so food goes only to legitimate causes.
- **Status tracking** that notifies the donor when food is Claimed and Collected (closure/satisfaction).
- **Analytics reports**: total servings/KGs saved, plus a per-user **Social Impact Score**.
- **Lightweight** enough to run smoothly on basic mobile browsers (mobile-first, fast).

## 3. Roles & primary modules (three modules — build all three)

### 3.1 Admin Module
- Secure login/logout.
- **Verify NGOs:** approve/reject NGO registrations based on uploaded documents.
- **Monitor donations:** view all active and past donations.
- **Manage users:** ban users who post fake requests, fail to collect, or misuse the platform.
- Oversight dashboard with system-wide metrics.

### 3.2 Donor Module
- Registration (Name, Address, Phone, password).
- **Post Donation:** form for Food Name, Quantity (servings), Best-Before / Expiry time, Address, optional image. Geolocation pre-fills address where possible (crude is fine).
- **Track Status:** see each donation as `Available/Pending → Claimed → Collected`.
- **History:** past donations.
- See own **Social Impact Score** and leaderboard rank.

### 3.3 NGO / Volunteer Module
- Registration with document upload (awaits admin verification before claiming).
- **Browse donations:** list of available food, sorted by time posted (and surfacing soon-to-expire items).
- **Claim donation:** locks the item so others cannot claim it (concurrency-safe).
- **Confirm collection:** mark as `Collected` after pickup.
- On claim: receive donor contact info + a **"Call Now"** action.
- **Quality feedback:** after collection, a one-question survey ("Was the quality acceptable? Yes/No").
- (Future-flagged but stub the table) **Requests:** NGOs post specific needs ("Need 50 packets Sunday").

## 4. Data model (relational — MySQL on Aiven)

> Build these as Django models. Use a custom User model or a Profile extension to carry `role`. Use proper FKs, indexes on hot columns (`status`, `expiry_time`, `created_at`), and DB-level constraints.

### 4.1 `users` (User + Profile)
| Column | Type | Notes |
|---|---|---|
| user_id | INT PK auto-increment | |
| username | VARCHAR unique | |
| password_hash | VARCHAR | Django PBKDF2/Argon2 — **never MD5** |
| role | ENUM('Donor','NGO','Admin') | |
| contact_info | VARCHAR | phone/email |
| address | TEXT | |
| is_verified | BOOL | NGOs start false until admin approves |
| is_banned | BOOL | admin action |
| impact_score | INT default 0 | drives leaderboard |
| created_at | TIMESTAMP | |

### 4.2 `donations`
| Column | Type | Notes |
|---|---|---|
| donation_id | INT PK | |
| donor_id | FK → users | |
| food_item | VARCHAR | e.g. "Rice and Curry" |
| quantity | VARCHAR | e.g. "5 kg" / "30 servings" |
| image | file/path | optional photo |
| expiry_time | DATETIME | best-before |
| status | ENUM('Available','Claimed','Collected') | state machine |
| claimed_by | FK → users (NGO), nullable | |
| latitude / longitude | FLOAT, nullable | crude location matching |
| address | TEXT | |
| created_at | TIMESTAMP | |
| collected_at | DATETIME, nullable | |

### 4.3 `requests` (future feature — create table + minimal UI hook)
| Column | Type | Notes |
|---|---|---|
| req_id | INT PK | |
| ngo_id | FK → users | |
| description | TEXT | e.g. "Need 50 packets Sunday" |
| created_at | TIMESTAMP | |

### 4.4 `quality_feedback`
| Column | Type | Notes |
|---|---|---|
| feedback_id | INT PK | |
| donation_id | FK → donations | |
| ngo_id | FK → users | |
| acceptable | BOOL | Yes/No survey |
| created_at | TIMESTAMP | |

### 4.5 Relationships
- User **POSTS** Donation (1:N).
- User (NGO) **CLAIMS** Donation (1:N).
- User (NGO) **MAKES** Request (1:N).
- Donation **HAS** QualityFeedback (1:1 after collection).

## 5. Core logic — the Claim state machine (the heart of the app)
`Available → Claimed → Collected`, enforced by ONE service function:
- **Claim** is only valid from `Available`, by a **verified, non-banned NGO**.
- **Concurrency:** wrap the read-check-write in a DB transaction with `select_for_update()` (or an atomic conditional `UPDATE ... WHERE status='Available'`) so **two NGOs can never claim the same donation**. Build a test that fires simultaneous claims and asserts exactly one succeeds.
- **Collect** is only valid from `Claimed`, by the claiming NGO; sets `collected_at`, awards impact points to the donor, triggers the feedback survey.
- Expired items (`expiry_time < now`) are visually flagged and excluded from claimable lists.

## 6. Event-driven architecture (must be genuinely event-driven)
Internal **event bus** (Django signals) with at least these events:
- `donation_posted` → update live feed, notify nearby verified NGOs, recompute counters.
- `donation_claimed` → notify donor, push contact info to NGO, remove from others' available list (live).
- `donation_collected` → award impact points, update leaderboard, trigger feedback survey, notify donor.
- `ngo_verified` / `user_banned` → admin-driven side effects.

**Reactive UI push (DECIDED: Server-Sent Events / SSE):** dashboards update live over SSE — a new donation or a claim appears for relevant users **without a manual refresh**. SSE is the chosen transport for v1 (one-way server → browser fits this feed perfectly); WebSockets are future scope only. This is a hard requirement, not a nice-to-have.

## 7. Screens / UI inventory (build every screen)
1. Landing/home with **Leaderboard** of top donors + impact stats.
2. Auth: register (role-aware), login, logout.
3. Donor dashboard: post-donation form (3-step, geolocation prefill), my donations + live status, my impact.
4. NGO dashboard: live available-food feed (sorted by time, urgency-highlighted), claim button, my claims, confirm-collection, post-collection feedback.
5. Admin panel: NGO verification queue, all donations monitor, user management/ban, system metrics.
6. Analytics/Impact report page: total servings/KG saved, social impact scores, charts.
7. 404 / empty states / error states.

## 8. UI/UX requirements (cannot be compromised — see STYLE_GUIDE.md)
- **Mobile-first**, fast on entry-level phones.
- **Palette:** Green (freshness/eco) + White (cleanliness); **Orange** for "Urgent"/expiring-soon alerts. Implement as Tailwind theme tokens.
- **Typography:** clean sans-serif (Roboto / Open Sans / Inter), highly readable.
- **Forms:** large inputs, dropdowns over free typing, minimal friction. Donate flow ≤ ~30s / 3 steps.
- **Gamification:** prominent Top-Donor leaderboard on home.
- **Visual confirmation:** large animated green ✓ "Thank You" after posting; "Call Now" button (not plain text) after claim.
- **Accessibility:** high contrast, large hit targets, full screen-reader navigability, semantic HTML, ARIA where needed.
- **Feedback loop:** one-question quality survey after collection.

## 9. Non-functional requirements
- **Performance:** dashboard loads < ~2s; live updates feel instant.
- **Reliability/Integrity:** concurrency control prevents double-claims; FKs + constraints keep data consistent.
- **Security:** hashed passwords (PBKDF2/Argon2), CSRF, parameterized ORM queries (no SQLi), per-role authorization, secrets in env.
- **Scalability:** code structured so new cities/regions can be added without rewriting core logic.

## 10. Environment & local-run requirements
- Runs fully on `localhost` against **Aiven MySQL**.
- `.env` driven config (Aiven host/port/user/password/db, SSL cert path if required by Aiven, Django secret key, debug flag).
- Tailwind built locally via CLI (`npm run build:css` / watch mode).
- Seed script for demo data (donors, NGOs pending + verified, donations in each state).
- `README.md` so a reviewer can go from clone → running app in a few documented steps.

## 11. License
- Codebase is OSS under **Apache 2.0**, no warranty/liability. Include `LICENSE` file. Author: Prajjawal Mishra.

## 12. Documentation deliverables (academic synopsis alignment)
Keep these so the build maps cleanly to the synopsis:
- System architecture note (MVC/MVT mapping).
- ER diagram + schema (Mermaid in `/docs`).
- DFDs: Level 0 (context), Level 1 (auth / manage donations / search-claim), Level 2 (claim/concurrency). Provide as Mermaid in `/docs`.
- Methodology, expected outcomes, conclusion notes (can live in `/docs`).

## 13. Future Scope (DO NOT build now — only these are deferrable)
- AI image recognition to auto-detect food type from photo.
- Google Maps route optimization for multi-pickup.
- React Native mobile app with push notifications.
- Dedicated volunteer-driver intermediary network.
- Full `requests`-board workflow (table is created now; rich UI is future).

> If it is in sections 1–12, it ships in this build. If it is in section 13, it is explicitly deferred. There is no third category.
