# Head-to-Toe Codebase Guide — FoodConnect

This document provides a comprehensive head-to-toe walk-through of the entire **FoodConnect** project codebase. It outlines the directory structure, describes the implementation details of each app, explains the execution flows, and defines configuration settings.

---

## 1. Directory Tree & File Index

```text
/workspaces/project-june-2026/
├── .dockerignore           # Excludes local files (sqlite, nodes) from Docker context
├── .editorconfig           # Standardizes line endings, tab widths, and spaces
├── .gitignore              # Ignores compiled python files, media folder, envs, sqlite
├── .prettierrc             # Defines code styling format rules for JS and HTML
├── AGENTS.md               # Constitution and rules of development
├── BUILD_PLAYBOOK.md       # Implementation phase workflows and testing guidelines
├── Dockerfile              # Multi-stage image build (compiles CSS, registers Gunicorn)
├── docker-compose.yml      # Orchestrates local container builds and ephemeral DB volumes
├── package.json            # Node project configuration for compiling Tailwind CSS
├── requirements.txt        # Pinned Python dependencies (Django, Pillow, Gunicorn, etc.)
├── tailwind.config.js      # Custom Tailwind theme overrides (brand colors, typography)
├── docs/                   # Academic synopsis diagrams & codebase documents
│   ├── architecture.md     # MVT mapping and custom SSE pipeline diagram
│   ├── codebase_guide.md   # [This File] Complete codebase walk-through
│   ├── dfd_diagrams.md     # Level 0, Level 1, and Level 2 Data Flow Diagrams
│   └── er_diagram.md       # Relational database entities and constraints
└── src/                    # Django Application Root
    ├── manage.py           # Django execution controller (runserver, migrate, seed)
    ├── db.sqlite3          # Ephemeral local database (Optimized in WAL mode)
    ├── foodconnect/        # Root Django Configuration Folder
    │   ├── settings.py     # Main project configurations, database toggles, middlewares
    │   ├── urls.py         # Main URL dispatcher mapping root routes (/signup, /login)
    │   └── wsgi.py         # Web Server Gateway Interface entry point for Gunicorn
    ├── accounts/           # Accounts, User Profiles & Access Controls
    │   ├── apps.py         # Registers accounts config
    │   ├── forms.py        # Role-aware registration form with dynamic document requirement
    │   ├── middleware.py   # BannedUserMiddleware terminating banned active sessions
    │   ├── models.py       # Custom User model containing roles, points, verification states
    │   ├── services.py     # Transactional services (verify, reject, toggle ban)
    │   ├── urls.py         # URL patterns (/auth/register/, verification endpoints)
    │   └── views.py        # Dashboard router and admin verification view handlers
    ├── donations/          # Donation Listings, Lifecycles & Coordination
    │   ├── forms.py        # DonationPostForm validating inputs (excludes past expiry)
    │   ├── models.py       # Donation model (Available/Claimed/Collected), stubs for Requests
    │   ├── services.py     # Concurrency-safe claim execution select_for_update locks
    │   ├── urls.py         # Mappings (/donations/post/, /donations/claim/<id>/, etc.)
    │   └── views.py        # Views rendering donor and NGO dashboards (N+1 queries optimized)
    ├── events/             # Custom Signal-Based SSE Broadcast Pipeline
    │   ├── handlers.py     # Django signal receivers packaging payloads and modifying scores
    │   ├── signals.py      # Custom Django Signal definitions
    │   ├── sse.py          # Thread-safe in-memory SSEManager client queue registry
    │   ├── urls.py         # Route mapping to SSE text/event-stream
    │   └── views.py        # StreamingHttpResponse yielding keepalives and broadcasts
    ├── analytics/          # Serving Computations & Charts
    │   ├── urls.py         # Mappings to analytics endpoint
    │   └── views.py        # Database-agnostic aggregate logic (servings, quality rate)
    ├── core/               # Public Landing page & Admin Dashboard
    │   ├── management/     # Management commands
    │   │   └── commands/   # Custom django-admin scripts
    │   │       └── seed_data.py  # Non-interactive developer database seed script
    │   ├── urls.py         # Routing for home and admin panel
    │   └── views.py        # Home view (ranks top 10 donors) and Admin panel (tab-swapping)
    ├── static/             # Static Assets
    │   └── css/            # Stylesheets
    │       ├── input.css   # Raw Tailwind CSS entrypoint
    │       └── output.css  # Compiled and minified production CSS (built via CLI)
    ├── templates/          # HTML Template Layer
    │   ├── base.html       # Root HTML structure, Inter typography, global SSE listener
    │   ├── 404.html        # Custom Page Not Found error page
    │   ├── 500.html        # Custom Server Error page
    │   ├── accounts/       # User profile screens (login, register)
    │   ├── analytics/      # Analytical report page containing Chart.js graphs
    │   ├── core/           # Landing page and admin panel oversight screens
    │   └── donations/      # Donor/NGO dashboards, listing wizards, feedback surveys
    └── tests/              # Test Suites
        ├── __init__.py     # Package initialization
        ├── test_concurrency.py # Transactional checks firing concurrent claims
        ├── test_integration.py # End-to-end platform user lifecycle simulations
        ├── test_security.py    # Enforces role auth boundaries and CSRF missing blocks
        └── stress/         # Endpoint Latency and Stress Test suite
            ├── __init__.py # Discovers stress test package
            ├── stress_test.py    # Simulates 16 concurrent users hitting views in threads
            └── test_endpoints.py # Benchmarks GET latencies for hot endpoints
```

---

## 2. Core Config & Dispatcher

