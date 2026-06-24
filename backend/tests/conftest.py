import os
import sys

# Add the parent 'backend' directory to sys.path so 'app' can be imported directly
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
