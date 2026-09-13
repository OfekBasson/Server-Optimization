# Canvas Lab Server Manager

Booking calendars, idle-server detection, and WhatsApp nudges for the lab's
servers. See the data model and workflow notes in this project's planning
discussion for the full design rationale; this README covers running it.

## Run it locally for review (no lab server, no sudo needed)

If you don't have server access yet (e.g. you're waiting on your
supervisor to approve installing this on a lab machine), you can run the
**entire app** — same code, same Docker setup that will eventually go on
the lab server — on any regular computer (your own laptop, or your
supervisor's, Mac/Windows/Linux). It only touches that computer; it never
connects to any lab server, and no `sudo`/admin rights are needed beyond
the one-time install of Docker Desktop itself.

**One-time setup:**

1. Install **Docker Desktop**: https://www.docker.com/products/docker-desktop
   (just click through the normal installer — no special permissions
   needed beyond what any app install needs).
2. **Open the Docker Desktop app itself** (double-click it like any
   other app) and wait until it says it's running (a whale icon appears
   in the menu bar / system tray). This step is easy to miss — the
   `docker` command doesn't work in the terminal until the app has been
   opened at least once. If you already had a terminal open, close it
   and open a new one after this step so it picks up the change.
3. Install **Git**, or skip it and just download the code as a ZIP
   instead: on the repo's GitHub page, green **Code** button → **Download
   ZIP** → unzip it, then open a terminal in that folder (skip the
   `git clone`/`git checkout` lines below if you did this).

**Then, in a terminal, inside the project folder** (copy each line
separately rather than pasting the whole block at once, some terminals
mishandle multi-line pastes):

```bash
git clone https://github.com/OfekBasson/Server-Optimization.git
cd Server-Optimization
git checkout main
```

```bash
cp .env.example .env
docker compose up --build
```

Leave that running — it downloads and starts everything (database +
backend). The first run takes a few minutes; after that it's fast. In a
**second terminal**, in the same folder:

```bash
docker compose exec backend python scripts/seed_servers.py
docker compose exec backend python scripts/seed_admin.py "Your Name" you@example.com YourPassword
```

Optional, adds a couple of fake users and example bookings so the app
isn't empty:

```bash
docker compose exec backend python scripts/seed_demo_data.py
```

Then:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in a browser — that's the real app,
running fully on this computer. Log in with the email/password you gave
`seed_admin.py` (top-right of the page) to see the **Admin** page too. No
messages get sent anywhere (Twilio is off by default), and nothing here
can reach or affect the actual lab servers — it's completely sandboxed.

**To stop:** `Ctrl+C` both terminals, then `docker compose down` (add
`-v` on the end if you also want to wipe the local database and start
fresh next time).

This is exactly what will run on the lab server once it's approved — the
only things that change for the real deployment are *where* it runs and
that it gets a public web address (see "Going live on the web" below).

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
git checkout main
```

Backend, pointed at a local SQLite file instead of Postgres:

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="sqlite:///$(pwd)/demo.db"
python3 scripts/init_db.py
python3 scripts/seed_servers.py
python3 scripts/seed_admin.py "Your Name" you@post.runi.ac.il
```

`seed_admin.py` prompts for a password interactively. Optional, adds a
couple of fake users and example bookings:

```bash
python3 scripts/seed_demo_data.py
```

Then start the backend (leave it running):

```bash
uvicorn app.main:app --port 8000
```

In a second terminal:

```bash
cd Server-Optimization/frontend
npm install
npm run dev
```

Open **http://localhost:5173**. You'll see the real dashboard and
calendars, mass-01 shown as reserved by the demo data — no login needed to
look around or book something (see "Identifying yourself" below). Log in
with the email/password you gave `seed_admin.py` (top right) to reach the
**Admin** page.

To stop: `Ctrl+C` both terminals. Nothing here touches the real lab
servers or sends any notifications (Twilio is off by default) - this is
fully sandboxed on your own machine, safe to leave running.

