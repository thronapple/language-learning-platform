import os
import sys


# Ensure the backend package root is on sys.path so that
# tests can import `app.*` when running `pytest` from this
# directory or higher-level roots on different platforms.
BACKEND_ROOT = os.path.abspath(os.path.dirname(__file__))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

