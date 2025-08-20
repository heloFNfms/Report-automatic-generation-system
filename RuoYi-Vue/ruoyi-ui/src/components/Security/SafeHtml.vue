<template>
  <div ref="safeHtml"></div>
</template>

<script>
// 尝试导入DOMPurify，如果失败则使用fallback
let DOMPurify = null
try {
  DOMPurify = require('dompurify')
} catch (e) {
  console.warn('DOMPurify not available, using basic HTML sanitization')
}

export default {
  name: 'SafeHtml',
  props: {
    content: {
      type: String,
      default: ''
    },
    config: {
      type: Object,
      default: () => ({
        ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th'],
        ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'style'],
        ALLOW_DATA_ATTR: false
      })
    }
  },
  watch: {
    content: {
      immediate: true,
      handler(newContent) {
        this.updateContent(newContent)
      }
    }
  },
  methods: {
    // 基础HTML净化函数（fallback）
    basicSanitize(html) {
      if (!html) return ''
      
      // 移除script标签和事件处理器
      let cleaned = html
        .replace(/<script[^>]*>.*?<\/script>/gi, '')
        .replace(/<iframe[^>]*>.*?<\/iframe>/gi, '')
        .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '')
        .replace(/javascript:/gi, '')
        .replace(/vbscript:/gi, '')
        .replace(/data:/gi, '')
      
      // 只允许安全的标签
      const allowedTags = this.config.ALLOWED_TAGS.join('|')
      const tagRegex = new RegExp(`<(?!/?(?:${allowedTags})\\b)[^>]+>`, 'gi')
      cleaned = cleaned.replace(tagRegex, '')
      
      return cleaned
    },
    
    updateContent(content) {
      if (this.$refs.safeHtml) {
        let cleanHtml
        if (DOMPurify) {
          // 使用DOMPurify进行高级净化
          cleanHtml = DOMPurify.sanitize(content || '', this.config)
        } else {
          // 使用基础净化函数
          cleanHtml = this.basicSanitize(content || '')
        }
        this.$refs.safeHtml.innerHTML = cleanHtml
      }
    }
  },
  mounted() {
    this.updateContent(this.content)
  }
}
</script>

<style scoped>
/* 安全HTML组件样式 */
</style>
