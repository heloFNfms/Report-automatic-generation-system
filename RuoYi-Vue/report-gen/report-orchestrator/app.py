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
from api.cache_api import cache_router
from core.vector_config import get_vector_manager, initialize_vector_store
import asyncio
import time
import uuid
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(title="Report Orchestrator", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含缓存API路由
app.include_router(cache_router, prefix="/api/cache", tags=["cache"])

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
vector_manager = None

class Step1In(BaseModel):
    project_name: str
    company_name: Optional[str] = None
    research_content: str

class TaskIn(BaseModel):
    task_id: str

@app.on_event("startup")
async def on_startup():
    global vector_manager
    try:
        # 初始化向量存储管理器
        vector_manager = await initialize_vector_store()
        logger.info("向量存储管理器初始化完成")
        
        # 初始化数据库
        await db.init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"组件初始化失败: {e}")

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
        return {"outline": result}
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
        perf_logger.end_timer("step3", success=True, task_id=body.task_id, sections_count=len(result) if isinstance(result, dict) else 0)
        logger.info(f"Step3 completed successfully for task {body.task_id}", task_id=body.task_id, sections_count=len(result) if isinstance(result, dict) else 0)
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
        return {"content": result}
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
        return {"final_report": result}
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
    # 步骤名称映射
    step_mapping = {
        "step1": "outline",
        "step2": "outline", 
        "step3": "content",
        "step4": "report",
        "step5": "final"
    }
    
    # 如果是数字格式的步骤名，转换为内部名称
    internal_step = step_mapping.get(step, step)
    
    history = await db.get_step_history(task_id, internal_step)
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
        # 步骤名称映射
        step_mapping = {
            "step1": "outline",
            "step2": "outline", 
            "step3": "content",
            "step4": "report",
            "step5": "final"
        }
        
        # 如果是数字格式的步骤名，转换为内部名称
        internal_step = step_mapping.get(body.step, body.step)
        
        success = await db.rollback_to_version(body.task_id, internal_step, body.version)
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

# 向量存储管理API
@app.get("/api/vector/health")
async def vector_health_check():
    """向量存储健康检查"""
    try:
        global vector_manager
        if vector_manager is None:
            vector_manager = get_vector_manager()
        
        health_status = await vector_manager.health_check()
        return health_status
    except Exception as e:
        logger.error(f"向量存储健康检查失败: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/vector/stats")
async def vector_stats():
    """获取向量存储统计信息"""
    try:
        global vector_manager
        if vector_manager is None:
            vector_manager = get_vector_manager()
        
        stats = await vector_manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"获取向量存储统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@app.post("/api/vector/backup")
async def backup_vectors(backup_path: str = "./backups"):
    """备份向量数据"""
    try:
        global vector_manager
        if vector_manager is None:
            vector_manager = get_vector_manager()
        
        success = await vector_manager.backup(backup_path)
        if success:
            return {"message": f"向量数据备份完成，路径: {backup_path}"}
        else:
            raise HTTPException(status_code=500, detail="备份失败")
    except Exception as e:
        logger.error(f"向量数据备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"备份失败: {str(e)}")

@app.delete("/api/vector/clear")
async def clear_vectors():
    """清空向量数据"""
    try:
        global vector_manager
        if vector_manager is None:
            vector_manager = get_vector_manager()
        
        store = vector_manager.get_store()
        if hasattr(store, 'clear'):
            if asyncio.iscoroutinefunction(store.clear):
                success = await store.clear()
            else:
                success = store.clear()
        else:
            success = False
        
        if success:
            return {"message": "向量数据清空完成"}
        else:
            raise HTTPException(status_code=500, detail="清空失败")
    except Exception as e:
        logger.error(f"清空向量数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")

# ============================================================================
# 兼容性路由 - 为平滑过渡提供向后兼容的API端点
# 注意：这些路由将在未来版本中被移除，请使用新的POST接口
# ============================================================================

@app.get("/step4/{task_id}")
async def step4_compat(task_id: str):
    """兼容性路由：Step4 报告生成（GET方式）
    
    警告：此接口已废弃，请使用 POST /step4 接口
    """
    logger.warning(f"Using deprecated GET /step4/{task_id} endpoint. Please migrate to POST /step4")
    
    try:
        perf_logger.start_timer("step4", task_id=task_id)
        result = await orc.step4_report(task_id)
        perf_logger.end_timer("step4", success=True, task_id=task_id)
        logger.info(f"Step4 completed successfully for task {task_id} (compat)", task_id=task_id)
        return {"report": result}
    except Exception as e:
        perf_logger.end_timer("step4", success=False, task_id=task_id, error=str(e))
        logger.error(f"Step4 failed for task {task_id} (compat): {str(e)}", task_id=task_id, error=str(e))
        raise HTTPException(400, str(e))

@app.get("/step5/{task_id}")
async def step5_compat(task_id: str):
    """兼容性路由：Step5 最终报告（GET方式）
    
    警告：此接口已废弃，请使用 POST /step5 接口
    """
    logger.warning(f"Using deprecated GET /step5/{task_id} endpoint. Please migrate to POST /step5")
    
    try:
        perf_logger.start_timer("step5", task_id=task_id)
        result = await orc.step5_finalize(task_id)
        perf_logger.end_timer("step5", success=True, task_id=task_id)
        logger.info(f"Step5 completed successfully for task {task_id} (compat)", task_id=task_id)
        return {"final_report": result}
    except Exception as e:
        perf_logger.end_timer("step5", success=False, task_id=task_id, error=str(e))
        logger.error(f"Step5 failed for task {task_id} (compat): {str(e)}", task_id=task_id, error=str(e))
        raise HTTPException(400, str(e))

@app.get("/api/compatibility/info")
async def compatibility_info():
    """获取兼容性API信息"""
    return {
        "deprecated_endpoints": [
            {
                "endpoint": "GET /step4/{task_id}",
                "replacement": "POST /step4",
                "deprecation_date": "2024-01-01",
                "removal_date": "2024-06-01",
                "status": "deprecated"
            },
            {
                "endpoint": "GET /step5/{task_id}",
                "replacement": "POST /step5",
                "deprecation_date": "2024-01-01",
                "removal_date": "2024-06-01",
                "status": "deprecated"
            }
        ],
        "migration_guide": {
            "step4": {
                "old": "GET /step4/{task_id}",
                "new": "POST /step4 with body: {\"task_id\": \"...\"}" 
            },
            "step5": {
                "old": "GET /step5/{task_id}",
                "new": "POST /step5 with body: {\"task_id\": \"...\"}"
            }
        },
        "notice": "兼容性端点将在2024年6月1日后移除，请尽快迁移到新的POST接口"
    }
