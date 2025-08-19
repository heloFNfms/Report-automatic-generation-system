<template>
  <div class="report-wizard">
    <div class="wizard-header">
      <h2>报告生成向导</h2>
      <p>通过5个简单步骤，快速生成专业的研究报告</p>
    </div>

    <!-- 步骤条 -->
    <el-steps :active="currentStep - 1" finish-status="success" align-center>
      <el-step title="基本信息" description="填写项目基本信息"></el-step>
      <el-step title="生成大纲" description="AI生成研究大纲"></el-step>
      <el-step title="内容检索" description="检索相关文献资料"></el-step>
      <el-step title="报告组装" description="组装并润色报告"></el-step>
      <el-step title="完成报告" description="生成最终报告"></el-step>
    </el-steps>

    <!-- 步骤内容 -->
    <div class="wizard-content">
      <!-- Step 1: 基本信息 -->
      <div v-show="currentStep === 1" class="step-content">
        <el-card>
          <div slot="header">
            <span>步骤1：填写基本信息</span>
          </div>
          <el-form ref="step1Form" :model="reportForm" :rules="step1Rules" label-width="120px">
            <el-form-item label="项目名称" prop="projectName">
              <el-input v-model="reportForm.projectName" placeholder="请输入项目名称"></el-input>
            </el-form-item>
            <el-form-item label="公司名称" prop="companyName">
              <el-input v-model="reportForm.companyName" placeholder="请输入公司名称"></el-input>
            </el-form-item>
            <el-form-item label="研究主题" prop="researchTopic">
              <el-input v-model="reportForm.researchTopic" placeholder="请输入研究主题"></el-input>
            </el-form-item>
            <el-form-item label="详细描述" prop="description">
              <el-input
                type="textarea"
                v-model="reportForm.description"
                :rows="4"
                placeholder="请详细描述研究内容、目标和要求"
              ></el-input>
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <!-- Step 2: 生成大纲 -->
      <div v-show="currentStep === 2" class="step-content">
        <el-card>
          <div slot="header" class="clearfix">
            <span>步骤2：生成研究大纲</span>
            <div style="float: right;">
              <el-button
                v-if="step2.result && outlineModified"
                type="text"
                @click="saveOutline"
                :disabled="!outlineModified"
              >
                保存修改
              </el-button>
              <el-button
                v-if="step2.result"
                type="primary"
                size="small"
                @click="regenerateOutline"
                :loading="step2.loading"
              >
                重新生成
              </el-button>
            </div>
          </div>
          
          <div v-if="step2.loading" class="loading-content">
            <el-progress :percentage="step2.progress" :show-text="true"></el-progress>
            <p class="loading-text">正在生成研究大纲，请稍候...</p>
          </div>
          
          <div v-else-if="step2.result && outlineTreeData.length > 0" class="outline-content">
            <el-tree
              ref="outlineTree"
              :data="outlineTreeData"
              :props="treeProps"
              :expand-on-click-node="false"
              default-expand-all
              node-key="id"
              class="outline-tree"
              :allow-drop="allowDrop"
              :allow-drag="allowDrag"
              draggable
            >
              <span class="custom-tree-node" slot-scope="{ node, data }">
                <span v-if="!data.editing" class="node-content">
                  <i :class="getNodeIcon(data.level)" style="margin-right: 5px;"></i>
                  <span class="node-label">{{ data.title }}</span>
                </span>
                <el-input
                  v-else
                  v-model="data.title"
                  size="mini"
                  @blur="saveNodeEdit(data)"
                  @keyup.enter.native="saveNodeEdit(data)"
                  ref="nodeInput"
                />
                <span class="node-actions">
                  <span class="node-level">{{ getLevelText(data.level) }}</span>
                  <el-button
                    v-if="!data.editing"
                    type="text"
                    size="mini"
                    @click="editOutlineNode(data)"
                    icon="el-icon-edit"
                    title="编辑"
                  >
                  </el-button>
                  <el-button
                    v-if="data.level < 3"
                    type="text"
                    size="mini"
                    @click="addChildNode(data)"
                    icon="el-icon-plus"
                    title="添加子节点"
                  >
                  </el-button>
                  <el-button
                    type="text"
                    size="mini"
                    @click="deleteNode(data)"
                    icon="el-icon-delete"
                    title="删除"
                  >
                  </el-button>
                </span>
              </span>
            </el-tree>
            <div class="outline-actions" style="margin-top: 15px;">
              <el-button type="primary" @click="addRootNode">添加章节</el-button>
              <el-button @click="expandAll">展开全部</el-button>
              <el-button @click="collapseAll">收起全部</el-button>
            </div>
          </div>
          
          <div v-else class="empty-content">
            <el-empty description="暂无大纲数据">
              <el-button type="primary" @click="executeStep2">生成大纲</el-button>
            </el-empty>
          </div>
        </el-card>
      </div>

      <!-- Step 3: 内容检索 -->
      <div v-show="currentStep === 3" class="step-content">
        <el-card>
          <div slot="header" class="clearfix">
            <span>步骤3：章节内容生成</span>
            <div style="float: right;">
              <el-button
                v-if="step3.result"
                type="primary"
                size="small"
                @click="regenerateAllContent"
                :loading="step3.loading"
              >
                重新生成全部
              </el-button>
            </div>
          </div>
          
          <div v-if="step3.loading && !chapterContents.length" class="loading-content">
            <el-progress :percentage="step3.progress" :show-text="true"></el-progress>
            <p class="loading-text">正在检索文献并生成章节内容...</p>
          </div>
          
          <div v-else-if="step3.result && chapterContents.length > 0" class="content-display">
            <div class="content-summary">
              <el-alert
                title="内容生成完成"
                :description="`共生成 ${chapterContents.length} 个章节，${getTotalReferences()} 个参考资料`"
                type="success"
                :closable="false"
                style="margin-bottom: 20px;"
              >
              </el-alert>
            </div>
            
            <div class="chapter-list">
              <div v-for="(chapter, index) in chapterContents" :key="index" class="chapter-section">
                <el-card class="chapter-card" shadow="hover">
                  <div slot="header" class="chapter-header">
                    <div class="chapter-title">
                      <i :class="getChapterIcon(chapter.level)"></i>
                      <span>{{ chapter.title }}</span>
                      <el-tag size="mini" :type="getChapterTagType(chapter.level)">{{ getLevelText(chapter.level) }}</el-tag>
                    </div>
                    <div class="chapter-actions">
                      <el-button
                        type="text"
                        size="small"
                        @click="editChapterContent(index)"
                        icon="el-icon-edit"
                      >
                        编辑
                      </el-button>
                      <el-button
                        type="text"
                        size="small"
                        @click="regenerateChapter(index)"
                        :loading="chapter.loading"
                        icon="el-icon-refresh"
                      >
                        重新生成
                      </el-button>
                    </div>
                  </div>
                  
                  <div class="chapter-content">
                    <div v-if="!chapter.editing" class="content-text">
                      <p v-html="formatContent(chapter.content)"></p>
                    </div>
                    <div v-else class="content-editor">
                      <el-input
                        v-model="chapter.content"
                        type="textarea"
                        :rows="6"
                        placeholder="请输入章节内容"
                      ></el-input>
                      <div class="editor-actions" style="margin-top: 10px;">
                        <el-button size="mini" type="primary" @click="saveChapterContent(index)">保存</el-button>
                        <el-button size="mini" @click="cancelEditChapter(index)">取消</el-button>
                      </div>
                    </div>
                    
                    <div v-if="chapter.references && chapter.references.length > 0" class="references-section">
                      <div class="references-header">
                        <i class="el-icon-link"></i>
                        <span>参考资料 ({{ chapter.references.length }})</span>
                      </div>
                      <div class="reference-links">
                        <el-link
                          v-for="(ref, refIndex) in chapter.references"
                          :key="refIndex"
                          :href="ref.url"
                          target="_blank"
                          type="primary"
                          class="reference-item"
                          :underline="false"
                        >
                          <i class="el-icon-document"></i>
                          {{ ref.title }}
                        </el-link>
                      </div>
                    </div>
                    
                    <div class="chapter-stats">
                      <el-tag size="mini" effect="plain">字数: {{ getWordCount(chapter.content) }}</el-tag>
                      <el-tag size="mini" effect="plain" type="info">更新时间: {{ formatTime(chapter.updateTime) }}</el-tag>
                    </div>
                  </div>
                </el-card>
              </div>
            </div>
          </div>
          
          <div v-else class="empty-content">
            <el-empty description="暂无内容数据">
              <el-button type="primary" @click="executeStep3">生成章节内容</el-button>
            </el-empty>
          </div>
        </el-card>
      </div>

      <!-- Step 4: 报告组装 -->
      <div v-show="currentStep === 4" class="step-content">
        <el-card>
          <div slot="header">
            <span>步骤4：报告组装润色</span>
            <el-button
              v-if="step4.result"
              type="primary"
              size="small"
              style="float: right"
              @click="regenerateReport"
              :loading="step4.loading"
            >
              重新生成
            </el-button>
          </div>
          
          <div v-if="step4.loading" class="loading-content">
            <el-progress :percentage="step4.progress" :show-text="true"></el-progress>
            <p class="loading-text">正在组装并润色报告...</p>
          </div>
          
          <div v-else-if="step4.result" class="report-preview">
            <!-- 报告头部信息 -->
            <div class="report-header">
              <div class="header-left">
                <h2><i class="el-icon-document"></i> 初版报告预览</h2>
                <div class="report-info">
                  <el-tag type="info" size="small">{{ step4.result.title || '未命名报告' }}</el-tag>
                  <span class="word-count">字数：{{ getWordCount(step4.result.content) }}</span>
                  <span class="update-time">生成时间：{{ formatTime(step4.result.createTime) }}</span>
                </div>
              </div>
              <div class="header-actions">
                <el-button size="small" @click="regenerateReport" :loading="step4.regenerating">
                  <i class="el-icon-refresh"></i> 重新生成
                </el-button>
                <el-button size="small" type="primary" @click="previewReport(4)">
                  <i class="el-icon-view"></i> 全屏预览
                </el-button>
              </div>
            </div>
            
            <!-- 报告内容 -->
            <div class="report-content-wrapper">
              <div class="content-toolbar">
                <el-button-group size="small">
                  <el-button :type="viewMode === 'preview' ? 'primary' : ''" @click="viewMode = 'preview'">
                    <i class="el-icon-view"></i> 预览
                  </el-button>
                  <el-button :type="viewMode === 'edit' ? 'primary' : ''" @click="viewMode = 'edit'">
                    <i class="el-icon-edit"></i> 编辑
                  </el-button>
                </el-button-group>
                <div class="toolbar-right">
                  <el-button size="small" @click="saveReportContent(4)" v-if="viewMode === 'edit'">
                    <i class="el-icon-check"></i> 保存修改
                  </el-button>
                </div>
              </div>
              
              <div v-if="viewMode === 'preview'" class="report-content" v-html="formatContent(step4.result.content)"></div>
              <el-input 
                v-else
                type="textarea" 
                v-model="step4.result.content" 
                :rows="20"
                placeholder="请输入报告内容"
                class="content-editor"
              />
            </div>
            
            <!-- 报告统计 -->
            <div class="report-stats">
              <el-row :gutter="20">
                <el-col :span="6">
                  <div class="stat-item">
                    <i class="el-icon-document-copy"></i>
                    <div class="stat-content">
                      <div class="stat-value">{{ getChapterCount() }}</div>
                      <div class="stat-label">章节数</div>
                    </div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-item">
                    <i class="el-icon-edit-outline"></i>
                    <div class="stat-content">
                      <div class="stat-value">{{ getWordCount(step4.result.content) }}</div>
                      <div class="stat-label">字数</div>
                    </div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-item">
                    <i class="el-icon-link"></i>
                    <div class="stat-content">
                      <div class="stat-value">{{ getTotalReferences() }}</div>
                      <div class="stat-label">参考资料</div>
                    </div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-item">
                    <i class="el-icon-time"></i>
                    <div class="stat-content">
                      <div class="stat-value">{{ getGenerationTime() }}</div>
                      <div class="stat-label">生成耗时</div>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </div>
          
          <div v-else class="empty-content">
            <el-empty description="暂无报告数据"></el-empty>
          </div>
        </el-card>
      </div>

      <!-- Step 5: 完成报告 -->
      <div v-show="currentStep === 5" class="step-content">
        <el-card>
          <div slot="header">
            <span>步骤5：完成报告</span>
            <div style="float: right">
              <el-button
                v-if="step5.result"
                type="success"
                size="small"
                @click="downloadReport('pdf')"
              >
                下载PDF
              </el-button>
              <el-button
                v-if="step5.result"
                type="primary"
                size="small"
                @click="downloadReport('word')"
              >
                下载Word
              </el-button>
            </div>
          </div>
          
          <div v-if="step5.loading" class="loading-content">
            <el-progress :percentage="step5.progress" :show-text="true"></el-progress>
            <p class="loading-text">正在生成最终报告...</p>
          </div>
          
          <div v-else-if="step5.result" class="final-report">
            <!-- 报告头部 -->
            <div class="report-header">
              <div class="header-left">
                <h2><i class="el-icon-medal"></i> 最终报告</h2>
                <div class="report-info">
                  <el-tag type="success" size="small">{{ step5.result.title || '未命名报告' }}</el-tag>
                  <span class="word-count">字数：{{ getWordCount(step5.result.content) }}</span>
                  <span class="update-time">完成时间：{{ formatTime(step5.result.createTime) }}</span>
                </div>
              </div>
              <div class="header-actions">
                <el-button size="small" @click="regenerateReport" :loading="step5.regenerating">
                  <i class="el-icon-refresh"></i> 重新生成
                </el-button>
                <el-button size="small" type="primary" @click="previewReport(5)">
                  <i class="el-icon-view"></i> 全屏预览
                </el-button>
              </div>
            </div>
            
            <!-- 报告摘要和关键词 -->
            <div class="report-meta">
              <el-card class="meta-card" shadow="never">
                <div class="meta-section">
                  <h4><i class="el-icon-document"></i> 摘要</h4>
                  <div v-if="!editingAbstract" class="meta-content">
                    <p>{{ step5.result.summary || '暂无摘要' }}</p>
                    <el-button size="mini" type="text" @click="editAbstract">
                      <i class="el-icon-edit"></i> 编辑
                    </el-button>
                  </div>
                  <div v-else class="meta-edit">
                    <el-input 
                      type="textarea" 
                      v-model="step5.result.summary" 
                      :rows="3"
                      placeholder="请输入报告摘要"
                    />
                    <div class="edit-actions">
                      <el-button size="mini" type="primary" @click="saveAbstract">保存</el-button>
                      <el-button size="mini" @click="cancelEditAbstract">取消</el-button>
                    </div>
                  </div>
                </div>
                
                <div class="meta-section">
                  <h4><i class="el-icon-collection-tag"></i> 关键词</h4>
                  <div v-if="!editingKeywords" class="meta-content">
                    <div class="keywords-display">
                      <el-tag 
                        v-for="keyword in step5.result.keywords" 
                        :key="keyword" 
                        size="small" 
                        class="keyword-tag"
                        style="margin-right: 8px"
                      >
                        {{ keyword }}
                      </el-tag>
                      <el-button size="mini" type="text" @click="editKeywords">
                        <i class="el-icon-edit"></i> 编辑
                      </el-button>
                    </div>
                  </div>
                  <div v-else class="meta-edit">
                    <el-input 
                      v-model="keywordsText" 
                      placeholder="请输入关键词，用逗号分隔"
                    />
                    <div class="edit-actions">
                      <el-button size="mini" type="primary" @click="saveKeywords">保存</el-button>
                      <el-button size="mini" @click="cancelEditKeywords">取消</el-button>
                    </div>
                  </div>
                </div>
              </el-card>
            </div>
            
            <!-- 报告内容 -->
            <div class="report-content-wrapper">
              <div class="content-toolbar">
                <el-button-group size="small">
                  <el-button :type="viewMode === 'preview' ? 'primary' : ''" @click="viewMode = 'preview'">
                    <i class="el-icon-view"></i> 预览
                  </el-button>
                  <el-button :type="viewMode === 'edit' ? 'primary' : ''" @click="viewMode = 'edit'">
                    <i class="el-icon-edit"></i> 编辑
                  </el-button>
                </el-button-group>
                <div class="toolbar-right">
                  <el-button size="small" @click="saveReportContent(5)" v-if="viewMode === 'edit'">
                    <i class="el-icon-check"></i> 保存修改
                  </el-button>
                </div>
              </div>
              
              <div v-if="viewMode === 'preview'" class="report-content" v-html="formatContent(step5.result.content)"></div>
              <el-input 
                v-else
                type="textarea" 
                v-model="step5.result.content" 
                :rows="20"
                placeholder="请输入报告内容"
                class="content-editor"
              />
            </div>
            
            <!-- 导出操作 -->
            <div class="export-section">
              <el-card class="export-card" shadow="never">
                <div class="export-header">
                  <h4><i class="el-icon-download"></i> 导出报告</h4>
                  <p>选择导出格式并下载最终报告</p>
                </div>
                <div class="export-actions">
                  <el-button 
                    type="danger" 
                    size="medium" 
                    @click="exportReport('pdf')" 
                    :loading="exporting.pdf"
                  >
                    <i class="el-icon-document"></i> 导出PDF
                  </el-button>
                  <el-button 
                    type="primary" 
                    size="medium" 
                    @click="exportReport('docx')" 
                    :loading="exporting.docx"
                  >
                    <i class="el-icon-document-copy"></i> 导出DOCX
                  </el-button>
                  <el-button 
                    type="success" 
                    size="medium" 
                    @click="exportReport('html')" 
                    :loading="exporting.html"
                  >
                    <i class="el-icon-document-add"></i> 导出HTML
                  </el-button>
                  <el-button 
                    type="info" 
                    size="medium" 
                    @click="downloadReport" 
                    :loading="downloading"
                  >
                    <i class="el-icon-download"></i> 下载报告
                  </el-button>
                </div>
                <div class="export-history" v-if="exportHistory.length > 0">
                  <h5>导出历史</h5>
                  <div class="history-list">
                    <div 
                      v-for="item in exportHistory" 
                      :key="item.id" 
                      class="history-item"
                    >
                      <div class="history-info">
                        <span class="format-tag">{{ item.format.toUpperCase() }}</span>
                        <span class="file-name">{{ item.fileName }}</span>
                        <span class="export-time">{{ formatTime(item.exportTime) }}</span>
                      </div>
                      <div class="history-actions">
                        <el-button size="mini" type="text" @click="downloadExportedFile(item)">
                          <i class="el-icon-download"></i> 下载
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </el-card>
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
      <el-button v-if="currentStep > 1" @click="prevStep">上一步</el-button>
      <el-button
        v-if="currentStep < 5"
        type="primary"
        @click="nextStep"
        :loading="isStepLoading"
      >
        {{ currentStep === 1 ? '开始生成' : '下一步' }}
      </el-button>
      <el-button v-if="currentStep === 5" type="success" @click="completeWizard">
        完成
      </el-button>
    </div>
  </div>
