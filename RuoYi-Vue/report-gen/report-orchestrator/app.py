from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from core.orchestrator import Orchestrator
from core import db
from core.logger import logger, perf_logger
from core.security import security_manager
from core.export import export_manager
import time
import uuid
import os

app = FastAPI(title="Report Orchestrator", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志和安全中间件
@app.middleware("http")
async def log_and_security_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.set_request_id(request_id)
    
    start_time = time.time()
    client_ip = security_manager.get_client_id(request)
    
    logger.info(
        f"Request started: {request.method} {request.url}",
        method=request.method,
        url=str(request.url),
        client_ip=client_ip
    )
    
    try:
        # 安全检查（跳过健康检查接口）
        if not request.url.path.startswith("/health"):
            await security_manager.check_access(request)
            await security_manager.acquire_concurrency(request)
        
        response = await call_next(request)
        duration = time.time() - start_time
        
        logger.info(
            f"Request completed: {request.method} {request.url} - {response.status_code}",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration=duration,
            client_ip=client_ip
        )
        
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url} - {str(e)}",
            method=request.method,
            url=str(request.url),
            error=str(e),
            duration=duration,
            client_ip=client_ip
        )
        raise
    finally:
        # 释放并发许可
        if not request.url.path.startswith("/health"):
            try:
                await security_manager.release_concurrency(request)
            except:
                pass  # 忽略释放错误

orc = Orchestrator()

class Step1In(BaseModel):
    project_name: str
    company_name: Optional[str] = None
    research_content: str

class TaskIn(BaseModel):
    task_id: str

@app.on_event("startup")
async def on_startup():
    await db.init_db()

