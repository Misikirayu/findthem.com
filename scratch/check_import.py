import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    from modules.analyzer import analyze_stream
    print("SUCCESS: analyze_stream imported successfully")
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
except NameError as e:
    print(f"NAME ERROR: {e}")
except Exception as e:
    print(f"OTHER ERROR: {e}")
