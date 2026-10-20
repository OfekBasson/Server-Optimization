# Canvas Lab Server Manager

A small web app for sharing a research lab's GPU servers fairly.

Labs often have a handful of expensive GPU machines shared by many
students. People book a server "for the week", finish early, and the
machine sits idle while someone else waits. Or someone starts a job on a
machine that's already booked, and nobody notices until there's a
conflict. This project tackles that with three things:

1. **A booking calendar per server** — see who has which machine, when,
   and book time yourself.
2. **Live usage monitoring** — a lightweight agent on every server reports
   GPU/CPU/RAM load and *which Linux user* is running each GPU process.
3. **Gentle WhatsApp nudges** — if a booked server has been idle for a
   while, the person holding it is asked whether they still need it, and
   anyone waiting for a similar machine is told it may be free.

The app never takes a reservation away on its own: it only informs
people, and the holder always decides.

It was built for the Canvas Lab's six GPU servers (`mass-01` … `mass-06`),
but nothing about it is specific to that lab — the server list is just
seed data.

## Features

- **Dashboard** with every server, its hardware, current status, and
  who has it reserved right now.
- **Per-server calendar** (week/day views): click-drag to book, drag or
  resize an existing booking to move it, right-click to release it.
- **"Notify me" watch requests**: say "I need e.g. 2+ RTX 3090s", and get
  a WhatsApp message when a matching server frees up. Requests expire, so
  they don't pile up.
- **Idle detection**: a booked server whose holder isn't running anything
  and whose GPUs are near 0% for a configurable time (default 2 h) is
  flagged, and the holder gets a nudge.
- **Takeover alerts**: if someone *else* starts using a server that's
  booked but idle, the holder is told who.
- **Long-booking check-ins**: holders of reservations running longer
  than a few days (default 5) are periodically asked if they still need
  the time.
- **Usage analytics**: reserved hours vs. actually-used hours per person,
  exportable as CSV.
- **Admin page** for managing lab members, their WhatsApp numbers, and
  other admins.

## How it works

```
 ┌──────────────┐   every 15 min    ┌──────────────────────────┐
 │ GPU server 1 │ ── usage + ────▶  │                          │
 │  (agent.py)  │   process owners  │   Backend (FastAPI)      │◀──── Browser
 └──────────────┘                   │   + PostgreSQL           │      (React app)
 ┌──────────────┐                   │                          │
 │ GPU server N │ ───────────────▶  │   Scheduler (every 15m): │
 │  (agent.py)  │                   │   idle / takeover /      │──▶ WhatsApp
 └──────────────┘                   │   long-booking checks    │    (Twilio)
                                    └──────────────────────────┘
```

- **Agent** (`agent/`) — a plain Python daemon (not an AI agent) that runs
  on each GPU server under systemd. It reads GPU stats via NVIDIA's NVML
  plus CPU/RAM via `psutil`, and posts a snapshot to the backend.
- **Backend** (`backend/`) — FastAPI + SQLAlchemy over PostgreSQL (SQLite
  works for local trials). Holds servers, users, reservations, usage
  samples, and watch requests. An in-process APScheduler job compares
  each active reservation against the latest usage sample.
- **Frontend** (`frontend/`) — React + TypeScript + Vite, with FullCalendar
  for the booking views.

To tell "the holder is using their booking" apart from "someone else is",
the backend needs to know which Linux account belongs to which lab
member on each machine. That's stored as an **OS-username mapping** (see
[Mapping Linux accounts to people](#mapping-linux-accounts-to-people)).

### Who can do what

- **Lab members don't log in.** When you book a server or create a
  watch request, a dialog asks you to pick your name from the list of
  members. There are no passwords for regular users, so the app is meant
  to run on a trusted lab network or behind a private link.
- **Admins log in** with email + password (top-right of the page). Only
  admins can open the Admin page to add members, set WhatsApp numbers, and
  promote other admins.

## Try it locally

You can run the whole app on any laptop to look around. It doesn't
connect to any real server and doesn't send any messages (notifications
are logged instead of sent unless you explicitly enable Twilio).

### Option A — Python + Node only (quickest)