@app.get("/")
async def root():
    return {
        "service": "Report Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "task_info": "/task/{task_id}",
            "step1": "/step1",
            "step2": "/step2",
            "step3": "/step3",
            "step4": "/step4",
            "step5": "/step5",
            "export": "/export",
            "download": "/download/{task_id}/{filename}",
            "upload": "/upload",
            "rerun": "/rerun",
            "rollback": "/rollback",
            "history": "/task/{task_id}/history/{step}",
            "cleanup": "/cleanup"
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/task/{task_id}")
async def get_task(task_id: str):
    t = await db.get_task(task_id)
    if not t:
        raise HTTPException(404, "not found")
    return t

@app.post("/step1")
async def step1(body: Step1In):
    perf_logger.start_timer("step1")
    logger.info(f"Starting step1 for project {body.project_name}", project_name=body.project_name, research_content=body.research_content)
    try:
        result = await orc.step1(body.project_name, body.company_name or "", body.research_content)
        perf_logger.end_timer("step1", success=True, task_id=result.get('task_id'))
        logger.info(f"Step1 completed successfully, task_id: {result.get('task_id')}", task_id=result.get('task_id'))
        return result
    except Exception as e:
        perf_logger.end_timer("step1", success=False, error=str(e))
        logger.error(f"Step1 failed: {str(e)}", error=str(e))
        raise HTTPException(400, str(e))

@app.post("/step2")
async def step2(body: TaskIn):
    perf_logger.start_timer("step2")
    logger.info(f"Starting step2 for task {body.task_id}", task_id=body.task_id)
    try:
        result = await orc.step2_outline(body.task_id)
        perf_logger.end_timer("step2", success=True, task_id=body.task_id)
        logger.info(f"Step2 completed successfully for task {body.task_id}", task_id=body.task_id)
        return result
    except Exception as e:
        perf_logger.end_timer("step2", success=False, task_id=body.task_id, error=str(e))
        logger.error(f"Step2 failed for task {body.task_id}: {str(e)}", task_id=body.task_id, error=str(e))
        raise HTTPException(400, str(e))

@app.post("/step3")
async def step3(body: TaskIn):
    perf_logger.start_timer("step3")
    logger.info(f"Starting step3 for task {body.task_id}", task_id=body.task_id)
    try:
        result = await orc.step3_content(body.task_id)
        perf_logger.end_timer("step3", success=True, task_id=body.task_id, sections_count=len(result.get('sections', [])))
        logger.info(f"Step3 completed successfully for task {body.task_id}", task_id=body.task_id, sections_count=len(result.get('sections', [])))
        return result
    except Exception as e:
        perf_logger.end_timer("step3", success=False, task_id=body.task_id, error=str(e))
        logger.error(f"Step3 failed for task {body.task_id}: {str(e)}", task_id=body.task_id, error=str(e))
        raise HTTPException(400, str(e))

@app.post("/step4")
async def step4(body: TaskIn):
    perf_logger.start_timer("step4")
    logger.info(f"Starting step4 for task {body.task_id}", task_id=body.task_id)
    try:
        result = await orc.step4_report(body.task_id)
        perf_logger.end_timer("step4", success=True, task_id=body.task_id)
        logger.info(f"Step4 completed successfully for task {body.task_id}", task_id=body.task_id)
        return result
    except Exception as e:
        perf_logger.end_timer("step4", success=False, task_id=body.task_id, error=str(e))
        logger.error(f"Step4 failed for task {body.task_id}: {str(e)}", task_id=body.task_id, error=str(e))
        raise HTTPException(400, str(e))

@app.post("/step5")
async def step5(body: TaskIn):
    perf_logger.start_timer("step5")
    logger.info(f"Starting step5 for task {body.task_id}", task_id=body.task_id)
    try:
        result = await orc.step5_finalize(body.task_id)
        perf_logger.end_timer("step5", success=True, task_id=body.task_id)
        logger.info(f"Step5 completed successfully for task {body.task_id}", task_id=body.task_id)
        return result
    except Exception as e:
        perf_logger.end_timer("step5", success=False, task_id=body.task_id, error=str(e))
        logger.error(f"Step5 failed for task {body.task_id}: {str(e)}", task_id=body.task_id, error=str(e))
        raise HTTPException(400, str(e))

# 历史管理接口
class StepHistoryIn(BaseModel):
    task_id: str
    step: str

class RerunStepIn(BaseModel):
    task_id: str
    step: str
    version: Optional[int] = None

@app.get("/task/{task_id}/history/{step}")
async def get_step_history(task_id: str, step: str):
    """获取某步骤的所有历史版本"""
    history = await db.get_step_history(task_id, step)
    if not history:
        raise HTTPException(404, "no history found")
    return {"task_id": task_id, "step": step, "history": history}

@app.post("/rerun")
async def rerun_step(body: RerunStepIn):
    """重跑指定步骤"""
    try:
        if body.step == "step2":
            return await orc.step2_outline(body.task_id)
        elif body.step == "step3":
            return await orc.step3_content(body.task_id)
        elif body.step == "step4":
            return await orc.step4_report(body.task_id)
        elif body.step == "step5":
            return await orc.step5_finalize(body.task_id)
        else:
            raise HTTPException(400, "invalid step")
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/rollback")
async def rollback_step(body: RerunStepIn):
    """回滚到指定版本"""
    if not body.version:
        raise HTTPException(400, "version required")
    try:
        success = await db.rollback_to_version(body.task_id, body.step, body.version)
        if not success:
            raise HTTPException(404, "version not found")
        return {"message": f"rolled back to version {body.version}"}
    except Exception as e:
        raise HTTPException(400, str(e))

# 导出相关接口
class ExportRequest(BaseModel):
    task_id: str
    format: str  # 'pdf' or 'docx'
    upload_to_oss: Optional[bool] = False
    oss_provider: Optional[str] = 'minio'  # 'minio' or 'aliyun'

@app.post("/export")
async def export_report(body: ExportRequest):
    """导出报告"""
    try:
        logger.info(f"Starting export for task {body.task_id}, format: {body.format}")
        
        # 获取任务数据
        task_data = await db.get_task(body.task_id)
        if not task_data:
            raise HTTPException(404, "task not found")
        
        # 根据格式导出
        if body.format.lower() == 'pdf':
            export_result = await export_manager.export_to_pdf(task_data)
        elif body.format.lower() == 'docx':
            export_result = await export_manager.export_to_word(task_data)
        else:
            raise HTTPException(400, "unsupported format. Use 'pdf' or 'docx'")
        
        if 'error' in export_result:
            raise HTTPException(500, export_result['error'])
        
        # 如果需要上传到 OSS
        if body.upload_to_oss:
            upload_result = await export_manager.upload_to_oss(
                export_result['file_path'], 
                body.oss_provider
            )
            
            if 'error' in upload_result:
                logger.warning(f"OSS upload failed: {upload_result['error']}")
                export_result['upload_error'] = upload_result['error']
            else:
                export_result['upload_result'] = upload_result
        
        logger.info(f"Export completed for task {body.task_id}")
        return export_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed for task {body.task_id}: {str(e)}")
        raise HTTPException(500, str(e))

@app.get("/download/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    """下载导出的文件"""
    try:
        file_path = export_manager.temp_dir / filename
        
        if not file_path.exists():
            raise HTTPException(404, "file not found")
        
        # 验证文件名是否包含任务ID（安全检查）
        if task_id not in filename:
            raise HTTPException(403, "access denied")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise HTTPException(500, str(e))

class UploadRequest(BaseModel):
    file_path: str
    provider: Optional[str] = 'minio'

@app.post("/upload")
async def upload_to_oss(body: UploadRequest):
    """上传文件到对象存储"""
    try:
        if not os.path.exists(body.file_path):
            raise HTTPException(404, "file not found")
        
        upload_result = await export_manager.upload_to_oss(body.file_path, body.provider)
        
        if 'error' in upload_result:
            raise HTTPException(500, upload_result['error'])
        
        return upload_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/cleanup")
async def cleanup_temp_files():
    """清理临时文件"""
    try:
        await export_manager.cleanup_temp_files()
        return {"message": "cleanup completed"}
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(500, str(e))
