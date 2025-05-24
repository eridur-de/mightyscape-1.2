
import os
import sys

HERE = os.path.dirname(__file__) or "."
# This is suggested by https://docs.python-guide.org/writing/structure/.
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
