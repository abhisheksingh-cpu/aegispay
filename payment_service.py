"""Pretend payment service with a fault switch (demo only: the switch is unauthenticated)."""
import asyncio
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Demo payment service")
state = {"mode": "none"}


class Fault(BaseModel):
    mode: Literal["none", "down", "slow"]


@app.get("/health")
def health():
    if state["mode"] == "down":
        raise HTTPException(status_code=503, detail="unavailable")
    return {"status": "healthy"}


@app.post("/pay")
async def pay():
    if state["mode"] == "down":
        raise HTTPException(status_code=503, detail="payment service unavailable")
    if state["mode"] == "slow":
        await asyncio.sleep(3)
    return {"status": "approved"}


@app.get("/fault")
def get_fault():
    return state


@app.post("/fault")
def set_fault(fault: Fault):
    state["mode"] = fault.mode
    return state
