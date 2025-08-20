package com.ruoyi.web.controller.system;

import java.util.List;
import javax.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.system.domain.ReportTask;
import com.ruoyi.system.service.IReportService;
import com.ruoyi.system.validation.ValidStep;
import com.ruoyi.system.validation.ValidTaskId;

import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Min;

/**
 * 报告生成Controller
 * 
 * @author ruoyi
 * @date 2024-01-01
 */
@RestController
@RequestMapping("/system/report")
public class ReportController extends BaseController {
    @Autowired
    private IReportService reportService;

    /**
     * 查询报告任务列表
     */
    @PreAuthorize("@ss.hasPermi('system:report:list')")
    @GetMapping("/list")
    public TableDataInfo list(ReportTask reportTask) {
        startPage();
        List<ReportTask> list = reportService.selectReportTaskList(reportTask);
        return getDataTable(list);
    }

    /**
     * 导出报告任务列表
     */
    @PreAuthorize("@ss.hasPermi('system:report:export')")
    @Log(title = "报告任务", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(HttpServletResponse response, ReportTask reportTask) {
        List<ReportTask> list = reportService.selectReportTaskList(reportTask);
        ExcelUtil<ReportTask> util = new ExcelUtil<ReportTask>(ReportTask.class);
        util.exportExcel(response, list, "报告任务数据");
    }

    /**
     * 获取报告任务详细信息
     */
    @PreAuthorize("@ss.hasPermi('system:report:query')")
    @GetMapping(value = "/{taskId}")
    public AjaxResult getInfo(@PathVariable("taskId") String taskId) {
        return success(reportService.selectReportTaskByTaskId(taskId));
    }

    /**
     * 新增报告任务
     */
    @PreAuthorize("@ss.hasPermi('system:report:add')")
    @Log(title = "报告任务", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@Validated @RequestBody ReportTask reportTask) {
        return toAjax(reportService.insertReportTask(reportTask));
    }

    /**
     * 修改报告任务
     */
    @PreAuthorize("@ss.hasPermi('system:report:edit')")
    @Log(title = "报告任务", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@Validated @RequestBody ReportTask reportTask) {
        return toAjax(reportService.updateReportTask(reportTask));
    }

    /**
     * 删除报告任务
     */
    @PreAuthorize("@ss.hasPermi('system:report:remove')")
    @Log(title = "报告任务", businessType = BusinessType.DELETE)
    @DeleteMapping("/{taskIds}")
    public AjaxResult remove(@PathVariable String[] taskIds) {
        return toAjax(reportService.deleteReportTaskByTaskIds(taskIds));
    }

    /**
     * 开始生成报告
     */
    @PreAuthorize("@ss.hasPermi('system:report:generate')")
    @Log(title = "生成报告", businessType = BusinessType.OTHER)
    @PostMapping("/generate")
    public AjaxResult generateReport(@RequestBody ReportTask reportTask) {
        try {
            String taskId = reportService.startReportGeneration(reportTask);
            return AjaxResult.success("报告生成任务已启动", taskId);
        } catch (Exception e) {
            return error("启动报告生成失败: " + e.getMessage());
        }
    }

    /**
     * 获取报告生成状态
     */
    @PreAuthorize("@ss.hasPermi('system:report:query')")
    @GetMapping("/status/{taskId}")
    public AjaxResult getReportStatus(@PathVariable String taskId) {
        try {
            return success(reportService.getReportStatus(taskId));
        } catch (Exception e) {
            return error("获取报告状态失败: " + e.getMessage());
        }
    }

    /**
     * 获取报告内容
     */
    @PreAuthorize("@ss.hasPermi('system:report:query')")
    @GetMapping("/content/{taskId}")
    public AjaxResult getReportContent(@PathVariable String taskId) {
        try {
            return success(reportService.getReportContent(taskId));
        } catch (Exception e) {
            return error("获取报告内容失败: " + e.getMessage());
        }
    }

    /**
     * 重新执行报告步骤
     */
    @PreAuthorize("@ss.hasPermi('system:report:generate')")
    @Log(title = "重新执行报告步骤", businessType = BusinessType.OTHER)
    @PostMapping("/rerun/{taskId}/{step}")
    public AjaxResult rerunStep(@ValidTaskId @PathVariable String taskId, @ValidStep @PathVariable String step) {
        try {
            reportService.rerunReportStep(taskId, step);
            return success("步骤重新执行已启动");
        } catch (Exception e) {
            return error("重新执行步骤失败: " + e.getMessage());
        }
    }

    /**
     * 回滚报告到指定版本
     */
    @PreAuthorize("@ss.hasPermi('system:report:generate')")
    @Log(title = "回滚报告版本", businessType = BusinessType.OTHER)
    @PostMapping("/rollback/{taskId}/{step}/{version}")
    public AjaxResult rollbackStep(@ValidTaskId @PathVariable String taskId, @ValidStep @PathVariable String step,
            @Min(value = 1, message = "版本号必须大于0") @PathVariable Integer version) {
        try {
            reportService.rollbackReportStep(taskId, step, version);
            return success("报告版本回滚成功");
        } catch (Exception e) {
            return error("回滚报告版本失败: " + e.getMessage());
        }
    }

    /**
     * 导出报告为 PDF 或 Word
     */
    @PreAuthorize("@ss.hasPermi('system:report:export')")
    @Log(title = "导出报告", businessType = BusinessType.EXPORT)
    @PostMapping("/export/{taskId}")
    public AjaxResult exportReport(@ValidTaskId @PathVariable String taskId,
            @Valid @RequestBody ExportRequest exportRequest) {
        try {
            String downloadUrl = reportService.exportReport(taskId, exportRequest.getFormat(),
                    exportRequest.isUploadToOss());
            return AjaxResult.success("报告导出成功", downloadUrl);
        } catch (Exception e) {
            return error("导出报告失败: " + e.getMessage());
        }
    }

    /**
     * 下载导出的报告文件
     */
    @PreAuthorize("@ss.hasPermi('system:report:export')")
    @GetMapping("/download/{taskId}/{filename}")
    public void downloadReport(@PathVariable String taskId, @PathVariable String filename,
            HttpServletResponse response) {
        try {
            reportService.downloadReport(taskId, filename, response);
        } catch (Exception e) {
            // 记录错误日志
            System.err.println("下载报告文件失败: " + e.getMessage());
        }
    }

    /**
     * 清理临时文件
     */
    @PreAuthorize("@ss.hasPermi('system:report:generate')")
    @Log(title = "清理临时文件", businessType = BusinessType.DELETE)
    @DeleteMapping("/cleanup/{taskId}")
    public AjaxResult cleanupFiles(@PathVariable String taskId) {
        try {
            boolean success = reportService.cleanupFiles(taskId);
            return success ? success("清理成功") : error("清理失败");
        } catch (Exception e) {
            return error("清理失败: " + e.getMessage());
        }
    }

    // ==================== 分步骤接口 ====================

    /**
     * 执行步骤1：保存主题到数据库
     */
    @PreAuthorize("@ss.hasPermi('system:report:generate')")
    @Log(title = "执行报告步骤1", businessType = BusinessType.OTHER)
    @PostMapping("/step1")
    public AjaxResult executeStep1(@Valid @RequestBody ReportTask reportTask) {
        try {
            String taskId = reportService.executeStep1(reportTask);
            return AjaxResult.success("步骤1执行成功", taskId);
        } catch (Exception e) {
            return error("步骤1执行失败: " + e.getMessage());
        }
    }

    /**
     * 执行步骤2：生成研究大纲
     */
    @PreAuthorize("@ss.hasPermi('system:report:generate')")
    @Log(title = "执行报告步骤2", businessType = BusinessType.OTHER)
    @PostMapping("/step2/{taskId}")
    public AjaxResult executeStep2(@ValidTaskId @PathVariable String taskId) {
        try {
            Object result = reportService.executeStep2(taskId);
            return AjaxResult.success("步骤2执行成功", result);
        } catch (Exception e) {
            return error("步骤2执行失败: " + e.getMessage());
        }
    }

    /**
     * 执行步骤3：检索并生成章节内容
     */
    @PreAuthorize("@ss.hasPermi('system:report:generate')")
    @Log(title = "执行报告步骤3", businessType = BusinessType.OTHER)
    @PostMapping("/step3/{taskId}")
    public AjaxResult executeStep3(@ValidTaskId @PathVariable String taskId) {
        try {
            Object result = reportService.executeStep3(taskId);
            return AjaxResult.success("步骤3执行成功", result);
        } catch (Exception e) {
            return error("步骤3执行失败: " + e.getMessage());
        }
    }

    /**
     * 执行步骤4：组装润色报告
     */
    @PreAuthorize("@ss.hasPermi('system:report:generate')")
    @Log(title = "执行报告步骤4", businessType = BusinessType.OTHER)
    @PostMapping("/step4/{taskId}")
    public AjaxResult executeStep4(@ValidTaskId @PathVariable String taskId) {
        try {
            Object result = reportService.executeStep4(taskId);
            return AjaxResult.success("步骤4执行成功", result);
        } catch (Exception e) {
            return error("步骤4执行失败: " + e.getMessage());
        }
    }

    /**
     * 执行步骤5：生成摘要和关键词
     */
    @PreAuthorize("@ss.hasPermi('system:report:generate')")
    @Log(title = "执行报告步骤5", businessType = BusinessType.OTHER)
    @PostMapping("/step5/{taskId}")
    public AjaxResult executeStep5(@ValidTaskId @PathVariable String taskId) {
        try {
            Object result = reportService.executeStep5(taskId);
            return AjaxResult.success("步骤5执行成功", result);
        } catch (Exception e) {
            return error("步骤5执行失败: " + e.getMessage());
        }
    }

    /**
     * 获取指定步骤的结果
     */
    @PreAuthorize("@ss.hasPermi('system:report:query')")
    @GetMapping("/step/{taskId}/{step}")
    public AjaxResult getStepResult(@ValidTaskId @PathVariable String taskId, @ValidStep @PathVariable String step) {
        try {
            Object result = reportService.getStepResult(taskId, step);
            return AjaxResult.success("获取步骤结果成功", result);
        } catch (Exception e) {
            return error("获取步骤结果失败: " + e.getMessage());
        }
    }

    /**
     * 获取指定步骤的历史版本
     */
    @PreAuthorize("@ss.hasPermi('system:report:query')")
    @GetMapping("/step/{taskId}/{step}/history")
    public AjaxResult getStepHistory(@PathVariable String taskId, @PathVariable String step) {
        try {
            Object result = reportService.getStepHistory(taskId, step);
            return AjaxResult.success("获取步骤历史成功", result);
        } catch (Exception e) {
            return error("获取步骤历史失败: " + e.getMessage());
        }
    }

    // ==================== 报告发布和归档功能接口 ====================

    /**
     * 发布报告
     */
    @PreAuthorize("@ss.hasPermi('system:report:publish')")
    @Log(title = "发布报告", businessType = BusinessType.UPDATE)
    @PostMapping("/publish/{taskId}")
    public AjaxResult publishReport(@ValidTaskId @PathVariable String taskId) {
        try {
            boolean result = reportService.publishReport(taskId);
            return result ? success("报告发布成功") : error("报告发布失败");
        } catch (Exception e) {
            return error("发布报告失败: " + e.getMessage());
        }
    }

    /**
     * 归档报告
     */
    @PreAuthorize("@ss.hasPermi('system:report:archive')")
    @Log(title = "归档报告", businessType = BusinessType.UPDATE)
    @PostMapping("/archive/{taskId}")
    public AjaxResult archiveReport(@ValidTaskId @PathVariable String taskId) {
        try {
            boolean result = reportService.archiveReport(taskId);
            return result ? success("报告归档成功") : error("报告归档失败");
        } catch (Exception e) {
            return error("归档报告失败: " + e.getMessage());
        }
    }

    /**
     * 批量归档报告
     */
    @PreAuthorize("@ss.hasPermi('system:report:archive')")
    @Log(title = "批量归档报告", businessType = BusinessType.UPDATE)
    @PostMapping("/archive/batch")
    public AjaxResult batchArchiveReports(@RequestBody String[] taskIds) {
        try {
            int successCount = reportService.batchArchiveReports(taskIds);
            return success("成功归档 " + successCount + " 个报告");
        } catch (Exception e) {
            return error("批量归档报告失败: " + e.getMessage());
        }
    }

    /**
     * 取消发布报告
     */
    @PreAuthorize("@ss.hasPermi('system:report:publish')")
    @Log(title = "取消发布报告", businessType = BusinessType.UPDATE)
    @PostMapping("/unpublish/{taskId}")
    public AjaxResult unpublishReport(@ValidTaskId @PathVariable String taskId) {
        try {
            boolean result = reportService.unpublishReport(taskId);
            return result ? success("取消发布成功") : error("取消发布失败");
        } catch (Exception e) {
            return error("取消发布报告失败: " + e.getMessage());
        }
    }

    /**
     * 恢复归档报告
     */
    @PreAuthorize("@ss.hasPermi('system:report:archive')")
    @Log(title = "恢复归档报告", businessType = BusinessType.UPDATE)
    @PostMapping("/restore/{taskId}")
    public AjaxResult restoreReport(@ValidTaskId @PathVariable String taskId) {
        try {
            boolean result = reportService.restoreReport(taskId);
            return result ? success("恢复报告成功") : error("恢复报告失败");
        } catch (Exception e) {
            return error("恢复报告失败: " + e.getMessage());
        }
    }
}