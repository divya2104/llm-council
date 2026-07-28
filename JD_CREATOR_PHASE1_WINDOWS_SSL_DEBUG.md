# JD Creator — Shipping the DB/Excel Work & Windows SSL Handshake Debugging

Follow-up session to [`JD_CREATOR_PHASE1_DB_AND_BULK_UPLOAD.md`](JD_CREATOR_PHASE1_DB_AND_BULK_UPLOAD.md). Covers committing/pushing that session's work and rolling it out to the Windows contributor — which turned into an extended debugging session for a Windows-only `asyncpg`/Postgres connection failure. **As of 2026-07-28, the app runs end-to-end on the Windows laptop in local-storage fallback mode; the underlying Postgres/asyncpg TLS issue itself is still unresolved** — see "2026-07-28 update" below for what changed and what's still open.

## Committed and pushed

The Postgres migration + Excel bulk upload + wizard UI refinements from the previous session were committed and pushed to `feature/jd-creator-phase1`:

- `b0e1a71` — Move JD Creator storage to Postgres, add Excel bulk upload, and polish the wizard UI
- `63269b1` — Fix asyncpg SSL handshake hang on Windows (later found to be ineffective — see below)
- `5d5d659` — Fix Windows SSL handshake hang properly via uvicorn's loop_factory

Still nothing merged to `main` — see [`JD_CREATOR_PHASE1_UI_POLISH.md`](JD_CREATOR_PHASE1_UI_POLISH.md) for the standing merge gate.

## Rolling out to the Windows laptop

Straightforward part: `git pull`, `uv sync --python 3.12` (picked up `asyncpg`, `openpyxl`, `python-multipart` cleanly), and adding `DATABASE_URL` to `.env` (firewall was already opened to all IPs in the prior session, so no firewall step needed this time).

Then the backend failed to start on Windows with an `asyncpg` error connecting to Postgres — this took the rest of the session to diagnose.

## The SSL handshake debugging saga

**Symptom**: `backend/main.py`'s FastAPI `lifespan` startup hook (`jd_db.init_pool()` → `asyncpg.create_pool()`) failed every time, tracing down into `asyncpg`'s SSL connection setup.

### Round 1 — `OSError: [WinError 121] The semaphore timeout period has expired`

