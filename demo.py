"""Demo-only controls: flip the simulated payment service's fault switch from the dashboard."""
import os
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8001")


class Mode(BaseModel):
    mode: Literal["none", "down", "slow"]


@router.get("/demo/fault")
def get_fault():
    try:
        return httpx.get(f"{SERVICE_URL}/fault", timeout=1.5).json()
    except httpx.HTTPError:
        return {"mode": "unreachable"}


@router.post("/demo/fault")
def set_fault(body: Mode):
    try:
        r = httpx.post(f"{SERVICE_URL}/fault", json={"mode": body.mode}, timeout=3)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Payment service unreachable")
