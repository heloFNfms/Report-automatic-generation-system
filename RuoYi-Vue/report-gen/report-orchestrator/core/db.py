from __future__ import annotations
import os, json, uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, func, ForeignKey, JSON, select, delete, update

MYSQL_DSN = os.getenv("MYSQL_DSN", "mysql+asyncmy://user:WZY216814wzy@localhost:3306/analyze_db?charset=utf8mb4")

class Base(DeclarativeBase):
    pass

class ReportTask(Base):
    __tablename__ = "rg_task"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_name: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    research_content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

class ReportStep(Base):
    __tablename__ = "rg_step"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("rg_task.id", ondelete="CASCADE"), index=True)
    step: Mapped[str] = mapped_column(String(32))  # outline/content/report/final
    output_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

engine = create_async_engine(MYSQL_DSN, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_task(project_name: str, company_name: Optional[str], research_content: str) -> str:
    tid = str(uuid.uuid4())
    async with SessionLocal() as s:
        s.add(ReportTask(id=tid, project_name=project_name, company_name=company_name, research_content=research_content))
        await s.commit()
    return tid

async def update_task_status(task_id: str, status: str):
    async with SessionLocal() as s:
        await s.execute(update(ReportTask).where(ReportTask.id == task_id).values(status=status))
        await s.commit()

async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    async with SessionLocal() as s:
        res = await s.execute(select(ReportTask).where(ReportTask.id == task_id))
        t = res.scalar_one_or_none()
        if not t:
            return None
        return {
            "id": t.id,
            "project_name": t.project_name,
            "company_name": t.company_name,
            "research_content": t.research_content,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }

async def save_step(task_id: str, step: str, output: Dict[str, Any]) -> int:
    async with SessionLocal() as s:
        s.add(ReportStep(task_id=task_id, step=step, output_json=output))
        await s.commit()
        # 返回最新 version 序号（按自增简化处理）
        res = await s.execute(select(ReportStep.id).where(ReportStep.task_id == task_id, ReportStep.step == step).order_by(ReportStep.id.desc()).limit(1))
        row = res.first()
        return int(row[0]) if row else 1

async def latest_step(task_id: str, step: str) -> Optional[Dict[str, Any]]:
    async with SessionLocal() as s:
        res = await s.execute(select(ReportStep).where(ReportStep.task_id == task_id, ReportStep.step == step).order_by(ReportStep.id.desc()).limit(1))
        st = res.scalar_one_or_none()
        if not st:
            return None
        return st.output_json
