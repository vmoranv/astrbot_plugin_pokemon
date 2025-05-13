import sys
import os

# Add the backend directory to sys.path so that modules within backend can be imported
# when running tests from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# You can add other pytest configurations or fixtures here 