# Only needed if you deploy as a persistent worker (Railway/Fly.io/Render)
# instead of the GitHub Actions cron path — see DEPLOYMENT.md.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# --loop keeps this process alive, checking the market clock every
# --interval seconds rather than exiting after one pass (which is what the
# cron/one-shot path does instead).
CMD ["python", "scripts/run_scheduled.py", "--loop", "--interval", "900"]
