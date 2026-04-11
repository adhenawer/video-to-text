"""Entry point: python3 -m src"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import main

main()
