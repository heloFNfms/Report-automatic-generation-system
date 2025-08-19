package com.ruoyi.web.controller.system;

import java.util.List;
import javax.servlet.http.HttpServletResponse;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.system.domain.ReportStepHistory;
import com.ruoyi.system.service.IReportStepHistoryService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 报告步骤历史Controller
 * 
 * @author ruoyi
 * @date 2024-01-01
 */
@RestController
@RequestMapping("/system/stepHistory")
public class ReportStepHistoryController extends BaseController {
    @Autowired
    private IReportStepHistoryService reportStepHistoryService;

    /**
     * 查询报告步骤历史列表
     */
    @PreAuthorize("@ss.hasPermi('system:stepHistory:list')")
    @GetMapping("/list")
    public TableDataInfo list(ReportStepHistory reportStepHistory) {
        startPage();
        List<ReportStepHistory> list = reportStepHistoryService.selectReportStepHistoryList(reportStepHistory);
        return getDataTable(list);
    }

    /**
     * 导出报告步骤历史列表
     */
    @PreAuthorize("@ss.hasPermi('system:stepHistory:export')")
    @Log(title = "报告步骤历史", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(HttpServletResponse response, ReportStepHistory reportStepHistory) {
        List<ReportStepHistory> list = reportStepHistoryService.selectReportStepHistoryList(reportStepHistory);
        ExcelUtil<ReportStepHistory> util = new ExcelUtil<ReportStepHistory>(ReportStepHistory.class);
        util.exportExcel(response, list, "报告步骤历史数据");
    }

    /**
     * 获取报告步骤历史详细信息
     */
    @PreAuthorize("@ss.hasPermi('system:stepHistory:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return success(reportStepHistoryService.selectReportStepHistoryById(id));
    }

    /**
     * 根据任务ID查询步骤历史
     */
    @GetMapping("/task/{taskId}")
    public AjaxResult getHistoryByTaskId(@PathVariable("taskId") String taskId) {
        List<ReportStepHistory> list = reportStepHistoryService.selectReportStepHistoryByTaskId(taskId);
        return success(list);
    }

    /**
     * 根据任务ID和步骤查询历史
     */
    @GetMapping("/task/{taskId}/step/{step}")
    public AjaxResult getHistoryByTaskIdAndStep(@PathVariable("taskId") String taskId,
            @PathVariable("step") String step) {
        List<ReportStepHistory> list = reportStepHistoryService.selectReportStepHistoryByTaskIdAndStep(taskId, step);
        return success(list);
    }

    /**
     * 根据任务ID、步骤和版本查询历史
     */
    @GetMapping("/task/{taskId}/step/{step}/version/{version}")
    public AjaxResult getHistoryByTaskIdAndStepAndVersion(@PathVariable("taskId") String taskId,
            @PathVariable("step") String step,
            @PathVariable("version") Integer version) {
        ReportStepHistory history = reportStepHistoryService.selectReportStepHistoryByTaskIdAndStepAndVersion(taskId,
                step, version);
        return success(history);
    }

    /**
     * 新增报告步骤历史
     */
    @PreAuthorize("@ss.hasPermi('system:stepHistory:add')")
    @Log(title = "报告步骤历史", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody ReportStepHistory reportStepHistory) {
        return toAjax(reportStepHistoryService.insertReportStepHistory(reportStepHistory));
    }

    /**
     * 保存步骤执行历史
     */
    @PostMapping("/save")
    public AjaxResult saveStepHistory(@RequestBody ReportStepHistory reportStepHistory) {
        int result = reportStepHistoryService.saveStepHistory(
                reportStepHistory.getTaskId(),
                reportStepHistory.getStep(),
                reportStepHistory.getOutputJson(),
                reportStepHistory.getExecutionTime(),
                reportStepHistory.getStatus(),
                reportStepHistory.getErrorMessage());
        return toAjax(result);
    }

    /**
     * 修改报告步骤历史
     */
    @PreAuthorize("@ss.hasPermi('system:stepHistory:edit')")
    @Log(title = "报告步骤历史", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody ReportStepHistory reportStepHistory) {
        return toAjax(reportStepHistoryService.updateReportStepHistory(reportStepHistory));
    }

    /**
     * 删除报告步骤历史
     */
    @PreAuthorize("@ss.hasPermi('system:stepHistory:remove')")
    @Log(title = "报告步骤历史", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return toAjax(reportStepHistoryService.deleteReportStepHistoryByIds(ids));
    }

    /**
     * 根据任务ID删除步骤历史
     */
    @DeleteMapping("/task/{taskId}")
    public AjaxResult removeByTaskId(@PathVariable("taskId") String taskId) {
        return toAjax(reportStepHistoryService.deleteReportStepHistoryByTaskId(taskId));
    }

    /**
     * 回滚到指定版本
     */
    @PostMapping("/rollback/{taskId}/{step}/{version}")
    public AjaxResult rollbackToVersion(@PathVariable("taskId") String taskId,
            @PathVariable("step") String step,
            @PathVariable("version") Integer version) {
        ReportStepHistory history = reportStepHistoryService.rollbackToVersion(taskId, step, version);
        if (history != null) {
            return AjaxResult.success("回滚成功", history);
        } else {
            return error("回滚失败，未找到指定版本的历史记录");
        }
    }
}