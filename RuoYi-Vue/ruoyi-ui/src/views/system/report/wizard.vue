<template>
  <div class="app-container">
    <div class="wizard-container">
      <!-- 步骤条 -->
      <el-steps :active="currentStep" finish-status="success" align-center class="wizard-steps">
        <el-step title="基本信息" description="填写报告基本信息"></el-step>
        <el-step title="生成大纲" description="AI生成研究大纲"></el-step>
        <el-step title="内容检索" description="检索并生成章节内容"></el-step>
        <el-step title="报告组装" description="组装润色报告内容"></el-step>
        <el-step title="完成报告" description="生成摘要和关键词"></el-step>
      </el-steps>

      <!-- 步骤内容 -->
      <div class="wizard-content">
        <!-- 步骤1：基本信息 -->
        <div v-if="currentStep === 0" class="step-content">
          <el-card class="step-card">
            <div slot="header" class="clearfix">
              <span class="step-title">步骤1：填写报告基本信息</span>
            </div>
            <el-form ref="step1Form" :model="reportForm" :rules="step1Rules" label-width="120px">
              <el-form-item label="项目名称" prop="title">
                <el-input v-model="reportForm.title" placeholder="请输入项目名称" maxlength="100" show-word-limit></el-input>
              </el-form-item>
              <el-form-item label="公司名称" prop="company">
                <el-input v-model="reportForm.company" placeholder="请输入公司名称" maxlength="100" show-word-limit></el-input>
              </el-form-item>
              <el-form-item label="研究主题" prop="topic">
                <el-input v-model="reportForm.topic" placeholder="请输入研究主题" maxlength="200" show-word-limit></el-input>
              </el-form-item>
              <el-form-item label="详细描述" prop="description">
                <el-input
                  v-model="reportForm.description"
                  type="textarea"
                  :rows="4"
                  placeholder="请详细描述研究内容、目标和要求"
                  maxlength="1000"
                  show-word-limit
                ></el-input>
              </el-form-item>
            </el-form>
          </el-card>
        </div>

        <!-- 步骤2：生成大纲 -->
        <div v-if="currentStep === 1" class="step-content">
          <el-card class="step-card">
            <div slot="header" class="clearfix">
              <span class="step-title">步骤2：研究大纲</span>
              <el-button style="float: right; padding: 3px 0" type="text" @click="rerunStep2" :loading="step2Loading">
                <i class="el-icon-refresh"></i> 重新生成
              </el-button>
            </div>
            <div v-if="step2Loading" class="loading-content">
              <el-progress :percentage="step2Progress" :show-text="false"></el-progress>
              <p class="loading-text">正在生成研究大纲，请稍候...</p>
            </div>
            <div v-else-if="step2Result" class="outline-content">
              <el-tree
                :data="outlineTree"
                :props="treeProps"
                default-expand-all
                node-key="id"
                class="outline-tree"
              >
                <span class="custom-tree-node" slot-scope="{ node, data }">
                  <span class="node-label">{{ data.title }}</span>
                  <span class="node-description" v-if="data.description">{{ data.description }}</span>
                </span>
              </el-tree>
            </div>
            <div v-else class="empty-content">
              <el-empty description="暂无大纲数据"></el-empty>
            </div>
          </el-card>
        </div>

        <!-- 步骤3：内容检索 -->
        <div v-if="currentStep === 2" class="step-content">
          <el-card class="step-card">
            <div slot="header" class="clearfix">
              <span class="step-title">步骤3：章节内容生成</span>
              <el-button style="float: right; padding: 3px 0" type="text" @click="rerunStep3" :loading="step3Loading">
                <i class="el-icon-refresh"></i> 重新生成
              </el-button>
            </div>
            <div v-if="step3Loading" class="loading-content">
              <el-progress :percentage="step3Progress" :show-text="false"></el-progress>
              <p class="loading-text">正在检索相关文献并生成章节内容...</p>
            </div>
            <div v-else-if="step3Result" class="content-sections">
              <div v-for="(section, index) in contentSections" :key="index" class="section-item">
                <el-collapse v-model="activeSections">
                  <el-collapse-item :title="section.title" :name="index">
                    <div class="section-content" v-html="section.content"></div>
                    <div v-if="section.references && section.references.length > 0" class="section-references">
                      <h4>参考文献：</h4>
                      <ul>
                        <li v-for="(ref, refIndex) in section.references" :key="refIndex">
                          <a :href="ref.url" target="_blank" class="reference-link">
                            {{ ref.title }}
                          </a>
                        </li>
                      </ul>
                    </div>
                    <div class="section-actions">
                      <el-button size="mini" @click="rerunSection(index)" :loading="sectionLoading[index]">
                        重新生成此章节
                      </el-button>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
            <div v-else class="empty-content">
              <el-empty description="暂无章节内容"></el-empty>
            </div>
          </el-card>
        </div>

        <!-- 步骤4：报告组装 -->
        <div v-if="currentStep === 3" class="step-content">
          <el-card class="step-card">
            <div slot="header" class="clearfix">
              <span class="step-title">步骤4：报告组装润色</span>
              <el-button style="float: right; padding: 3px 0" type="text" @click="rerunStep4" :loading="step4Loading">
                <i class="el-icon-refresh"></i> 重新组装
              </el-button>
            </div>
            <div v-if="step4Loading" class="loading-content">
              <el-progress :percentage="step4Progress" :show-text="false"></el-progress>
              <p class="loading-text">正在组装润色报告内容...</p>
            </div>
            <div v-else-if="step4Result" class="report-preview">
              <div class="report-content" v-html="assembledReport"></div>
            </div>
            <div v-else class="empty-content">
              <el-empty description="暂无报告内容"></el-empty>
            </div>
          </el-card>
        </div>

        <!-- 步骤5：完成报告 -->
        <div v-if="currentStep === 4" class="step-content">
          <el-card class="step-card">
            <div slot="header" class="clearfix">
              <span class="step-title">步骤5：最终报告</span>
              <div style="float: right;">
                <el-button type="text" @click="rerunStep5" :loading="step5Loading">
                  <i class="el-icon-refresh"></i> 重新生成
                </el-button>
                <el-button type="primary" size="mini" @click="exportReport" :loading="exportLoading">
                  <i class="el-icon-download"></i> 导出报告
                </el-button>
              </div>
            </div>
            <div v-if="step5Loading" class="loading-content">
              <el-progress :percentage="step5Progress" :show-text="false"></el-progress>
              <p class="loading-text">正在生成摘要和关键词...</p>
            </div>
            <div v-else-if="step5Result" class="final-report">
              <div class="report-summary">
                <h3>报告摘要</h3>
                <p>{{ finalReport.summary }}</p>
              </div>
              <div class="report-keywords">
                <h3>关键词</h3>
                <el-tag v-for="keyword in finalReport.keywords" :key="keyword" class="keyword-tag">
                  {{ keyword }}
                </el-tag>
              </div>
              <div class="report-content">
                <h3>完整报告</h3>
                <div v-html="finalReport.content"></div>
              </div>
            </div>
            <div v-else class="empty-content">
              <el-empty description="暂无最终报告"></el-empty>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="wizard-actions">
        <el-button v-if="currentStep > 0" @click="prevStep">上一步</el-button>
        <el-button v-if="currentStep < 4" type="primary" @click="nextStep" :loading="nextStepLoading">
          {{ getNextButtonText() }}
        </el-button>
        <el-button v-if="currentStep === 4" type="success" @click="completeWizard">
          完成向导
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { executeStep1, executeStep2, executeStep3, executeStep4, executeStep5, getStepResult } from "@/api/system/report"

