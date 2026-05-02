import os
import sys
import traceback

print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    from app.main import app
    print("SUCCESS: FastAPI app imported successfully!")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