### 2.1 settings.py ([src/foodconnect/settings.py](file:///workspaces/project-june-2026/src/foodconnect/settings.py))
- **`AUTH_USER_MODEL = "accounts.User"`**: Sets the custom user model as the default authentication user.
- **`MIDDLEWARE`**: Standard stack containing security, session, auth, and message middleware. Appended with `accounts.middleware.BannedUserMiddleware` to force-logout banned accounts.
- **`DATABASE_URL`**: Switched dynamically using `django-environ`. Swaps between Aiven Managed MySQL (for staging/production) and SQLite (local dev).
- **`LOGIN_REDIRECT_URL = "dashboard"`** & **`LOGOUT_REDIRECT_URL = "core:home"`**: Enforces login redirects to the role-aware dashboard router and logout redirects back to the home page.

### 2.2 urls.py ([src/foodconnect/urls.py](file:///workspaces/project-june-2026/src/foodconnect/urls.py))
Routes root requests to appropriate views:
- `/login/`: Renders Django's auth LoginView.
- `/logout/`: Handles session terminations.
- `/signup/`: Maps `/signup/` to `accounts_views.register` view.
- `/dashboard/`: Resolves to the dashboard router.

---

## 3. Account Profiles & Security (`accounts/`)

### 3.1 Custom User Model ([src/accounts/models.py](file:///workspaces/project-june-2026/src/accounts/models.py))
- Extends `AbstractUser`. Adds fields: `role` (Choice: Donor, NGO, Admin), `contact_info`, `address`, `is_verified` (NGOs start unverified; Donors/Admins are auto-verified in `save()`), `is_banned` (resets access immediately), and `impact_score` (gamification tracking).

### 3.2 Registration Form ([src/accounts/forms.py](file:///workspaces/project-june-2026/src/accounts/forms.py))
- Extends `UserCreationForm`. Customizes clean validation: if the chosen role is `NGO`, a registration file upload is strictly required (`verification_document`).

### 3.3 Session Ban Middleware ([src/accounts/middleware.py](file:///workspaces/project-june-2026/src/accounts/middleware.py))
- `BannedUserMiddleware` checks if an authenticated user has `is_banned = True`.
- If true, calls `logout(request)`, appends a session message, and redirects to `login/`.
- Placed after `MessageMiddleware` to prevent initialization errors in test clients.

### 3.4 Services Layer ([src/accounts/services.py](file:///workspaces/project-june-2026/src/accounts/services.py))
Decoupled logic for admin actions:
- `verify_ngo_user(user_id, admin_user)`: Approves NGO, fires `ngo_verified` signal.
- `reject_ngo_user(user_id, admin_user)`: Deletes registration of rejected NGO.
- `toggle_user_ban(user_id, admin_user)`: Flips user ban status, fires `user_banned` signal.

---

## 4. Donation Lifecycle & Concurrency (`donations/`)

### 4.1 Models ([src/donations/models.py](file:///workspaces/project-june-2026/src/donations/models.py))
- **`Donation`**: Contains coordinates, expiry timestamp, address, status (`Available`, `Claimed`, `Collected`), and relations to `donor` and `claimed_by`.
- **`QualityFeedback`**: One-to-one mapping to `Donation`. Holds the acceptability check boolean.
- **`Request`**: Stub table for future NGO requests.

### 4.2 Concurrency-Safe Claiming ([src/donations/services.py](file:///workspaces/project-june-2026/src/donations/services.py))
- **`claim_donation(donation_id, ngo_user)`**:
  - Enforces database transactions using `transaction.atomic()`.
  - Executes `select_for_update()` on the target `Donation` row to lock it.
  - Verifies if the status is still `Available` and if it is not expired.
  - If valid, sets status to `Claimed`, sets `claimed_by = ngo_user`, and fires the `donation_claimed` signal.
  - If locked or already claimed, raises `ValueError`, preventing double-claiming under race conditions.

---

## 5. Signal Event Bus & SSE Real-time Updates (`events/`)

### 5.1 Signal Handlers ([src/events/handlers.py](file:///workspaces/project-june-2026/src/events/handlers.py))
- Listens to signals: `donation_posted`, `donation_claimed`, `donation_collected`, `ngo_verified`, and `user_banned`.
- On `donation_collected`, automatically parses the quantity field (e.g., "30 servings" -> 30) and atomically increments the donor's `impact_score` in a `select_for_update` block.
- Forwards event payloads (as JSON dicts) to the `sse_manager` for distribution.

### 5.2 Thread-Safe SSE Manager ([src/events/sse.py](file:///workspaces/project-june-2026/src/events/sse.py))
- Implements `SSEManager` using a `threading.Lock()` to thread-safely append client connections into `queue.Queue` objects.
- `broadcast(data, event_type)` formats the JSON payload using `text/event-stream` schema, loops through active connections, and enqueues the payload. Full queues are automatically cleaned up.

---

## 6. Frontend CSS & JavaScript Reactivity

### 6.1 Styles & Theme ([src/static/css/input.css](file:///workspaces/project-june-2026/src/static/css/input.css))
- Theme overrides define green primaries (`#059669`), white backgrounds (`#ffffff`), and warning alerts (`#ea580c`).
- Node compiles raw Tailwind styles into `output.css` using `npm run build:css`.

### 6.2 Base Templates & SSE Dispatch ([src/templates/base.html](file:///workspaces/project-june-2026/src/templates/base.html))
- Embedded JavaScript establishes a persistent `EventSource` connection to `/events/stream/` on connection load.
- Dispatches event payloads to specific windows via custom document triggers (e.g., `sse:donation_posted`).
- Dynamically injects toast notification banners to notify active users of real-time actions.
