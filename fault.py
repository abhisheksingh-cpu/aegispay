"""Usage: python fault.py none|down|slow"""
import sys

import httpx

print(httpx.post("http://localhost:8001/fault", json={"mode": sys.argv[1]}).json())
