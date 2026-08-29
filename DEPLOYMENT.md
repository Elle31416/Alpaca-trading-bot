# Deployment

Two things need to run, and they're not the same thing:

1. **The trading loop** — needs to execute repeatedly during market hours
   for the rest of the week.
2. **A public URL judges can open** — a status dashboard, not the bot
   itself (there's nothing to "visit" on a headless trading agent).

## Recommended path: GitHub Actions + GitHub Pages (free, no servers)

This repo is already wired for it: `.github/workflows/trading-loop.yml`
runs the strategy on a schedule and commits results to `docs/data/`, and
`docs/index.html` is a static dashboard that reads those same files. GitHub
Pages just serves the `docs/` folder — no backend to host anywhere.

**Setup (do this after pushing to GitHub):**

1. **Add your paper credentials as repo secrets.**
   Repo → Settings → Secrets and variables → Actions → New repository secret:
   - `APCA_API_KEY_ID`
   - `APCA_API_SECRET_KEY`

   Never commit these — `.gitignore` already excludes `.env`, but double
   check nothing with real keys got committed before you push.

2. **Turn on GitHub Pages.**
   Repo → Settings → Pages → Source: "Deploy from a branch" → Branch:
   `main`, folder: `/docs` → Save. GitHub gives you a URL like
   `https://<username>.github.io/<repo>/` within a minute or two — that's
   your "reachable by URL" prototype link for the submission.

3. **Test the workflow manually before trusting the schedule.**
   Repo → Actions → "Trading Loop" → "Run workflow" (this uses the
   `workflow_dispatch` trigger). Watch the log. The workflow runs
   `--dry-run` by default — leave it that way until you've confirmed auth
   and the screener work end-to-end, then edit the `run` line in the
   workflow to drop `--dry-run` and start placing real (paper) orders.

4. **Confirm the cron will actually fire.**
   The schedule is `*/15 13-19 * * 1-5` (roughly market hours in UTC).
   Scheduled workflows only run on the **default branch**, and GitHub can
   delay the first scheduled run by a few minutes — that's normal. The
   `market_is_open()` check in `scripts/run_scheduled.py` is what actually
   gates trading, not the cron precision, so a few minutes of drift doesn't
   matter.

5. **Watch the commits.** Every run that finds something to log pushes a
   commit updating `docs/data/*.json` — this is also your visible, real
   commit history for judges, which they explicitly check for.

That's it — no server, no Railway/Fly account needed, and the dashboard
updates itself as a side effect of the bot running.

## Alternative: persistent worker (Railway / Fly.io / Render)

Use this instead if you'd rather have one continuously-running process than
a periodic cron — e.g. if you extend this into something that needs to react
faster than every 15 minutes. The `Dockerfile` is already set up for it.

**Railway** (fastest to click through):
1. New Project → Deploy from GitHub repo → pick this repo.
2. Railway detects the `Dockerfile` automatically.
3. Add `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`, `APCA_API_BASE_URL` as
   environment variables in the service's Variables tab.
4. Deploy. Check the deploy logs for the first `market_is_open()` cycle.

**Fly.io / Render**: same shape — point either at this repo, let it build
the `Dockerfile`, set the three env vars, deploy as a worker/background
service (not a web service, since nothing listens on a port here).

For any of these three, you'd still want a **separate** static host for the
dashboard (e.g. GitHub Pages, Vercel, or Netlify serving `docs/`) since the
worker itself has no public URL to show judges — or extend `docs/index.html`
to fetch from wherever the worker writes its logs instead of a same-repo
JSON file.

## Either way, before judging week starts

- Confirm the paper account being traded is the **new, dedicated** one from
  the rules, not an old test account.
- Run at least one full day with `--dry-run` on, read the dashboard, and
  sanity-check the proposed structures before switching it to live paper
  orders.
- Keep an eye on the Actions tab (or worker logs) for the first real trading
  day — better to catch an auth or sizing bug on day one than find out at
  submission time the log is empty.
