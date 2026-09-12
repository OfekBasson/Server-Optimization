# Canvas Lab Server Manager

Booking calendars, idle-server detection, and WhatsApp nudges for the lab's
servers. See the data model and workflow notes in this project's planning
discussion for the full design rationale; this README covers running it.

## Layout

- `backend/` — FastAPI + PostgreSQL API, plus the scheduled jobs that detect
  idle-but-reserved servers and long-standing reservations.
- `agent/` — monitoring daemon deployed to each server; reports GPU/CPU/RAM
  usage and per-process OS ownership to the backend.
- `frontend/` — React app: per-server calendar, dashboard, watch-request form.

## The servers

Seeded by `backend/scripts/seed_servers.py` (edit that file if hardware
changes — safe to re-run, it skips servers that already exist by name):

| Server | PI | GPUs | VRAM (per GPU) | SSH |
|---|---|---|---|---|
| mass-01 | Ohad | 4x RTX 3090 | 24GB | `ssh <user>@mass.ohadf.com -p 1203` |
| mass-02 | Ohad | Quadro RTX 5000 + TITAN V | 16GB / 12GB (mixed) | `ssh <user>@mass.ohadf.com -p 1110` |
| mass-03 | Arik & Ohad | 4x RTX 3090 | 24GB | `ssh <user>@mass.ohadf.com -p 1206` |
| mass-04 | Arik & Ohad | 4x RTX 3090 | 24GB | `ssh <user>@mass.ohadf.com -p 1205` |
| mass-05 | Arik & Ohad | 2x RTX 6000 Ada | 48GB | `ssh <user>@mass.ohadf.com -p 1204` |
| mass-06 | Arik & Ohad | RTX PRO 6000 Blackwell Max-Q | 96GB (verify) | `ssh <user>@mass.ohadf.com -p 1214` |

`cpu_cores` / `ram_gb` / `disk_gb` aren't filled in yet (not provided) —
add them via `POST /api/servers` or directly in the DB if you want watch
requests to filter on those too.

## Just want to look at it? (no Docker, no deploy)

The fastest way to see the actual app running, on your own machine, with
nothing installed but Python and Node - no Postgres, no Docker, no lab
server:

```bash
git clone https://github.com/OfekBasson/Server-Optimization.git
cd Server-Optimization
git checkout claude/canvas-lab-server-manager-dlef6l

# Backend, pointed at a local SQLite file instead of Postgres
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="sqlite:///$(pwd)/demo.db"
export PYTHONPATH="$(pwd)"
python3 scripts/init_db.py
python3 scripts/seed_servers.py       # real mass-01..06 hardware
python3 scripts/seed_demo_data.py     # 2 fake users + 2 bookings so it's not empty

uvicorn app.main:app --port 8000      # leave this running
```

In a second terminal:

```bash
cd Server-Optimization/frontend
npm install
npm run dev                            # leave this running too
```

Open **http://localhost:5173**. You'll see the real dashboard and calendars,
with mass-01 shown as reserved by the demo data.

What works without any further setup: browsing the dashboard, opening a
server's calendar, seeing the idle/reserved status. What needs the Azure
step below first: clicking to actually create a new booking or watch
request through the UI (both now require being signed in) — until then,
you can still create test bookings directly via the interactive API docs
at **http://localhost:8000/docs** (try `POST /api/reservations`) and see
them show up in the calendar.

To stop: `Ctrl+C` both terminals. Nothing here touches the real lab
servers or sends any notifications (Twilio is off by default) - this is
fully sandboxed on your own machine, safe to leave running.

## Running with Docker (closer to the real deployment)

```bash
cp .env.example .env
docker compose up --build
docker compose exec backend python scripts/seed_servers.py
```

API is at `http://localhost:8000` (interactive docs at `/docs`). Health
check: `/api/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173` and proxies `/api` to the backend.

### Monitoring agent (per server)

```bash
cd agent
pip install -r requirements.txt
BACKEND_URL=http://<backend-host>:8000 AGENT_API_KEY=<key> SERVER_NAME=mass-01 python agent.py
```

`SERVER_NAME` must match a `name` seeded in the backend's `servers` table
(`mass-01` .. `mass-06`). For a permanent install see "Installing the
agent on all 6 servers" below.

## Setting up Microsoft login (do this once)

Login is wired up in the code (session cookie, `/api/auth/login`,
`/api/auth/me`, `/api/auth/logout`) but needs an app registration in your
university's Azure AD tenant before it'll work — that part only someone
with a university Microsoft account can do, in the browser:

1. Go to **https://portal.azure.com** → sign in with your university
   account → search **"App registrations"** → **New registration**.
   - If your university account can't create app registrations (some IT
     departments lock this down to admins), you'll need to ask IT to
     either create one for you or grant permission.
2. Name it something like "Canvas Lab Server Manager". Under **Supported
   account types**, pick **"Accounts in this organizational directory
   only"** (single tenant) so only university accounts can log in.
3. Under **Redirect URI**, choose platform **Web** and enter the backend's
   callback URL — for local dev: `http://localhost:8000/api/auth/callback`.
   For the real deployment, use `http://<lab-server-host>:8000/api/auth/callback`
   (same as `MS_REDIRECT_URI` below). Register.
4. On the app's **Overview** page, copy:
   - **Application (client) ID** → `MS_CLIENT_ID`
   - **Directory (tenant) ID** → `MS_TENANT_ID`
