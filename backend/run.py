import os
import sys
from pathlib import Path

# Ensure the backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from server import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4000))
    debug = app.config.get("DEBUG", True)
    print(f" * LegalEase Backend running on http://127.0.0.1:{port}")
    print(f" * API Health check: http://127.0.0.1:{port}/api/health")
    app.run(host="0.0.0.0", port=port, debug=debug)