## Running with Docker (closer to the real deployment)

```bash
cp .env.example .env
docker compose up --build
docker compose exec backend python scripts/seed_servers.py
docker compose exec backend python scripts/seed_admin.py "Your Name" you@post.runi.ac.il YourPassword
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

## Identifying yourself (regular users vs. admins)

Two different trust levels:

- **Regular users never log in at all.** There's no session, no cookie,
  nothing persistent. Instead, the moment you actually do something that
  needs to know who you are — booking a server or creating a "notify me"
  watch request — a small "Who's booking this?" / "Who is this request
  for?" dialog pops up with a dropdown of everyone the admin has added.
  Pick your name, confirm, done. This only makes sense on a trusted
  internal network, not exposed publicly, since anyone can pick anyone's
  name and there's no password check for it.
- **Admins log in for real**, with a university email + password, via the
  form in the top-right of the nav bar. That's a real (if lightweight)
  session cookie, gating the **Admin** page - adding users, promoting
  others to admin, setting/changing admin passwords. Regular users never
  have a password at all; only admins do.

**Adding users** is admin-only, through the **Admin** page or directly via
`POST /api/admin/users`. The very first admin has to be created once from
the command line, since the admin panel itself requires an existing admin
to log into:

```bash
python scripts/seed_admin.py "Ofek Basson" ofek.basson@post.runi.ac.il
# prompts for a password interactively - or pass it as a 3rd argument for
# non-interactive use, e.g. `docker compose exec backend python scripts/seed_admin.py "Ofek Basson" ofek.basson@post.runi.ac.il YourPassword`
```

That admin can then add everyone else from the Admin page, and promote
others to admin (which prompts for a password for them too - only admins
have one). Running the script again on an existing email just re-promotes
and resets that user's password instead of duplicating them.

`SESSION_SECRET_KEY` in `.env` signs the session cookie — set it to
something random before going live, not the default. `CORS_ORIGINS` is
which origin(s) the frontend is allowed to call the API from — defaults to
`http://localhost:5173` for local dev; update it to the real host when you
deploy.

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

If that email doesn't have a `User` row yet (the admin hasn't added them),
one is created automatically (as a non-admin) so mappings can be set up
ahead of time. Repeat once per person per server they have a Linux
account on.
List existing mappings for a server: `GET /api/os-usernames?server_name=mass-01`.

This endpoint has no auth check yet — fine on a trusted lab network for
now, but worth locking down before exposing it more broadly.

## Going live on the web (free address, auto-deploy on push)

This runs the app on a real HTTPS URL on `mass.ohadf.com` (the lab
server), and redeploys automatically every time `main` is pushed. Pieces
involved: **Caddy** (local reverse proxy in front of the app),
**Tailscale Funnel** (free — gives a public HTTPS URL and does the TLS,
with **no need to open any inbound ports** on the lab network, since we
can't be sure 80/443 are reachable from outside), and a **GitHub
Actions** workflow that SSHes in and redeploys.

### 1. One-time setup on the server

SSH in as `ofek_basson@mass.ohadf.com -p 1204`, then:

Install Docker if it isn't already there:

```bash
curl -fsSL https://get.docker.com | sh
```

```bash
git clone https://github.com/OfekBasson/Server-Optimization.git
cd Server-Optimization
git checkout main

cp .env.prod.example .env
nano .env
```

In `.env`, generate random values for `POSTGRES_PASSWORD`,
`SESSION_SECRET_KEY`, and `AGENT_API_KEY` with `openssl rand -hex 32`
(run it once per value). Leave `DOMAIN` blank for now — that's step 2.

```bash
cd frontend && npm ci && npm run build && cd ..
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_servers.py
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_admin.py "Ofek Basson" ofek.basson@post.runi.ac.il
```

This starts Caddy listening on `127.0.0.1:8080` only — not yet reachable
from outside the server itself. Step 2 exposes it publicly.

### 2. Turn on Tailscale Funnel (the public HTTPS address)

Still on the server:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --hostname=canvaslab
```

That prints a login link — open it in your browser and sign in (free,
works with a Google/GitHub/Microsoft account). Then, one time only, in
the [Tailscale admin console](https://login.tailscale.com/admin/machines):
click the `canvaslab` machine → **enable HTTPS certificates** for the
tailnet if prompted (Settings → click "enable" if it's not already on).

Then turn the funnel on:

```bash
sudo tailscale funnel --bg 8080
```

It'll print the public URL — something like
`https://canvaslab.<your-tailnet-name>.ts.net`. That's the site's real
address; visit it from your phone on cellular data (not the lab wifi) to
confirm it's actually reachable from outside. Put that exact URL as
`DOMAIN=` in the server's `.env` file (no `https://` prefix, just the
hostname), then restart the backend so `CORS_ORIGINS` picks it up:

