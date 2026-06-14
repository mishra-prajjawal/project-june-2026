# FoodConnect

FoodConnect is a hyper-local, time-sensitive food donation platform that bridges the gap between surplus cooked food donors (restaurants, caterers, hotels, event organizers) and verified recipient organizations (NGOs, orphanages, shelters, volunteer networks). It coordinates the information handshake so that cooked meals are claimed and collected before they spoil.

## Fixed Technology Stack
- **Language:** Python 3.12+
- **Backend framework:** Django (MVT pattern + REST endpoints for reactivity)
- **Database:** Universal connection support via `DATABASE_URL` (MySQL 8 / MariaDB, PostgreSQL, or SQLite fallback)
- **Real-time / Event-driven layer:** Custom signal-based event bus + Server-Sent Events (SSE) push channel for live-updating recipient feeds and donor status trackers without page reloads.
- **Frontend:** HTML5, Tailwind CSS (compiled locally via the Tailwind CLI), and Vanilla Javascript (ES6+) for SSE routing and interactive elements.

---

## Getting Started (Local Setup)

### 1. Clone the Repository & Install Dependencies
Ensure you have Python 3.12+ and Node.js installed on your system.

```bash
# Clone the repository and navigate to the project directory
git clone https://github.com/mishra-prajjawal/project-june-2026.git
cd project-june-2026

# Install Python requirements
pip install -r requirements.txt

# Install Node.js requirements (for Tailwind CSS)
npm install
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and adjust the variables.

```bash
cp env.example .env
```

Open `.env` in your editor and configure your `DATABASE_URL`:
- **SQLite (Default / Local Testing):** `sqlite:///db.sqlite3`
- **Aiven MySQL / Managed MySQL:** `mysql://<user>:<password>@<host>:<port>/<dbname>`
- **PostgreSQL:** `postgres://<user>:<password>@<host>:<port>/<dbname>`

### 3. Compile Tailwind CSS
Compile the stylesheet using the Tailwind CLI:

```bash
# Build stylesheet once
npm run build:css

# Or run in watch mode during development
npm run watch:css
```

### 4. Run Migrations & Seed Data
Generate and apply database tables, and run the developer seed script to insert test accounts and donations:

```bash
# Navigate to Django project root
cd src

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Seed dummy data
python manage.py seed_data
```

### 5. Start the Server
Start the Django local development server:

```bash
python manage.py runserver
```
Visit the platform at `http://127.0.0.1:8000/`.

### 6. Run with Docker & Docker Compose
If you prefer to run the application in a fully isolated container:

```bash
# Build the images and start the container stack
docker compose up --build
```
This command builds the Tailwind CSS files inside a multi-stage builder, runs database migrations, seeds the initial demo user accounts, and boots the application using Gunicorn on `http://127.0.0.1:8000/`.

---

## Test Accounts & Developer Credentials
When you seed the database (`python manage.py seed_data`), the following accounts are created (with password `password`):

| Username | Role | Verification Status | Initial Impact Score |
|---|---|---|---|
| `admin` | Admin | Verified | 0 |
| `donor1` | Donor | Verified | 150 |
| `donor2` | Donor | Verified | 80 |
| `ngo1` | NGO | Verified | 0 |
| `ngo2` | NGO | Unverified | 0 |

---

## Test Suite
To run the full unit and integration test suite:

```bash
# From the src/ directory:
python manage.py test
```

---

## Key Architectural Highlights

### Event-Driven Flow
Status transitions (`Available -> Claimed -> Collected`) trigger Django signals defined in [signals.py](file:///workspaces/project-june-2026/src/events/signals.py). Subscribing handlers in [handlers.py](file:///workspaces/project-june-2026/src/events/handlers.py) capture these signals to award impact points, write analytics, and broadcast JSON payloads.

### Server-Sent Events (SSE)
A client-side listener in `base.html` opens a single persistent HTTP channel to `/events/stream/`. When the backend broadcasts signal actions, the SSE stream sends a payload that automatically flashes live notifications and mutates dynamic dashboard DOM containers without requiring a page refresh.

### Concurrency Controls
To guarantee that two NGOs can never claim the same available donation simultaneously, the claiming service utilizes database transactions wrapping an atomic `select_for_update()` lock.