Initial theory: corporate network/proxy interference (the Windows laptop is corporate-managed, on Aditya Birla Capital's network). Ruled out methodically:
- Confirmed raw TCP connects fine (`Test-NetConnection -Port 5432` → `TcpTestSucceeded: True`) — so it wasn't a blocked port.
- Suspected corporate SSL-inspection (Zscaler) next. Found `ZEPService` ("Zscaler Endpoint Platform Service") running via `Get-Service`, even though the Zscaler Client Connector UI showed "not connected."
- **Disproved by testing**: same failure occurred on a mobile hotspot (no corporate network in the path at all), and again with Zscaler's own Zero Trust Connectivity panel explicitly showing `Service Status: OFF`. Neither network nor endpoint security software was the cause.
- **Actual root cause**: Windows' default `asyncio` event loop (`ProactorEventLoop`) has long-standing SSL-over-IOCP bugs. Confirmed via the traceback showing `asyncio\proactor_events.py`.

**Fix attempt 1** (`63269b1`): `asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())` at the top of `backend/main.py`. **This had no effect** — retried on Windows, identical failure, traceback still showed `proactor_events.py`.

**Why it didn't work**: reading `uvicorn`'s source (`.venv/.../uvicorn/loops/asyncio.py`) showed that uvicorn 0.38 selects its event loop via an explicit `loop_factory` callable passed to `asyncio.run()` — a Python 3.12-era mechanism that **completely bypasses** `asyncio.set_event_loop_policy()`. Worse, uvicorn's own `asyncio_loop_factory()` hardcodes `asyncio.ProactorEventLoop` on `win32` whenever `use_subprocess=False` (our case), regardless of any policy set beforehand.

**Fix attempt 2** (`5d5d659`, correct): define our own loop factory function and pass it directly via `uvicorn.run(app, ..., loop=_event_loop_factory)`, where the factory returns `asyncio.SelectorEventLoop()` on `win32`. Confirmed uvicorn does accept an arbitrary callable here (via `Config.get_loop_factory()` → `import_from_string()`, which returns non-string args unchanged). **This worked** — retried on Windows, traceback now showed `selector_events.py` instead of `proactor_events.py`, confirming the loop swap took effect.

### Round 2 — `ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host`

Getting past the event-loop bug surfaced a *different*, more specific failure: a genuine TCP-level reset during the TLS handshake itself (inside `asyncpg`'s `_create_ssl_connection`). This is a real network/TLS-layer problem, not a local Windows async bug.

**Not yet resolved.** To isolate whether this is `asyncpg`-specific or a broader issue, a minimal diagnostic script using only the stdlib `socket`/`ssl` modules (no `asyncpg`) was handed to the Windows contributor — it manually sends Postgres's `SSLRequest` preamble, checks for the `S` accept byte, then attempts a raw TLS handshake via `ssl.SSLContext.wrap_socket()`. **The output of this script was never received** — the session got sidetracked into an unrelated "view this chat on my phone" detour before it could be run.

## 2026-07-28 update — new blocker found and cleared, app now boots on Windows

Rolling out the latest `feature/jd-creator-phase1` commits (the wizard content-restructure work) to the same Windows laptop hit a **new, unrelated blocker** before we even got back to the Postgres question:

**Symptom**: `uv sync` failed with `error: No interpreter found for Python 3.10 in managed installations, search path, or registry` / `hint: A managed Python download is available for Python 3.10, but Python downloads are set to 'never'`.

**Cause**: the repo's `.python-version` pins `3.10`, but this laptop has no 3.10 interpreter installed, and IT policy has `uv`'s managed-Python auto-download disabled (`'never'`). Same class of environment restriction as the corporate-managed-laptop constraints noted elsewhere in this doc.

**Fix**: override the pin at the command line with whatever Python the laptop actually has (3.12, confirmed present from the prior session's rollout):
```powershell
uv sync --python 3.12
uv run --python 3.12 python -m backend.main
```
Also re-hit the pre-existing "run from project root, not from `backend/`" gotcha (`CLAUDE.md` → Common Gotchas) — running `uv run ... python -m backend.main` from inside `.\backend\` fails with `ModuleNotFoundError: No module named 'backend'` since `-m backend.main` only resolves from the repo root.

**Outcome**: with both fixed, the backend now starts cleanly on this Windows laptop:
```
INFO:     Started server process
INFO:     Waiting for application startup.
[jd_db] Could not connect to Postgres (TimeoutError()) — running in local-storage fallback mode.
INFO:     Application startup complete.
```
This confirms the `5d5d659` event-loop fix still holds (no more `WinError 121` hang), and that `jd_db.init_pool()`'s fallback-on-failure design works as intended end-to-end — Council chat and JD Creator (offline-banner mode) are both usable on Windows today, Postgres or not.

**Still open**: the Postgres connection itself did not succeed — this time it's a plain `TimeoutError` rather than Round 2's `ConnectionResetError [WinError 10054]`, which may or may not be the same underlying TLS issue (worth re-confirming rather than assuming). The stdlib SSL diagnostic script from Round 2 was still never run.

## Next session should start here

1. Run the stdlib SSL diagnostic script (recreate if needed — it's not committed to the repo, was handed over inline in chat) on the Windows laptop and get its output. Worth first confirming whether the current failure is a slow/blocked connection (`TimeoutError`, as seen 2026-07-28) or the earlier handshake reset (`ConnectionResetError`) — they may point to different causes.
2. If the stdlib handshake also fails with the same reset, it's not `asyncpg`-specific — look at TLS version/cipher negotiation between this Windows Python/OpenSSL build and Azure Postgres Flexible Server's TLS termination.
3. If the stdlib handshake succeeds while `asyncpg` still fails, the issue is something `asyncpg`-specific (e.g. ALPN, a TLS extension, or a cipher list it sends that Azure's endpoint dislikes) — worth checking `asyncpg`'s SSL context construction versus a plain `ssl.create_default_context()`.
4. Once resolved, re-verify the full DB + Excel upload flow on the Windows laptop (it was verified on macOS only, in the prior session).