```bash
nano .env
```

Set `DOMAIN=canvaslab.<your-tailnet-name>.ts.net` in that file, then:

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 3. Wire up auto-deploy on push

A dedicated SSH key for this (not your personal one) — I generated one and
sent it to you as a file. Add its **public** half to
`~/.ssh/authorized_keys` for `ofek_basson` on the server:

```bash
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILffG2kQDwi08NaH+pRHn2HPDR2QtjwVAMB7W+Cthj/8 canvas-lab-deploy" >> ~/.ssh/authorized_keys
```

Then, in the GitHub repo → **Settings → Secrets and variables → Actions**,
add these secrets:

| Secret | Value |
|---|---|
| `DEPLOY_HOST` | `mass.ohadf.com` |
| `DEPLOY_PORT` | `1204` |
| `DEPLOY_USER` | `ofek_basson` |
| `DEPLOY_SSH_KEY` | the **private** key (the file sent to you earlier — paste its full contents, including the `BEGIN`/`END` lines) |
| `DEPLOY_PATH` | `/home/ofek_basson/Server-Optimization` (wherever you cloned it in step 1 — adjust if different) |

`.github/workflows/deploy.yml` is already in the repo — once those secrets
exist, every push to `main` SSHes in, pulls, rebuilds the frontend,
`docker compose -f docker-compose.prod.yml up -d --build`, and re-runs
`init_db.py` (safe to run repeatedly — only creates tables that don't
exist yet, never touches existing data). Tailscale Funnel itself keeps
running in the background (`sudo tailscale funnel --bg`), so redeploys
don't disturb it. You can also trigger the workflow manually from the
repo's **Actions** tab (`workflow_dispatch`).

## Installing the agent on all 6 servers

Repeat this on each of mass-01 through mass-06 (SSH details in the table
above):

```bash
ssh <you>@mass.ohadf.com -p <that server's port>

git clone https://github.com/OfekBasson/Server-Optimization.git /tmp/com
sudo mkdir -p /opt/canvas-lab-agent
sudo cp /tmp/com/agent/agent.py /opt/canvas-lab-agent/
python3 -m pip install --user -r /tmp/com/agent/requirements.txt

sudo cp /tmp/com/agent/canvas-lab-agent.env.example /etc/canvas-lab-agent.env
sudo nano /etc/canvas-lab-agent.env
```

(use a venv instead of `--user` if you prefer)

Set, per machine — `SERVER_NAME` must match the name `seed_servers.py`
gave this machine (`mass-01`, `mass-02`, etc.):
```
BACKEND_URL=http://<the-app-host>:8000
AGENT_API_KEY=<same value as AGENT_API_KEY in the backend's .env>
SERVER_NAME=mass-01
POLL_INTERVAL_SECONDS=900
```

Then install the service:

```bash
sudo cp /tmp/com/agent/canvas-lab-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now canvas-lab-agent
```

Confirm it's running, and watch its logs live:

```bash
sudo systemctl status canvas-lab-agent
journalctl -u canvas-lab-agent -f
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