Requires Python 3.9+ and Node.js 18+. Uses a local SQLite file instead of
PostgreSQL.

```bash
git clone https://github.com/OfekBasson/Server-Optimization.git
cd Server-Optimization/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

```bash
export DATABASE_URL="sqlite:///$(pwd)/demo.db"
python3 scripts/init_db.py
python3 scripts/seed_servers.py
python3 scripts/seed_admin.py "Your Name" you@example.com
python3 scripts/seed_demo_data.py
uvicorn app.main:app --port 8000
```

`seed_admin.py` asks for a password. `seed_demo_data.py` is optional — it
adds a few fake members and bookings so the calendars aren't empty.

In a second terminal:

```bash
cd Server-Optimization/frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Log in (top right) with the admin email
and password you just created to see the Admin page.

### Option B — Docker (same setup as production)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop)
(open the app once so the `docker` command works) and Node.js.

```bash
git clone https://github.com/OfekBasson/Server-Optimization.git
cd Server-Optimization
cp .env.example .env
docker compose up --build
```

In a second terminal, in the same folder:

```bash
docker compose exec backend python scripts/seed_servers.py
docker compose exec backend python scripts/seed_admin.py "Your Name" you@example.com YourPassword
docker compose exec backend python scripts/seed_demo_data.py
```

Then start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The API runs on http://localhost:8000,
with interactive docs at http://localhost:8000/docs.

To stop, press `Ctrl+C` in both terminals, then run `docker compose down`
(add `-v` to also wipe the local database).

## Repository layout

```
backend/            FastAPI app
  app/routers/      REST endpoints (servers, reservations, usage, watch requests, admin, analytics)
  app/services/     scheduler (idle/stale checks), matching, WhatsApp notifications
  scripts/          init_db, seed_servers, seed_admin, seed_demo_data
agent/              Monitoring daemon + systemd unit for each GPU server
frontend/           React app (dashboard, per-server calendar, admin page)
docker-compose.yml       Local stack: PostgreSQL + backend
docker-compose.prod.yml  Production stack: PostgreSQL + backend + Caddy
Caddyfile           Reverse proxy serving the built frontend and /api
.github/workflows/deploy.yml  Auto-deploy to the lab server on every push to main
```

## Configuration

All settings are environment variables, read from `.env` (copy
`.env.example` for local use, `.env.prod.example` for production).

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | local PostgreSQL | SQLAlchemy URL; `sqlite:///...` also works |
| `SESSION_SECRET_KEY` | `change-me-too` | Signs admin session cookies — **set a random value in production** |
| `AGENT_API_KEY` | `change-me` | Shared secret the agents use to post usage |
| `CORS_ORIGINS` | `http://localhost:5173` | Origins allowed to call the API |
| `NOTIFICATIONS_ENABLED` | `false` | When `false`, messages are only logged |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_WHATSAPP_FROM` | empty | Twilio credentials for WhatsApp |
| `IDLE_THRESHOLD_MINUTES` | `120` | How long a booked server must be idle before it's flagged |
| `IDLE_GPU_UTIL_PERCENT_THRESHOLD` | `5` | GPU utilization below this counts as idle |
| `STALE_RESERVATION_DAYS` | `5` | Bookings older than this get "still need it?" check-ins |
| `NUDGE_COOLDOWN_HOURS` | `12` | Minimum gap between repeated nudges |
| `SCHEDULER_INTERVAL_MINUTES` | `15` | How often the checks run |
| `AGENT_POLL_INTERVAL_MINUTES` | `15` | Agent reporting interval (used for analytics) |

## The servers

The default server list lives in `backend/scripts/seed_servers.py`. Edit
it to match your own hardware; re-running it is safe (existing servers
are skipped by name).

| Server | GPUs | VRAM per GPU |
|---|---|---|
| mass-01 | 4× RTX 3090 | 24 GB |
| mass-02 | Quadro RTX 5000 + TITAN V | 16 GB / 12 GB |
| mass-03 | 4× RTX 3090 | 24 GB |
| mass-04 | 4× RTX 3090 | 24 GB |
| mass-05 | 2× RTX 6000 Ada | 48 GB |
| mass-06 | RTX PRO 6000 Blackwell Max-Q | 96 GB |

## Deploying

### The web app

Production runs `docker-compose.prod.yml` on one machine: PostgreSQL, the
backend, and Caddy serving the built frontend on `127.0.0.1:8080`. The
lab exposes it publicly with [Tailscale Funnel](https://tailscale.com/kb/1223/funnel),
which gives a free HTTPS address without opening inbound ports; any other
reverse proxy or tunnel works too.

On the host:

```bash
git clone https://github.com/OfekBasson/Server-Optimization.git
cd Server-Optimization
cp .env.prod.example .env
```

Fill in `.env`: generate `POSTGRES_PASSWORD`, `SESSION_SECRET_KEY` and
`AGENT_API_KEY` with `openssl rand -hex 32`, and set `DOMAIN` to the
public hostname. Then:

```bash
cd frontend && npm ci && npm run build && cd ..
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_servers.py
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_admin.py "Admin Name" admin@example.com
```

To expose it with Tailscale Funnel:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --hostname=canvaslab
sudo tailscale funnel --bg 8080
```

