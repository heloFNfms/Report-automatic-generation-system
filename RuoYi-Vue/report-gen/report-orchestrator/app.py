from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.orchestrator import Orchestrator

app = FastAPI(title="report-orchestrator (new flow)")
orc = Orchestrator()

class Step1In(BaseModel):
    project_name: str
    company_name: Optional[str] = None
    research_content: str

class TaskIn(BaseModel):
    task_id: str

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/step1")
async def step1(body: Step1In):
    return await orc.step1(body.project_name, body.company_name or "", body.research_content)

@app.post("/step2")
async def step2(body: TaskIn):
    try:
        return await orc.step2_outline(body.task_id)
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/step3")
async def step3(body: TaskIn):
    try:
        return await orc.step3_content(body.task_id)
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/step4")
async def step4(body: TaskIn):
    try:
        return await orc.step4_report(body.task_id)
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/step5")
async def step5(body: TaskIn):
    try:
        return await orc.step5_finalize(body.task_id)
    except Exception as e:
        raise HTTPException(400, str(e))