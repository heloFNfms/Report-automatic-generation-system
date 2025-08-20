<template>
  <div class="report-editor">
    <div class="editor-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/system/report' }">报告管理</el-breadcrumb-item>
        <el-breadcrumb-item>在线编辑</el-breadcrumb-item>
      </el-breadcrumb>
      
      <div class="header-actions">
        <el-button-group>
          <el-button :type="editMode === 'chapter' ? 'primary' : 'default'" @click="setEditMode('chapter')">
            <i class="el-icon-menu"></i> 按章编辑
          </el-button>
          <el-button :type="editMode === 'full' ? 'primary' : 'default'" @click="setEditMode('full')">
            <i class="el-icon-document"></i> 整体编辑
          </el-button>
        </el-button-group>
        
        <el-button type="success" @click="saveReport" :loading="saveLoading">
          <i class="el-icon-check"></i> 保存
        </el-button>
        <el-button type="primary" @click="previewReport">
          <i class="el-icon-view"></i> 预览
        </el-button>
        <el-button @click="exportReport">
          <i class="el-icon-download"></i> 导出
        </el-button>
      </div>
    </div>

    <div class="editor-content">
      <!-- 按章编辑模式 -->
      <div v-if="editMode === 'chapter'" class="chapter-editor">
        <div class="chapter-sidebar">
          <div class="sidebar-header">
            <h3>章节目录</h3>
            <el-button size="mini" type="primary" @click="addChapter">
              <i class="el-icon-plus"></i> 添加章节
            </el-button>
          </div>
          
          <el-tree
            :data="chapterTree"
            :props="treeProps"
            node-key="id"
            :current-node-key="currentChapterId"
            @node-click="selectChapter"
            draggable
            @node-drop="handleChapterDrop"
            class="chapter-tree">
            <span class="custom-tree-node" slot-scope="{ node, data }">
              <span class="node-label">{{ data.title }}</span>
              <span class="node-actions">
                <el-button type="text" size="mini" @click.stop="editChapterTitle(data)">
                  <i class="el-icon-edit"></i>
                </el-button>
                <el-button type="text" size="mini" @click.stop="deleteChapter(data)">
                  <i class="el-icon-delete"></i>
                </el-button>
              </span>
            </span>
          </el-tree>
        </div>
        
        <div class="chapter-content">
          <div v-if="currentChapter" class="chapter-editor-area">
            <div class="chapter-header">
              <el-input
                v-model="currentChapter.title"
                placeholder="章节标题"
                class="chapter-title-input"
                @blur="updateChapterTitle">
              </el-input>
            </div>
            
            <!-- 富文本编辑器 -->
            <div class="editor-container">
              <quill-editor
                ref="chapterEditor"
                v-model="currentChapter.content"
                :options="editorOptions"
                @change="onChapterContentChange"
                class="chapter-quill-editor">
              </quill-editor>
            </div>
            
            <!-- 章节参考链接 -->
            <div class="chapter-references">
              <h4>参考链接</h4>
              <div v-for="(ref, index) in currentChapter.references" :key="index" class="reference-item">
                <el-input v-model="ref.title" placeholder="链接标题" style="width: 200px; margin-right: 10px;"></el-input>
                <el-input v-model="ref.url" placeholder="链接地址" style="width: 300px; margin-right: 10px;"></el-input>
                <el-button size="mini" type="danger" @click="removeReference(index)">
                  <i class="el-icon-delete"></i>
                </el-button>
              </div>
              <el-button size="mini" type="primary" @click="addReference">
                <i class="el-icon-plus"></i> 添加参考链接
              </el-button>
            </div>
          </div>
          
          <div v-else class="empty-chapter">
            <el-empty description="请选择一个章节进行编辑"></el-empty>
          </div>
        </div>
      </div>

      <!-- 整体编辑模式 -->
      <div v-if="editMode === 'full'" class="full-editor">
        <div class="report-meta">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-input v-model="reportMeta.title" placeholder="报告标题" class="report-title-input"></el-input>
            </el-col>
            <el-col :span="6">
              <el-input v-model="reportMeta.author" placeholder="作者"></el-input>
            </el-col>
            <el-col :span="6">
              <el-date-picker v-model="reportMeta.date" type="date" placeholder="报告日期"></el-date-picker>
            </el-col>
          </el-row>
        </div>
        
        <div class="editor-container">
          <quill-editor
            ref="fullEditor"
            v-model="fullContent"
            :options="fullEditorOptions"
            @change="onFullContentChange"
            class="full-quill-editor">
          </quill-editor>
        </div>
      </div>
    </div>

    <!-- 预览对话框 -->
    <el-dialog title="报告预览" :visible.sync="previewVisible" width="80%" class="preview-dialog">
      <div class="preview-content" v-html="previewHtml"></div>
      <div slot="footer" class="dialog-footer">
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" @click="exportFromPreview">导出</el-button>
      </div>
    </el-dialog>

    <!-- 章节标题编辑对话框 -->
    <el-dialog title="编辑章节标题" :visible.sync="titleEditVisible" width="400px">
      <el-input v-model="editingTitle" placeholder="请输入章节标题"></el-input>
      <div slot="footer" class="dialog-footer">
        <el-button @click="titleEditVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmTitleEdit">确定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { quillEditor } from 'vue-quill-editor'