The last command prints the public URL (`https://canvaslab.<tailnet>.ts.net`);
put its hostname in `DOMAIN` and run `docker compose -f docker-compose.prod.yml up -d`
again.

**Auto-deploy:** `.github/workflows/deploy.yml` SSHes into the host on
every push to `main`, pulls, rebuilds the frontend, restarts the stack,
and runs `init_db.py` (which only creates missing tables). It needs these
repository secrets: `DEPLOY_HOST`, `DEPLOY_PORT`, `DEPLOY_USER`,
`DEPLOY_SSH_KEY` (a private key whose public half is in the deploy
user's `~/.ssh/authorized_keys`), and `DEPLOY_PATH` (where the repo is
cloned on the host). It can also be run manually from the **Actions**
tab.

### The monitoring agent (on each GPU server)

```bash
git clone https://github.com/OfekBasson/Server-Optimization.git /tmp/canvas-lab
sudo mkdir -p /opt/canvas-lab-agent
sudo cp /tmp/canvas-lab/agent/agent.py /opt/canvas-lab-agent/
python3 -m pip install --user -r /tmp/canvas-lab/agent/requirements.txt
sudo cp /tmp/canvas-lab/agent/canvas-lab-agent.env.example /etc/canvas-lab-agent.env
sudo nano /etc/canvas-lab-agent.env
```

Set these in `/etc/canvas-lab-agent.env`:

```
BACKEND_URL=https://<your-app-host>
AGENT_API_KEY=<same value as the backend's AGENT_API_KEY>
SERVER_NAME=mass-01
POLL_INTERVAL_SECONDS=900
```

`SERVER_NAME` must match the server's name in the backend. Then install
and start the service:

```bash
sudo cp /tmp/canvas-lab/agent/canvas-lab-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now canvas-lab-agent
journalctl -u canvas-lab-agent -f
```

The agent restarts automatically if it crashes or the machine reboots.

### Mapping Linux accounts to people

For idle and takeover detection, each lab member's Linux username on each
server has to be linked to their account in the app. There's no UI for
this yet; use the API:

```bash
curl -X POST https://<your-app-host>/api/os-usernames -H "Content-Type: application/json" -d '{"university_email": "jane.doe@example.com", "server_name": "mass-01", "os_username": "jdoe"}'
```

Repeat once per person per server. If the email isn't a member yet, one is
created automatically. List mappings with
`GET /api/os-usernames?server_name=mass-01`.

### Turning on WhatsApp messages

Create a Twilio account with WhatsApp enabled, put its credentials in
`.env`, set `NOTIFICATIONS_ENABLED=true`, and add each member's WhatsApp
number on the Admin page. Until then, every notification is computed and
written to the log, so you can check what would have been sent.

## Status and known limitations

This is an early, working version built for one lab.

- Regular users pick their name rather than logging in, so anyone with
  access to the site can act as anyone else. Keep it on a trusted network
  or private link.
- The OS-username mapping endpoint has no auth check yet.
- Server CPU/RAM/disk specs aren't filled in by default, so watch requests
  can currently only filter on GPU type and count.
- There are no automated tests yet.
