# Canvas Lab Server Manager

Booking calendars, idle-server detection, and WhatsApp nudges for the lab's
6 servers. See the data model and workflow notes in this project's planning
discussion for the full design rationale; this README covers running it.

## Layout

- `backend/` — FastAPI + PostgreSQL API, plus the scheduled jobs that detect
  idle-but-reserved servers and long-standing reservations.
- `agent/` — monitoring daemon deployed to each of the 6 servers; reports
  GPU/CPU/RAM usage and per-process OS ownership to the backend.
- `frontend/` — React app: per-server calendar, dashboard, watch-request form.

## Running locally

```bash
cp .env.example .env   # fill in Twilio / Microsoft OAuth creds when you have them
docker compose up --build
```

Then seed the 6 servers (edit `backend/scripts/seed_servers.py` first to match
real hardware):

```bash
docker compose exec backend python scripts/seed_servers.py
```

API is at `http://localhost:8000` (docs at `/docs`). Health check: `/api/health`.

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
BACKEND_URL=http://<backend-host>:8000 AGENT_API_KEY=<key> SERVER_NAME=gpu-1 python agent.py
```

`SERVER_NAME` must match a `name` seeded in the backend's `servers` table.
For a permanent install, copy `canvas-lab-agent.env.example` to
`/etc/canvas-lab-agent.env` (filled in), the script to
`/opt/canvas-lab-agent/agent.py`, and `canvas-lab-agent.service` to
`/etc/systemd/system/`, then `systemctl enable --now canvas-lab-agent`.

## Notes / not-yet-done

- **Auth**: the Microsoft OIDC login route (`/api/auth/login`) works once
  `MS_CLIENT_ID`/`MS_CLIENT_SECRET`/`MS_TENANT_ID` are set (an app
  registration in the university's Azure AD tenant); until then it returns
  501 and the API can still be used directly with numeric `user_id`s. The
  frontend doesn't have a real login screen yet — pages currently ask for a
  user ID by hand.
- **OS username mapping**: usage attribution (idle vs. takeover detection,
  per-user analytics) depends on the `os_usernames` table mapping each
  user's Linux account(s) per server to their app `User` record. No admin
  UI for this yet — insert rows directly for now.
- **Reservations are never auto-released.** Idle and staleness checks only
  ever send a WhatsApp nudge; the holder always decides.
- **Statelessness**: the app should eventually hold no important state on
  local disk (all state in Postgres) so it can move between lab machines
  freely — not yet audited/enforced, flagged as follow-up work.