5. Go to **Certificates & secrets** → **New client secret** → copy the
   secret **value** (not the ID, and copy it immediately — Azure won't show
   it again) → `MS_CLIENT_SECRET`.
6. Go to **API permissions** → confirm `User.Read` (Microsoft Graph,
   delegated) is present — it's added by default. That's enough; this app
   only needs the signed-in user's name/email, not deeper Graph access.
7. Put all four values in `.env`:
   ```
   MS_CLIENT_ID=<from step 4>
   MS_CLIENT_SECRET=<from step 5>
   MS_TENANT_ID=<from step 4>
   MS_REDIRECT_URI=http://localhost:8000/api/auth/callback   # or your real host
   ```
8. Restart the backend. "Sign in with Microsoft" in the nav bar will now
   redirect to a real Microsoft login, and land back on the app logged in.

Notes on what the code does with this once configured:
- On first login, a `User` row is created automatically from the
  account's email/name — no separate signup step.
- The login state is a signed session cookie (`SESSION_SECRET_KEY` in
  `.env` signs it — set that to something random, not the default, before
  going live).
- `FRONTEND_URL` is where the browser gets redirected after login, and
  `CORS_ORIGINS` is which origin(s) the frontend is allowed to call the
  API from — both default to `http://localhost:5173` for local dev; update
  them to the real host when you deploy.

## Mapping OS usernames (needed for idle/takeover detection)

The scheduler tells "you're still using your reservation" apart from
"someone else started using it" by matching the monitoring agent's
per-process Linux username against this mapping. No admin UI yet — use the
API directly. Example, mapping the Linux account `ofek_basson` on
`mass-01` to `ofek.basson@post.runi.ac.il`:

```bash
curl -X POST http://localhost:8000/api/os-usernames \
  -H "Content-Type: application/json" \
  -d '{
    "university_email": "ofek.basson@post.runi.ac.il",
    "server_name": "mass-01",
    "os_username": "ofek_basson"
  }'
```

If that email doesn't have a `User` row yet (hasn't logged in via
Microsoft), one is created automatically so mappings can be set up ahead
of time. Repeat once per person per server they have a Linux account on.
List existing mappings for a server: `GET /api/os-usernames?server_name=mass-01`.

This endpoint has no auth check yet — fine on a trusted lab network for
now, but worth locking down before exposing it more broadly.

## Deploying to a lab server

Pick one server to host the app itself (the booking API + database) —
doesn't need to be one of the 6 GPU machines, but can be. SSH in, then:

```bash
# One-time: install Docker + Compose if not already present
curl -fsSL https://get.docker.com | sh   # or your distro's package manager

git clone https://github.com/OfekBasson/Server-Optimization.git
cd Server-Optimization
git checkout claude/canvas-lab-server-manager-dlef6l   # or main, once merged

cp .env.example .env
nano .env   # fill in SESSION_SECRET_KEY (random string), MS_* once you have
            # them from the Azure steps above, and set FRONTEND_URL /
            # MS_REDIRECT_URI to this server's real hostname instead of
            # localhost

docker compose up -d --build
docker compose exec backend python scripts/seed_servers.py
```

Backend is now running on port 8000 of that host. For the frontend:

```bash
cd frontend
npm install
npm run build
npx serve -s dist -l 5173   # or any static file server; nginx works too
```

Point people at `http://<that-host>:5173`. Login and API calls both work
across the two ports on the same host without extra config — cookies
aren't port-specific, only `CORS_ORIGINS` needs to list the frontend's
actual origin (already set to that in `.env` above).

## Installing the agent on all 6 servers

Repeat this on each of mass-01 through mass-06 (SSH details in the table
above):

```bash
ssh <you>@mass.ohadf.com -p <that server's port>

git clone https://github.com/OfekBasson/Server-Optimization.git /tmp/com
sudo mkdir -p /opt/canvas-lab-agent
sudo cp /tmp/com/agent/agent.py /opt/canvas-lab-agent/
python3 -m pip install --user -r /tmp/com/agent/requirements.txt   # or a venv

sudo cp /tmp/com/agent/canvas-lab-agent.env.example /etc/canvas-lab-agent.env
sudo nano /etc/canvas-lab-agent.env
```

Set, per machine:
```
BACKEND_URL=http://<the-app-host>:8000
AGENT_API_KEY=<same value as AGENT_API_KEY in the backend's .env>
SERVER_NAME=mass-01   # mass-02 on that machine, etc. - must match seed_servers.py
POLL_INTERVAL_SECONDS=900
```

Then install the service:

```bash
sudo cp /tmp/com/agent/canvas-lab-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now canvas-lab-agent
sudo systemctl status canvas-lab-agent   # confirm it's running
journalctl -u canvas-lab-agent -f        # watch its logs live
```

It'll now report GPU/CPU/RAM + per-process usernames every 15 minutes and
restart automatically if it crashes or the machine reboots.

## Notes / not-yet-done

- **Twilio is off by default** (`NOTIFICATIONS_ENABLED=false`) — every
  notification still gets computed and logged, just not sent as a real
  WhatsApp message, until you set that to `true` and fill in real Twilio
  credentials.
- **Reservations are never auto-released.** Idle and staleness checks only
  ever send a WhatsApp nudge (or log it); the holder always decides.
- **Statelessness**: the app should eventually hold no important state on
  local disk (all state in Postgres) so it can move between lab machines
  freely — not yet audited/enforced, flagged as follow-up work.
