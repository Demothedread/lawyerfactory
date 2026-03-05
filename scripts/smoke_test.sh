#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[smoke] backend test client..."
export LF_DISABLE_EVENTLET=1
PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" python3 - <<'PY'
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "apps", "api"))
import server  # noqa: E402

client = server.app.test_client()
resp = client.get("/api/health")
if resp.status_code != 200:
    raise SystemExit(f"/api/health status {resp.status_code}")

data = resp.get_json() or {}
if data.get("status") != "healthy":
    raise SystemExit(f"unexpected health payload: {data}")

print("[smoke] /api/health ok")
PY

echo "[smoke] frontend build..."
npm --prefix "$PROJECT_ROOT/apps/ui/react-app" run build

echo "[smoke] smoke test complete"