</template>

<script>
import { executeStep1, executeStep2, executeStep3, executeStep4, executeStep5, getStepResult, rerunStep, exportReport } from '@/api/report'

export default {
  name: 'ReportWizard',
  data() {
    return {
      currentStep: 1,
      taskId: null,
      
      // 表单数据
      reportForm: {
        projectName: '',
        companyName: '',
        researchTopic: '',
        description: ''
      },
      
      // 表单验证规则
      step1Rules: {
        projectName: [
          { required: true, message: '请输入项目名称', trigger: 'blur' }
        ],
        companyName: [
          { required: true, message: '请输入公司名称', trigger: 'blur' }
        ],
        researchTopic: [
          { required: true, message: '请输入研究主题', trigger: 'blur' }
        ],
        description: [
          { required: true, message: '请输入详细描述', trigger: 'blur' }
        ]
      },
      
      // 各步骤状态
      step2: {
        loading: false,
        progress: 0,
        result: null
      },
      step3: {
        loading: false,
        progress: 0,
        result: null
      },
      step4: {
        loading: false,
        progress: 0,
        regenerating: false,
        result: {
          title: '智能制造技术研究报告',
          content: '这是初版报告的内容...',
          createTime: new Date()
        }
      },
      step5: {
        loading: false,
        progress: 0,
        regenerating: false,
        result: {
          title: '智能制造技术研究报告（最终版）',
          content: '这是最终报告的内容...',
          summary: '本报告深入研究了智能制造技术的发展现状、关键技术和未来趋势，为企业数字化转型提供了重要参考。',
          keywords: ['智能制造', '工业4.0', '数字化转型', '人工智能', '物联网'],
          createTime: new Date()
        }
      },
      
      // 树形组件属性
      treeProps: {
        children: 'children',
        label: 'title'
      },
      // 大纲修改标识
      outlineModified: false,
      // 节点ID计数器
      nodeIdCounter: 1000,
      
      // 章节内容数据
      chapterContents: [],
      
      // 视图模式
      viewMode: 'preview',
      
      // 编辑状态
      editingAbstract: false,
      editingKeywords: false,
      keywordsText: '',
      
      // 导出状态
      exporting: {
        pdf: false,
        docx: false,
        html: false
      },
      downloading: false,
      
      // 导出历史
      exportHistory: []
    }
  },
  
  computed: {
    isStepLoading() {
      return this.step2.loading || this.step3.loading || this.step4.loading || this.step5.loading
    },
    
    outlineTreeData() {
      if (!this.step2.result || !this.step2.result.outline) {
        return []
      }
      return this.convertOutlineToTree(this.step2.result.outline)
    }
  },
  
  methods: {
    // 下一步
    nextStep() {
      if (this.currentStep === 1) {
        this.executeStep1()
      } else if (this.currentStep === 2) {
        this.executeStep2()
      } else if (this.currentStep === 3) {
        this.executeStep3()
      } else if (this.currentStep === 4) {
        this.executeStep4()
      } else if (this.currentStep === 5) {
        this.executeStep5()
      }
    },
    
    // 上一步
    prevStep() {
      if (this.currentStep > 1) {
        this.currentStep--
      }
    },
    
    // 执行步骤1
    async executeStep1() {
      try {
        await this.$refs.step1Form.validate()
        
        const response = await executeStep1(this.reportForm)
        this.taskId = response.data
        
        this.$message.success('基本信息保存成功')
        this.currentStep = 2
        
        // 自动执行步骤2
        setTimeout(() => {
          this.executeStep2()
        }, 500)
        
      } catch (error) {
        if (error.message) {
          this.$message.error('表单验证失败')
        } else {
          this.$message.error('保存失败：' + (error.msg || error.message))
        }
      }
    },
    
    // 执行步骤2
    async executeStep2() {
      if (!this.taskId) {
        this.$message.error('任务ID不存在')
        return
      }
      
      this.step2.loading = true
      this.step2.progress = 0
      
      try {
        // 模拟进度
        const progressInterval = setInterval(() => {
          if (this.step2.progress < 90) {
            this.step2.progress += 10
          }
        }, 500)
        
        const response = await executeStep2(this.taskId)
        
        clearInterval(progressInterval)
        this.step2.progress = 100
        this.step2.result = response.data
        
        this.$message.success('大纲生成成功')
        
      } catch (error) {
        this.$message.error('大纲生成失败：' + (error.msg || error.message))
      } finally {
        this.step2.loading = false
      }
    },
    
    // 执行步骤3
    async executeStep3() {
      if (!this.taskId) {
        this.$message.error('任务ID不存在')
        return
      }
      
      this.step3.loading = true
      this.step3.progress = 0
      
      try {
        const progressInterval = setInterval(() => {
          if (this.step3.progress < 90) {
            this.step3.progress += 5
          }
        }, 1000)
        
        const response = await executeStep3(this.taskId)
        
        clearInterval(progressInterval)
        this.step3.progress = 100
        this.step3.result = response.data
        
        this.$message.success('内容生成成功')
        
      } catch (error) {
        this.$message.error('内容生成失败：' + (error.msg || error.message))
      } finally {
        this.step3.loading = false
      }
    },
    
    // 执行步骤4
    async executeStep4() {
      if (!this.taskId) {
        this.$message.error('任务ID不存在')
        return
      }
      
      this.step4.loading = true
      this.step4.progress = 0
      
      try {
        const progressInterval = setInterval(() => {
          if (this.step4.progress < 90) {
            this.step4.progress += 10
          }
        }, 800)
        
        const response = await executeStep4(this.taskId)
        
        clearInterval(progressInterval)
        this.step4.progress = 100
        this.step4.result = response.data
        
        this.$message.success('报告组装成功')
        
      } catch (error) {
        this.$message.error('报告组装失败：' + (error.msg || error.message))
      } finally {
        this.step4.loading = false
      }
    },
    
    // 执行步骤5
    async executeStep5() {
      if (!this.taskId) {
        this.$message.error('任务ID不存在')
        return
      }
      
      this.step5.loading = true
      this.step5.progress = 0
      
      try {
        const progressInterval = setInterval(() => {
          if (this.step5.progress < 90) {
            this.step5.progress += 15
          }
        }, 600)
        
        const response = await executeStep5(this.taskId)
        
        clearInterval(progressInterval)
        this.step5.progress = 100
        this.step5.result = response.data
        
        this.$message.success('报告生成完成')
        
      } catch (error) {
        this.$message.error('报告生成失败：' + (error.msg || error.message))
      } finally {
        this.step5.loading = false
      }
    },
    
    // 重新生成大纲
    async regenerateOutline() {
      try {
        await rerunStep(this.taskId, '2')
        this.step2.result = null
        this.executeStep2()
      } catch (error) {
        this.$message.error('重新生成失败：' + (error.msg || error.message))
      }
    },
    
    // 重新生成内容
    async regenerateContent() {
      try {
        await rerunStep(this.taskId, '3')
        this.step3.result = null
        this.executeStep3()
      } catch (error) {
        this.$message.error('重新生成失败：' + (error.msg || error.message))
      }
    },
    
    // 重新生成报告
    async regenerateReport() {
      try {
        await rerunStep(this.taskId, '4')
        this.step4.result = null
        this.executeStep4()
      } catch (error) {
        this.$message.error('重新生成失败：' + (error.msg || error.message))
      }
    },
    
    // 下载报告
    async downloadReport(format) {
      try {
        const response = await exportReport(this.taskId, format)
        
        // 创建下载链接
        const blob = new Blob([response.data])
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${this.reportForm.projectName}_报告.${format === 'pdf' ? 'pdf' : 'docx'}`
        link.click()
        window.URL.revokeObjectURL(url)
        
        this.$message.success('下载成功')
      } catch (error) {
        this.$message.error('下载失败：' + (error.msg || error.message))
      }
    },
    
    // 完成向导
    completeWizard() {
      this.$message.success('报告生成完成！')
      this.$router.push('/report/list')
    },
    
    // 转换大纲为树形数据
    convertOutlineToTree(outline) {
      if (typeof outline === 'string') {
        // 如果是字符串，尝试解析为JSON
        try {
          outline = JSON.parse(outline)
        } catch (e) {
          // 如果解析失败，按行分割处理
          return this.parseOutlineText(outline)
        }
      }
      
      if (Array.isArray(outline)) {
        return outline.map((item, index) => ({
          id: index,
          title: item.title || item,
          level: item.level || 1,
          children: item.children ? this.convertOutlineToTree(item.children) : []
        }))
      }
      
      return []
    },
    
    // 解析文本格式的大纲
    parseOutlineText(text) {
      const lines = text.split('\n').filter(line => line.trim())
      const result = []
      
      lines.forEach((line, index) => {
        const trimmed = line.trim()
        let level = 1
        let title = trimmed
        
        // 检测层级
        if (trimmed.match(/^\d+\./)) {
          level = 1
          title = trimmed.replace(/^\d+\.\s*/, '')
        } else if (trimmed.match(/^\d+\.\d+/)) {
          level = 2
          title = trimmed.replace(/^\d+\.\d+\s*/, '')
        } else if (trimmed.match(/^\d+\.\d+\.\d+/)) {
          level = 3
          title = trimmed.replace(/^\d+\.\d+\.\d+\s*/, '')
        }
        
        result.push({
          id: index,
          title: title,
          level: level,
          children: []
        })
      })
      
      return result
    },
    
    // 获取层级文本
    getLevelText(level) {
      const levelMap = {
        1: '一级标题',
        2: '二级标题',
        3: '三级标题'
      }
      return levelMap[level] || '标题'
    },
    
    // 获取节点图标
    getNodeIcon(level) {
      const iconMap = {
        1: 'el-icon-folder',
        2: 'el-icon-document',
        3: 'el-icon-tickets'
      };
      return iconMap[level] || 'el-icon-document';
    },
    
    // 编辑大纲节点
    editOutlineNode(data) {
      this.$set(data, 'editing', true);
      this.$nextTick(() => {
        const input = this.$refs.nodeInput;
        if (input && input.length) {
          input[input.length - 1].focus();
        }
      });
    },
    
    // 保存节点编辑
    saveNodeEdit(data) {
      this.$set(data, 'editing', false);
      this.outlineModified = true;
    },
    
    // 添加子节点
    addChildNode(parentData) {
      if (!parentData.children) {
        this.$set(parentData, 'children', []);
      }
      const newNode = {
        id: ++this.nodeIdCounter,
        title: '新节点',
        level: parentData.level + 1,
        children: [],
        editing: true
      };
      parentData.children.push(newNode);
      this.outlineModified = true;
      this.$nextTick(() => {
        const input = this.$refs.nodeInput;
        if (input && input.length) {
          input[input.length - 1].focus();
        }
      });
    },
    
    // 添加根节点
    addRootNode() {
      const newNode = {
        id: ++this.nodeIdCounter,
        title: '新章节',
        level: 1,
        children: [],
        editing: true
      };
      this.outlineTreeData.push(newNode);
      this.outlineModified = true;
      this.$nextTick(() => {
        const input = this.$refs.nodeInput;
        if (input && input.length) {
          input[input.length - 1].focus();
        }
      });
    },
    
    // 删除节点
    deleteNode(data) {
      this.$confirm('确认删除此节点及其所有子节点？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.removeNodeFromTree(this.outlineTreeData, data.id);
        this.outlineModified = true;
        this.$message.success('删除成功');
      }).catch(() => {});
    },
    
    // 从树中移除节点
    removeNodeFromTree(tree, nodeId) {
      for (let i = 0; i < tree.length; i++) {
        if (tree[i].id === nodeId) {
          tree.splice(i, 1);
          return true;
        }
        if (tree[i].children && tree[i].children.length > 0) {
          if (this.removeNodeFromTree(tree[i].children, nodeId)) {
            return true;
          }
        }
      }
      return false;
    },
    
    // 保存大纲
    saveOutline() {
      this.$message.success('大纲保存成功');
      this.outlineModified = false;
      // 这里可以调用API保存大纲数据
    },
    
    // 展开全部
    expandAll() {
      this.$refs.outlineTree.filter('');
    },
    
    // 收起全部
    collapseAll() {
      const tree = this.$refs.outlineTree;
      tree.store.nodesMap = {};
      tree.store.root.childNodes = [];
      tree.store._initDefaultCheckedNodes();
      this.$nextTick(() => {
        tree.store.root.childNodes.forEach(child => {
          child.expanded = false;
        });
      });
    },
    
    // 允许拖拽
    allowDrag(draggingNode) {
      return true;
    },
    
    // 允许放置
     allowDrop(draggingNode, dropNode, type) {
       // 不允许跨级别拖拽
       if (type === 'inner') {
         return dropNode.data.level < 3;
       }
       return true;
     },
     
     // 获取章节图标
     getChapterIcon(level) {
       const iconMap = {
         1: 'el-icon-folder-opened',
         2: 'el-icon-document',
         3: 'el-icon-tickets'
       };
       return iconMap[level] || 'el-icon-document';
     },
     
     // 获取章节标签类型
     getChapterTagType(level) {
       const typeMap = {
         1: 'primary',
         2: 'success',
         3: 'info'
       };
       return typeMap[level] || 'info';
     },
     
     // 格式化内容
     formatContent(content) {
       if (!content) return '';
       // 将换行符转换为HTML换行
       return content.replace(/\n/g, '<br>');
     },
     
     // 获取字数
     getWordCount(content) {
       if (!content) return 0;
       return content.replace(/\s/g, '').length;
     },
     
     // 格式化时间
     formatTime(time) {
       if (!time) return '未知';
       return new Date(time).toLocaleString();
     },
     
     // 获取总参考资料数
     getTotalReferences() {
       let total = 0;
       this.chapterContents.forEach(chapter => {
         if (chapter.references) {
           total += chapter.references.length;
         }
       });
       return total;
     },
     
     // 编辑章节内容
     editChapterContent(index) {
       this.$set(this.chapterContents[index], 'editing', true);
       this.$set(this.chapterContents[index], 'originalContent', this.chapterContents[index].content);
     },
     
     // 保存章节内容
     saveChapterContent(index) {
       this.$set(this.chapterContents[index], 'editing', false);
       this.$set(this.chapterContents[index], 'updateTime', new Date());
       this.$message.success('章节内容保存成功');
       // 这里可以调用API保存章节内容
     },
     
     // 取消编辑章节
     cancelEditChapter(index) {
       this.chapterContents[index].content = this.chapterContents[index].originalContent;
       this.$set(this.chapterContents[index], 'editing', false);
     },
     
     // 重新生成章节
     regenerateChapter(index) {
       this.$confirm('确认重新生成此章节内容？', '提示', {
         confirmButtonText: '确定',
         cancelButtonText: '取消',
         type: 'warning'
       }).then(() => {
         this.$set(this.chapterContents[index], 'loading', true);
         
         // 模拟API调用
         setTimeout(() => {
           this.chapterContents[index].content = '这是重新生成的章节内容...';
           this.$set(this.chapterContents[index], 'updateTime', new Date());
           this.$set(this.chapterContents[index], 'loading', false);
           this.$message.success('章节重新生成成功');
         }, 2000);
       }).catch(() => {});
     },
     
     // 重新生成全部内容
     regenerateAllContent() {
       this.$confirm('确认重新生成所有章节内容？', '提示', {
         confirmButtonText: '确定',
         cancelButtonText: '取消',
         type: 'warning'
       }).then(() => {
         this.step3.loading = true;
         
         // 模拟API调用
         setTimeout(() => {
           this.chapterContents.forEach(chapter => {
             chapter.content = '这是重新生成的章节内容...';
             chapter.updateTime = new Date();
           });
           this.step3.loading = false;
           this.$message.success('所有章节重新生成成功');
         }, 3000);
       }).catch(() => {});
     },
     
     // 获取章节数量
     getChapterCount() {
       return this.chapterContents.length || 0;
     },
     
     // 获取生成耗时
     getGenerationTime() {
       return '2分30秒'; // 模拟数据
     },
     
     // 预览报告
     previewReport(step) {
       this.$message.info('全屏预览功能开发中...');
     },
     
     // 保存报告内容
     saveReportContent(step) {
       this.$message.success('报告内容保存成功');
     },
     
     // 编辑摘要
     editAbstract() {
       this.editingAbstract = true;
     },
     
     // 保存摘要
     saveAbstract() {
       this.editingAbstract = false;
       this.$message.success('摘要保存成功');
     },
     
     // 取消编辑摘要
     cancelEditAbstract() {
       this.editingAbstract = false;
     },
     
     // 编辑关键词
     editKeywords() {
       this.editingKeywords = true;
       this.keywordsText = this.step5.result.keywords ? this.step5.result.keywords.join(', ') : '';
     },
     
     // 保存关键词
     saveKeywords() {
       this.step5.result.keywords = this.keywordsText.split(',').map(k => k.trim()).filter(k => k);
       this.editingKeywords = false;
       this.$message.success('关键词保存成功');
     },
     
     // 取消编辑关键词
     cancelEditKeywords() {
       this.editingKeywords = false;
     },
     
     // 导出报告
     async exportReport(format) {
       this.exporting[format] = true;
       
       try {
         // 模拟导出过程
         await new Promise(resolve => setTimeout(resolve, 2000));
         
         const fileName = `${this.reportForm.projectName}_报告.${format}`;
         const exportItem = {
           id: Date.now(),
           format: format,
           fileName: fileName,
           exportTime: new Date()
         };
         
         this.exportHistory.unshift(exportItem);
         this.$message.success(`${format.toUpperCase()}导出成功`);
         
       } catch (error) {
         this.$message.error('导出失败：' + error.message);
       } finally {
         this.exporting[format] = false;
       }
     },
     
     // 下载导出的文件
      downloadExportedFile(item) {
        this.$message.success(`开始下载 ${item.fileName}`);
      },
      
      // 重新生成报告
      async regenerateReport(step) {
        this.$confirm(`确认重新生成${step === 4 ? '初版' : '最终'}报告？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(async () => {
          if (step === 4) {
            this.step4.regenerating = true;
            // 模拟API调用
            await new Promise(resolve => setTimeout(resolve, 3000));
            this.step4.result.content = '这是重新生成的初版报告内容...';
            this.step4.result.createTime = new Date();
            this.step4.regenerating = false;
            this.$message.success('初版报告重新生成成功');
          } else {
            this.step5.regenerating = true;
            // 模拟API调用
            await new Promise(resolve => setTimeout(resolve, 3000));
            this.step5.result.content = '这是重新生成的最终报告内容...';
            this.step5.result.createTime = new Date();
            this.step5.regenerating = false;
            this.$message.success('最终报告重新生成成功');
          }
        }).catch(() => {});
      },
      
      // 下载报告
      async downloadReport() {
        this.downloading = true;
        
        try {
          // 模拟下载过程
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          const fileName = `${this.reportForm.projectName}_最终报告.pdf`;
          this.$message.success(`开始下载 ${fileName}`);
          
        } catch (error) {
          this.$message.error('下载失败：' + error.message);
        } finally {
          this.downloading = false;
        }
      }
  }
}
</script>

<style scoped>
.report-wizard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.wizard-header {
  text-align: center;
  margin-bottom: 30px;
}

.wizard-header h2 {
  color: #303133;
  margin-bottom: 10px;
}

.wizard-header p {
  color: #909399;
  font-size: 14px;
}

.wizard-content {
  margin: 30px 0;
}

.step-content {
  min-height: 400px;
}

.loading-content {
  text-align: center;
  padding: 50px 0;
}

.loading-text {
  margin-top: 20px;
  color: #909399;
}

.outline-content {
  padding: 20px 0;
}

.outline-tree {
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  padding: 10px;
}

.custom-tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.node-content {
  display: flex;
  align-items: center;
  flex: 1;
}

.node-label {
  flex: 1;
  font-size: 14px;
  margin-left: 5px;
}

.node-actions {
  display: flex;
  align-items: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.custom-tree-node:hover .node-actions {
  opacity: 1;
}

.node-level {
  font-size: 12px;
  color: #909399;
  background: #F5F7FA;
  padding: 2px 8px;
  border-radius: 12px;
  margin-right: 10px;
}

.outline-actions {
  text-align: center;
  padding: 10px;
  border-top: 1px solid #e4e7ed;
}

.outline-actions .el-button {
  margin: 0 5px;
}

/* 树节点编辑样式 */
.el-tree-node__content {
  height: auto;
  min-height: 26px;
  padding: 5px 0;
}

.el-tree-node__content:hover {
  background-color: #f5f7fa;
}

/* 不同级别节点的样式 */
.outline-tree .el-tree-node[data-level="1"] > .el-tree-node__content {
  font-weight: bold;
  font-size: 16px;
}

.outline-tree .el-tree-node[data-level="2"] > .el-tree-node__content {
  font-size: 14px;
}

.outline-tree .el-tree-node[data-level="3"] > .el-tree-node__content {
  font-size: 13px;
  color: #606266;
}

/* Step3 章节内容样式 */
.content-summary {
  margin-bottom: 20px;
}

.chapter-list {
  max-height: 600px;
  overflow-y: auto;
}

.chapter-section {
  margin-bottom: 20px;
}

.chapter-card {
  border-radius: 8px;
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chapter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.chapter-title i {
  font-size: 16px;
  color: #409eff;
}

.chapter-actions {
  display: flex;
  gap: 5px;
}

.content-text {
  line-height: 1.8;
  color: #303133;
  margin-bottom: 15px;
}

.content-text p {
  margin: 0 0 10px 0;
  text-indent: 2em;
}

.content-editor {
  margin-bottom: 15px;
}

.editor-actions {
  text-align: right;
}

.references-section {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

.references-header {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 10px;
  font-weight: 500;
  color: #606266;
}

.reference-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.reference-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  transition: all 0.3s;
}

.reference-item:hover {
  background: #e3f2fd;
  border-color: #409eff;
}

.reference-item i {
  font-size: 12px;
}

.chapter-stats {
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  gap: 10px;
}

.loading-content {
  text-align: center;
  padding: 40px;
}

.loading-content p {
  margin-top: 15px;
  color: #606266;
}

.content-sections {
  padding: 20px 0;
}

.section-item {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
}

.section-item h4 {
  color: #303133;
  margin-bottom: 15px;
  border-bottom: 2px solid #409EFF;
  padding-bottom: 8px;
}

.section-content {
  line-height: 1.6;
  color: #606266;
  margin-bottom: 15px;
}

.section-references h5 {
  color: #303133;
  margin-bottom: 10px;
}

.section-references ul {
  margin: 0;
  padding-left: 20px;
}

.section-references li {
  margin-bottom: 5px;
}

.section-references a {
  color: #409EFF;
  text-decoration: none;
}

.section-references a:hover {
  text-decoration: underline;
}

.report-preview {
  padding: 20px 0;
}

.report-content {
  line-height: 1.8;
  color: #303133;
  background: #FAFAFA;
  padding: 20px;
  border-radius: 4px;
  border: 1px solid #EBEEF5;
}

.final-report {
  padding: 20px 0;
}

.report-summary {
  margin-bottom: 20px;
  padding: 15px;
  background: #F0F9FF;
  border-left: 4px solid #409EFF;
}

.report-summary h3 {
  color: #303133;
  margin-bottom: 10px;
}

.report-keywords {
  margin-bottom: 20px;
  padding: 15px;
  background: #F5F7FA;
  border-radius: 4px;
}

.report-keywords h3 {
  color: #303133;
  margin-bottom: 10px;
}

.empty-content {
  padding: 50px 0;
  text-align: center;
}

.wizard-actions {
  text-align: center;
  padding: 20px 0;
  border-top: 1px solid #EBEEF5;
}

.wizard-actions .el-button {
  margin: 0 10px;
}

/* Step 4 & 5 报告样式 */
.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.header-left h2 {
  margin: 0 0 10px 0;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.report-info {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 13px;
  color: #606266;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.report-content-wrapper {
  margin: 20px 0;
}

.content-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.toolbar-right {
  display: flex;
  gap: 10px;
}

.content-editor {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.report-stats {
  margin-top: 20px;
  padding: 15px;
  background: #fafbfc;
  border-radius: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stat-item i {
  font-size: 24px;
  color: #409eff;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

/* Step 5 特有样式 */
.meta-card {
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
}

.meta-section {
  margin-bottom: 20px;
}

.meta-section:last-child {
  margin-bottom: 0;
}

.meta-section h4 {
  margin: 0 0 10px 0;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.meta-content p {
  margin: 0;
  line-height: 1.6;
  color: #606266;
  flex: 1;
}

.keywords-display {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.keyword-tag {
  margin-bottom: 5px;
}

.meta-edit {
  width: 100%;
}

.edit-actions {
  margin-top: 10px;
  text-align: right;
}

.export-section {
  margin-top: 20px;
}

.export-card {
  border: 1px solid #e4e7ed;
}

.export-header {
  margin-bottom: 20px;
}

.export-header h4 {
  margin: 0 0 8px 0;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.export-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.export-actions {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.export-history {
  border-top: 1px solid #f0f0f0;
  padding-top: 15px;
}

.export-history h5 {
  margin: 0 0 10px 0;
  color: #606266;
  font-size: 14px;
}

.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 8px;
}

.history-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.format-tag {
  background: #409eff;
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: bold;
}

.file-name {
  font-weight: 500;
  color: #303133;
}

.export-time {
  font-size: 12px;
  color: #909399;
}

.history-actions {
  display: flex;
  gap: 5px;
}
</style>