export default {
  name: "ReportWizard",
  data() {
    return {
      currentStep: 0,
      taskId: null,
      nextStepLoading: false,
      
      // 步骤1表单
      reportForm: {
        title: '',
        company: '',
        topic: '',
        description: ''
      },
      step1Rules: {
        title: [
          { required: true, message: '请输入项目名称', trigger: 'blur' },
          { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
        ],
        company: [
          { required: true, message: '请输入公司名称', trigger: 'blur' },
          { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
        ],
        topic: [
          { required: true, message: '请输入研究主题', trigger: 'blur' },
          { min: 5, max: 200, message: '长度在 5 到 200 个字符', trigger: 'blur' }
        ],
        description: [
          { required: true, message: '请输入详细描述', trigger: 'blur' },
          { min: 10, max: 1000, message: '长度在 10 到 1000 个字符', trigger: 'blur' }
        ]
      },
      
      // 步骤2大纲
      step2Loading: false,
      step2Progress: 0,
      step2Result: null,
      outlineTree: [],
      treeProps: {
        children: 'children',
        label: 'title'
      },
      
      // 步骤3内容
      step3Loading: false,
      step3Progress: 0,
      step3Result: null,
      contentSections: [],
      activeSections: [],
      sectionLoading: {},
      
      // 步骤4组装
      step4Loading: false,
      step4Progress: 0,
      step4Result: null,
      assembledReport: '',
      
      // 步骤5完成
      step5Loading: false,
      step5Progress: 0,
      step5Result: null,
      finalReport: {
        summary: '',
        keywords: [],
        content: ''
      },
      
      // 导出
      exportLoading: false
    }
  },
  methods: {
    // 下一步
    async nextStep() {
      if (this.currentStep === 0) {
        // 验证表单
        const valid = await this.$refs.step1Form.validate().catch(() => false)
        if (!valid) return
        
        // 执行步骤1
        await this.executeStep1()
      } else if (this.currentStep === 1) {
        // 执行步骤2
        await this.executeStep2()
      } else if (this.currentStep === 2) {
        // 执行步骤3
        await this.executeStep3()
      } else if (this.currentStep === 3) {
        // 执行步骤4
        await this.executeStep4()
      }
      
      if (this.currentStep < 4) {
        this.currentStep++
      }
    },
    
    // 上一步
    prevStep() {
      if (this.currentStep > 0) {
        this.currentStep--
      }
    },
    
    // 执行步骤1
    async executeStep1() {
      this.nextStepLoading = true
      try {
        const response = await executeStep1(this.reportForm)
        this.taskId = response.data
        this.$message.success('基本信息保存成功')
      } catch (error) {
        this.$message.error('保存失败：' + error.message)
        throw error
      } finally {
        this.nextStepLoading = false
      }
    },
    
    // 执行步骤2
    async executeStep2() {
      this.step2Loading = true
      this.step2Progress = 0
      this.nextStepLoading = true
      
      try {
        // 模拟进度
        const progressInterval = setInterval(() => {
          if (this.step2Progress < 90) {
            this.step2Progress += 10
          }
        }, 500)
        
        const response = await executeStep2(this.taskId)
        this.step2Result = response.data
        this.parseOutline(this.step2Result)
        
        clearInterval(progressInterval)
        this.step2Progress = 100
        this.$message.success('大纲生成成功')
      } catch (error) {
        this.$message.error('大纲生成失败：' + error.message)
        throw error
      } finally {
        this.step2Loading = false
        this.nextStepLoading = false
      }
    },
    
    // 执行步骤3
    async executeStep3() {
      this.step3Loading = true
      this.step3Progress = 0
      this.nextStepLoading = true
      
      try {
        const progressInterval = setInterval(() => {
          if (this.step3Progress < 90) {
            this.step3Progress += 5
          }
        }, 1000)
        
        const response = await executeStep3(this.taskId)
        this.step3Result = response.data
        this.parseContentSections(this.step3Result)
        
        clearInterval(progressInterval)
        this.step3Progress = 100
        this.$message.success('章节内容生成成功')
      } catch (error) {
        this.$message.error('内容生成失败：' + error.message)
        throw error
      } finally {
        this.step3Loading = false
        this.nextStepLoading = false
      }
    },
    
    // 执行步骤4
    async executeStep4() {
      this.step4Loading = true
      this.step4Progress = 0
      this.nextStepLoading = true
      
      try {
        const progressInterval = setInterval(() => {
          if (this.step4Progress < 90) {
            this.step4Progress += 15
          }
        }, 800)
        
        const response = await executeStep4(this.taskId)
        this.step4Result = response.data
        this.assembledReport = this.step4Result.content || ''
        
        clearInterval(progressInterval)
        this.step4Progress = 100
        this.$message.success('报告组装成功')
      } catch (error) {
        this.$message.error('报告组装失败：' + error.message)
        throw error
      } finally {
        this.step4Loading = false
        this.nextStepLoading = false
      }
    },
    
    // 执行步骤5
    async executeStep5() {
      this.step5Loading = true
      this.step5Progress = 0
      
      try {
        const progressInterval = setInterval(() => {
          if (this.step5Progress < 90) {
            this.step5Progress += 20
          }
        }, 600)
        
        const response = await executeStep5(this.taskId)
        this.step5Result = response.data
        this.finalReport = {
          summary: this.step5Result.summary || '',
          keywords: this.step5Result.keywords || [],
          content: this.step5Result.content || ''
        }
        
        clearInterval(progressInterval)
        this.step5Progress = 100
        this.$message.success('最终报告生成成功')
      } catch (error) {
        this.$message.error('最终报告生成失败：' + error.message)
      } finally {
        this.step5Loading = false
      }
    },
    
    // 重新执行步骤2
    async rerunStep2() {
      await this.executeStep2()
    },
    
    // 重新执行步骤3
    async rerunStep3() {
      await this.executeStep3()
    },
    
    // 重新执行步骤4
    async rerunStep4() {
      await this.executeStep4()
    },
    
    // 重新执行步骤5
    async rerunStep5() {
      await this.executeStep5()
    },
    
    // 重新生成章节
    async rerunSection(sectionIndex) {
      this.$set(this.sectionLoading, sectionIndex, true)
      try {
        // 这里可以调用重新生成特定章节的API
        await new Promise(resolve => setTimeout(resolve, 2000)) // 模拟API调用
        this.$message.success('章节重新生成成功')
      } catch (error) {
        this.$message.error('章节重新生成失败')
      } finally {
        this.$set(this.sectionLoading, sectionIndex, false)
      }
    },
    
    // 导出报告
    async exportReport() {
      this.exportLoading = true
      try {
        // 调用导出API
        await new Promise(resolve => setTimeout(resolve, 2000)) // 模拟导出
        this.$message.success('报告导出成功')
      } catch (error) {
        this.$message.error('报告导出失败')
      } finally {
        this.exportLoading = false
      }
    },
    
    // 完成向导
    completeWizard() {
      this.$router.push('/system/report')
    },
    
    // 解析大纲数据
    parseOutline(data) {
      // 这里根据实际返回的数据结构解析大纲
      this.outlineTree = data.outline || []
    },
    
    // 解析章节内容
    parseContentSections(data) {
      // 这里根据实际返回的数据结构解析章节内容
      this.contentSections = data.sections || []
    },
    
    // 获取下一步按钮文本
    getNextButtonText() {
      const texts = ['开始生成', '生成大纲', '生成内容', '组装报告', '生成摘要']
      return texts[this.currentStep] || '下一步'
    }
  },
  
  async mounted() {
    // 如果有传入的taskId，则加载对应的数据
    if (this.$route.query.taskId) {
      this.taskId = this.$route.query.taskId
      // 根据任务状态跳转到对应步骤
      // 这里可以调用API获取任务状态
    }
  }
}
</script>

<style scoped>
.wizard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.wizard-steps {
  margin-bottom: 40px;
}

.wizard-content {
  min-height: 500px;
  margin-bottom: 30px;
}

.step-content {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.step-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.step-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.loading-content {
  text-align: center;
  padding: 40px 20px;
}

.loading-text {
  margin-top: 15px;
  color: #606266;
  font-size: 14px;
}

.empty-content {
  padding: 40px 20px;
}

.outline-tree {
  margin-top: 20px;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;
}

.node-label {
  font-weight: bold;
  color: #303133;
}

.node-description {
  color: #909399;
  font-size: 12px;
  margin-left: 10px;
}

.content-sections {
  margin-top: 20px;
}

.section-item {
  margin-bottom: 15px;
}

.section-content {
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
  line-height: 1.6;
}

.section-references {
  margin-top: 15px;
  padding: 10px;
  background-color: #f0f9ff;
  border-radius: 4px;
}

.section-references h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #409eff;
}

.section-references ul {
  margin: 0;
  padding-left: 20px;
}

.reference-link {
  color: #409eff;
  text-decoration: none;
}

.reference-link:hover {
  text-decoration: underline;
}

.section-actions {
  margin-top: 10px;
  text-align: right;
}

.report-preview {
  margin-top: 20px;
}

.report-content {
  padding: 20px;
  background-color: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  line-height: 1.8;
  font-size: 14px;
}

.final-report {
  margin-top: 20px;
}

.report-summary,
.report-keywords {
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.report-summary h3,
.report-keywords h3 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.keyword-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.wizard-actions {
  text-align: center;
  padding: 20px 0;
  border-top: 1px solid #e4e7ed;
}

.wizard-actions .el-button {
  margin: 0 10px;
}
</style>