import 'quill/dist/quill.core.css'
import 'quill/dist/quill.snow.css'
import 'quill/dist/quill.bubble.css'
import { getReportEditContent, updateReportContent, exportReport } from '@/api/system/report'

export default {
  name: 'ReportEditor',
  components: {
    quillEditor
  },
  data() {
    return {
      taskId: null,
      editMode: 'chapter', // 'chapter' | 'full'
      saveLoading: false,
      previewVisible: false,
      titleEditVisible: false,
      editingTitle: '',
      editingChapter: null,
      
      // 章节编辑相关
      chapterTree: [],
      currentChapterId: null,
      currentChapter: null,
      treeProps: {
        children: 'children',
        label: 'title'
      },
      
      // 整体编辑相关
      reportMeta: {
        title: '',
        author: '',
        date: new Date()
      },
      fullContent: '',
      previewHtml: '',
      
      // 编辑器配置
      editorOptions: {
        theme: 'snow',
        placeholder: '请输入章节内容...',
        modules: {
          toolbar: [
            ['bold', 'italic', 'underline', 'strike'],
            ['blockquote', 'code-block'],
            [{ 'header': 1 }, { 'header': 2 }],
            [{ 'list': 'ordered'}, { 'list': 'bullet' }],
            [{ 'script': 'sub'}, { 'script': 'super' }],
            [{ 'indent': '-1'}, { 'indent': '+1' }],
            [{ 'direction': 'rtl' }],
            [{ 'size': ['small', false, 'large', 'huge'] }],
            [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
            [{ 'color': [] }, { 'background': [] }],
            [{ 'font': [] }],
            [{ 'align': [] }],
            ['clean'],
            ['link', 'image', 'video']
          ]
        }
      },
      
      fullEditorOptions: {
        theme: 'snow',
        placeholder: '请输入完整报告内容...',
        modules: {
          toolbar: [
            ['bold', 'italic', 'underline', 'strike'],
            ['blockquote', 'code-block'],
            [{ 'header': 1 }, { 'header': 2 }],
            [{ 'list': 'ordered'}, { 'list': 'bullet' }],
            [{ 'script': 'sub'}, { 'script': 'super' }],
            [{ 'indent': '-1'}, { 'indent': '+1' }],
            [{ 'direction': 'rtl' }],
            [{ 'size': ['small', false, 'large', 'huge'] }],
            [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
            [{ 'color': [] }, { 'background': [] }],
            [{ 'font': [] }],
            [{ 'align': [] }],
            ['clean'],
            ['link', 'image', 'video']
          ]
        }
      }
    }
  },
  
  async mounted() {
    this.taskId = this.$route.query.taskId
    if (this.taskId) {
      await this.loadReportContent()
    }
  },
  
  methods: {
    // 加载报告内容
    async loadReportContent() {
      try {
        const response = await getReportEditContent(this.taskId)
        const data = response.data
        
        this.reportMeta = {
          title: data.title || '',
          author: data.author || '',
          date: data.date ? new Date(data.date) : new Date()
        }
        
        this.chapterTree = this.buildChapterTree(data.chapters || [])
        this.fullContent = data.fullContent || ''
        
        if (this.chapterTree.length > 0) {
          this.selectChapter(this.chapterTree[0])
        }
      } catch (error) {
        this.$message.error('加载报告内容失败：' + error.message)
      }
    },
    
    // 构建章节树
    buildChapterTree(chapters) {
      return chapters.map((chapter, index) => ({
        id: chapter.id || `chapter_${index}`,
        title: chapter.title || `章节 ${index + 1}`,
        content: chapter.content || '',
        references: chapter.references || [],
        children: chapter.children ? this.buildChapterTree(chapter.children) : []
      }))
    },
    
    // 设置编辑模式
    setEditMode(mode) {
      this.editMode = mode
    },
    
    // 选择章节
    selectChapter(chapter) {
      this.currentChapterId = chapter.id
      this.currentChapter = chapter
    },
    
    // 添加章节
    addChapter() {
      const newChapter = {
        id: `chapter_${Date.now()}`,
        title: '新章节',
        content: '',
        references: []
      }
      this.chapterTree.push(newChapter)
      this.selectChapter(newChapter)
    },
    
    // 编辑章节标题
    editChapterTitle(chapter) {
      this.editingChapter = chapter
      this.editingTitle = chapter.title
      this.titleEditVisible = true
    },
    
    // 确认标题编辑
    confirmTitleEdit() {
      if (this.editingChapter) {
        this.editingChapter.title = this.editingTitle
        this.titleEditVisible = false
      }
    },
    
    // 删除章节
    deleteChapter(chapter) {
      this.$confirm('确定要删除此章节吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        const index = this.chapterTree.findIndex(c => c.id === chapter.id)
        if (index > -1) {
          this.chapterTree.splice(index, 1)
          if (this.currentChapterId === chapter.id) {
            this.currentChapter = null
            this.currentChapterId = null
          }
        }
      })
    },
    
    // 处理章节拖拽
    handleChapterDrop(draggingNode, dropNode, dropType, ev) {
      // 重新排序章节
      this.$message.success('章节顺序已更新')
    },
    
    // 更新章节标题
    updateChapterTitle() {
      // 标题更新逻辑
    },
    
    // 章节内容变化
    onChapterContentChange() {
      // 自动保存逻辑可以在这里实现
    },
    
    // 整体内容变化
    onFullContentChange() {
      // 自动保存逻辑可以在这里实现
    },
    
    // 添加参考链接
    addReference() {
      if (this.currentChapter) {
        this.currentChapter.references.push({
          title: '',
          url: ''
        })
      }
    },
    
    // 删除参考链接
    removeReference(index) {
      if (this.currentChapter) {
        this.currentChapter.references.splice(index, 1)
      }
    },
    
    // 保存报告
    async saveReport() {
      this.saveLoading = true
      try {
        const reportData = {
          taskId: this.taskId,
          meta: this.reportMeta,
          chapters: this.chapterTree,
          fullContent: this.fullContent
        }
        
        await updateReportContent(reportData)
        this.$message.success('报告保存成功')
      } catch (error) {
        this.$message.error('保存失败：' + error.message)
      } finally {
        this.saveLoading = false
      }
    },
    
    // 预览报告
    previewReport() {
      if (this.editMode === 'chapter') {
        this.previewHtml = this.generateChapterPreview()
      } else {
        this.previewHtml = this.fullContent
      }
      this.previewVisible = true
    },
    
    // 生成章节预览
    generateChapterPreview() {
      let html = `<h1>${this.reportMeta.title}</h1>`
      html += `<p><strong>作者：</strong>${this.reportMeta.author}</p>`
      html += `<p><strong>日期：</strong>${this.formatDate(this.reportMeta.date)}</p>`
      
      this.chapterTree.forEach(chapter => {
        html += `<h2>${chapter.title}</h2>`
        html += chapter.content
        
        if (chapter.references && chapter.references.length > 0) {
          html += '<h4>参考链接：</h4><ul>'
          chapter.references.forEach(ref => {
            html += `<li><a href="${ref.url}" target="_blank">${ref.title || ref.url}</a></li>`
          })
          html += '</ul>'
        }
      })
      
      return html
    },
    
    // 导出报告
    async exportReport() {
      try {
        await exportReport(this.taskId)
        this.$message.success('导出请求已提交，请稍后查看下载')
      } catch (error) {
        this.$message.error('导出失败：' + error.message)
      }
    },
    
    // 从预览导出
    exportFromPreview() {
      this.previewVisible = false
      this.exportReport()
    },
    
    // 格式化日期
    formatDate(date) {
      if (!date) return ''
      return new Date(date).toLocaleDateString('zh-CN')
    }
  }
}
</script>

<style scoped>
.report-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.editor-header {
  padding: 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.editor-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.chapter-editor {
  display: flex;
  width: 100%;
  height: 100%;
}

.chapter-sidebar {
  width: 300px;
  background: #f8f9fa;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
}

.chapter-tree {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;
}

.node-actions {
  opacity: 0;
  transition: opacity 0.3s;
}

.custom-tree-node:hover .node-actions {
  opacity: 1;
}

.chapter-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chapter-editor-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.chapter-header {
  margin-bottom: 20px;
}

.chapter-title-input {
  font-size: 18px;
  font-weight: bold;
}

.editor-container {
  flex: 1;
  margin-bottom: 20px;
}

.chapter-quill-editor,
.full-quill-editor {
  height: 100%;
}

.chapter-references {
  border-top: 1px solid #e4e7ed;
  padding-top: 20px;
}

.reference-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.empty-chapter {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.full-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.report-meta {
  margin-bottom: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 4px;
}

.report-title-input {
  font-size: 20px;
  font-weight: bold;
}

.preview-content {
  max-height: 600px;
  overflow-y: auto;
  padding: 20px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  line-height: 1.8;
}

.preview-dialog .el-dialog__body {
  padding: 20px;
}
</style>