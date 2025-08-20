from __future__ import annotations
import os, json, uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, func, ForeignKey, JSON, select, delete, update

MYSQL_DSN = os.getenv("MYSQL_DSN", "mysql+asyncmy://root:WZY216814wzy@localhost:3306/analyze_db?charset=utf8mb4")

class Base(DeclarativeBase):
    pass

class ReportTask(Base):
    __tablename__ = "report_task"
    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    topic: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(1), default="0")
    current_step: Mapped[str] = mapped_column(String(20), default="step1")
    progress: Mapped[int] = mapped_column(default=0)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    config_params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    orchestrator_task_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    remark: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

class ReportStep(Base):
    __tablename__ = "report_step_history"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), ForeignKey("report_task.task_id", ondelete="CASCADE"), index=True)
    step: Mapped[str] = mapped_column(String(20))  # outline/content/report/final
    version: Mapped[int] = mapped_column(default=1)
    output_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    status: Mapped[str] = mapped_column(String(1), default="1")
    error_message: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

engine = create_async_engine(MYSQL_DSN, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_task(project_name: str, company_name: Optional[str], research_content: str) -> str:
    tid = str(uuid.uuid4())
    async with SessionLocal() as s:
        config_params = {
            "project_name": project_name,
            "company_name": company_name or "",
            "research_content": research_content
        }
        task = ReportTask(
            task_id=tid,
            title=f"{project_name} - {research_content}",
            description=research_content,
            topic=research_content,
            status="0",
            current_step="step1",
            progress=0,
            user_id=1,
            user_name="system",
            config_params=json.dumps(config_params, ensure_ascii=False),
            start_time=datetime.now()
        )
        s.add(task)
        await s.commit()
    return tid

async def update_task_status(task_id: str, status: str):
    async with SessionLocal() as s:
        # 映射编排器状态到Java后端状态
        status_mapping = {
            "created": "0",
            "processing": "1", 
            "step1_done": "1",
            "step2_done": "1",
            "step3_done": "1",
            "step4_done": "1",
            "step5_done": "2",
            "completed": "2",
            "failed": "3"
        }
        
        # 映射当前步骤和进度
        step_mapping = {
            "step1_done": ("step2", 20),
            "step2_done": ("step3", 40),
            "step3_done": ("step4", 60),
            "step4_done": ("step5", 80),
            "step5_done": ("step5", 100)
        }
        
        update_values = {
            "status": status_mapping.get(status, "0"),
            "update_time": datetime.now()
        }
        
        if status in step_mapping:
            current_step, progress = step_mapping[status]
            update_values["current_step"] = current_step
            update_values["progress"] = progress
            
        if status == "completed" or status == "step5_done":
            update_values["end_time"] = datetime.now()
        
        await s.execute(update(ReportTask).where(ReportTask.task_id == task_id).values(**update_values))
        await s.commit()

async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    async with SessionLocal() as s:
        res = await s.execute(select(ReportTask).where(ReportTask.task_id == task_id))
        t = res.scalar_one_or_none()
        if not t:
            return None
        
        # 从config_params中解析项目信息
        config = {}
        if t.config_params:
            try:
                config = json.loads(t.config_params)
            except:
                pass
        
        # 映射Java后端状态到编排器状态
        status_mapping = {
            "0": "created",
            "1": "processing",
            "2": "completed",
            "3": "failed"
        }
        
        return {
            "id": t.task_id,
            "project_name": config.get("project_name", ""),
            "company_name": config.get("company_name", ""),
            "research_content": config.get("research_content", t.description or ""),
            "status": status_mapping.get(t.status, "created"),
            "created_at": t.create_time.isoformat() if t.create_time else None,
            "updated_at": t.update_time.isoformat() if t.update_time else None,
        }

async def save_step(task_id: str, step: str, output: Dict[str, Any]) -> int:
    async with SessionLocal() as s:
        # 查找该步骤的最新版本号
        res = await s.execute(
            select(ReportStep.version)
            .where(ReportStep.task_id == task_id, ReportStep.step == step)
            .order_by(ReportStep.version.desc())
            .limit(1)
        )
        latest_version = res.scalar_one_or_none()
        new_version = (latest_version or 0) + 1
        
        # 创建新的历史记录
        step_history = ReportStep(
            task_id=task_id,
            step=step,
            version=new_version,
            output_json=json.dumps(output, ensure_ascii=False),
            execution_time=None,  # 暂时设为None避免格式问题
            status="1",  # 成功状态
        )
        s.add(step_history)
        await s.commit()
        return new_version

async def save_step_output(task_id: str, step: str, output: Dict[str, Any]):
    async with SessionLocal() as s:
        # 查找该步骤的最新版本号
        res = await s.execute(
            select(ReportStep.version)
            .where(ReportStep.task_id == task_id, ReportStep.step == step)
            .order_by(ReportStep.version.desc())
            .limit(1)
        )
        latest_version = res.scalar_one_or_none()
        new_version = (latest_version or 0) + 1
        
        # 创建新的历史记录
        step_history = ReportStep(
            task_id=task_id,
            step=step,
            version=new_version,
            output_json=json.dumps(output, ensure_ascii=False),
            execution_time=None,  # 暂时设为None避免格式问题
            status="1",  # 成功状态
        )
        s.add(step_history)
        await s.commit()

async def latest_step(task_id: str, step: str) -> Optional[Dict[str, Any]]:
    async with SessionLocal() as s:
        res = await s.execute(
            select(ReportStep)
            .where(ReportStep.task_id == task_id, ReportStep.step == step)
            .order_by(ReportStep.version.desc())
            .limit(1)
        )
        step_record = res.scalar_one_or_none()
        if not step_record:
            return None
        
        try:
            return json.loads(step_record.output_json)
        except:
            return None

async def get_step_history(task_id: str, step: str) -> List[Dict[str, Any]]:
    """获取某步骤的所有历史版本"""
    async with SessionLocal() as s:
        res = await s.execute(
            select(ReportStep)
            .where(ReportStep.task_id == task_id, ReportStep.step == step)
            .order_by(ReportStep.version.desc())
        )
        steps = res.scalars().all()
        
        history = []
        for step_record in steps:
            try:
                output = json.loads(step_record.output_json)
            except:
                output = {}
            
            history.append({
                "id": step_record.id,
                "version": step_record.version,
                "output": output,
                "created_at": step_record.create_time.isoformat() if step_record.create_time else None,
                "execution_time": step_record.execution_time,
                "status": step_record.status,
                "error_message": step_record.error_message
            })
        
        return history

async def rollback_to_version(task_id: str, step: str, version: int) -> bool:
    """回滚到指定版本（将指定版本的数据复制为新的最新版本）"""
    async with SessionLocal() as s:
        # 查找指定版本的记录
        res = await s.execute(
            select(ReportStep)
            .where(ReportStep.task_id == task_id, ReportStep.step == step, ReportStep.version == version)
        )
        target_record = res.scalar_one_or_none()
        
        if not target_record:
            return False
        
        # 查找最新版本号
        latest_res = await s.execute(
            select(ReportStep.version)
            .where(ReportStep.task_id == task_id, ReportStep.step == step)
            .order_by(ReportStep.version.desc())
            .limit(1)
        )
        latest_version = latest_res.scalar_one_or_none()
        new_version = (latest_version or 0) + 1
        
        # 创建新版本作为回滚结果
        new_record = ReportStep(
            task_id=task_id,
            step=step,
            version=new_version,
            output_json=target_record.output_json,
            execution_time=None,  # 暂时设为None避免格式问题
            status="1",  # 成功状态
        )
        s.add(new_record)
        await s.commit()
        
        return True
