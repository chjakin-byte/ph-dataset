import sys
import os

# Add the current directory to sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.__main__ import main

if __name__ == "__main__":
    main()
