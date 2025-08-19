from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import os
import asyncio
from orchestrator.core import ReportOrchestrator


app = FastAPI(title="report-orchestrator")


# init
MCP_BASE = os.getenv('MCP_BASE', 'http://localhost:8000')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE = os.getenv('DEEPSEEK_BASE', 'https://api.deepseek.com')


orch = ReportOrchestrator(mcp_base=MCP_BASE, deepseek_base=DEEPSEEK_BASE, deepseek_key=DEEPSEEK_API_KEY)


class Step1In(BaseModel):
    project_name: str
    company_name: Optional[str] = None
    research_content: str


class StepRequest(BaseModel):
    task_id: str


@app.post('/step1')
async def step1(self, data: Step1In):
    task = await orch.step1_create(data.project_name, data.company_name, data.research_content)
    return task


@app.post('/step2')
async def step2(self, req: StepRequest):
    res = await orch.step2_summary(req.task_id)
    return res


@app.post('/step3')
async def step3(req: StepRequest):
    res = await orch.step3_outline(req.task_id)
    return res


@app.post('/step4')
async def step4(self, req: StepRequest):
    res = await orch.step4_content(req.task_id)
    return res


@app.post('/step5')
async def step5(self, req: StepRequest):
    res = await orch.step5_assemble(req.task_id)
    return res


@app.get('/health')
async def health(self):
    return {"status":"ok"}
