<template>
  <n-card class="my-card" title="">
    <div class="actions mb-4">
      <div class="p-4 max-w-xl mx-auto">
        <!-- 上传文件部分 -->
        <input type="file" accept="application/pdf" @change="onFileChange" />
        <!-- 确认上传按钮 -->
        <button class="mt-2 px-4 py-2 rounded shadow bg-blue-500 text-white" :disabled="!file || loading"
          @click="upload">
          {{ loading ? '上传中…' : '上传' }}
        </button>

        <div v-if="message" class="mt-4 text-green-600">{{ message }}</div>
        <n-button @click="batchDownloadPDF" :disabled="!hasSelection">批量下载 PDF</n-button>
        <n-button @click="batchDownloadMD" :disabled="!hasSelection">批量下载 MD</n-button>
        <n-button @click="batchDelete" type="error" :disabled="!hasSelection">批量删除</n-button>
        <n-button @click="selectAll">全选</n-button>
        <n-button @click="invertSelect">反选</n-button>
      </div>
    </div>

    <n-data-table :columns="columns" :data="docs" :row-key="rowKey" v-model:checked-row-keys="checkedKeys" />
    <!-- Markdown 预览弹框 -->
    <n-modal v-model:show="showMdModal" title="Markdown 预览" size="600px">
      <div class="markdown-body" v-html="renderedMd"></div>
    </n-modal>
  </n-card>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import {
  NCard,
  NButton,
  NDataTable,
  NCheckbox,
  NSpace
} from 'naive-ui'
import MarkdownIt from 'markdown-it'
import JSZip from 'jszip'
import { saveAs } from 'file-saver'
import { uploadPdf, fetchDocs, deleteDoc } from '@/api/pdf'

const file = ref(null)
const loading = ref(false)
const message = ref('')
const docs = ref([])
const checkedKeys = ref([])
const hasSelection = computed(() => checkedKeys.value.length > 0)
const showMdModal = ref(false)
const renderedMd = ref('')
const mdParser = new MarkdownIt()
function rowKey(row) {
  return row.pdf_name
}

mdParser.use((md) => {
  const defaultImage = md.renderer.rules.image
  md.renderer.rules.image = (tokens, idx, options, env, self) => {
    const token = tokens[idx]
    let src = token.attrGet("src")
    if (src && src.startsWith("images/")) {
      // env.imgPrefix 从 to_dict() 里传过来的前缀
      src = env.imgPrefix + src.replace(/^images\//, "")
      token.attrSet("src", src)
    }
    return (defaultImage || self.renderToken)(tokens, idx, options, env, self)
  }
})

// 渲染列定义，使用 render 函数
const columns = [
  { type: 'selection', title: '勾选' },
  {
    key: 'pdf_name',
    title: '文件名',
    render: row => h('a', {
      href: row.pdf_url,
      target: '_blank',
      rel: 'noopener'
    }, row.pdf_name)
  },
  { key: 'pdf_time', title: '上传日期' },
  { key: 'pdf_size', title: '文件体积' },
  {
    key: 'md_name',
    title: 'Markdown',
    render: row => {
      if (row.md_name === 'UNKNOWN') {
        return h('span', '处理中…')
      }
      // 预览按钮
      return h('a', {
        onClick: async () => {
          const res = await fetch(row.md_url)
          const text = await res.text()
          renderedMd.value = mdParser.render(text, { imgPrefix: row.img_prefix })
          showMdModal.value = true
        },
        style: { cursor: 'pointer', color: '#409EFF' }
      }, row.md_name)
    }
  }
]

function selectAll() {
  checkedKeys.value = docs.value.map(d => d.pdf_name)
}
function invertSelect() {
  const all = docs.value.map(d => d.pdf_name)
  checkedKeys.value = all.filter(k => !checkedKeys.value.includes(k))
}

// 刷新列表的函数
async function load() {
  try {
    const res = await fetchDocs()
    docs.value = res.data.map(d => ({ ...d, _checked: false }))
  } catch (e) {
    console.error('加载文件列表失败', e)
  }
}
// 在挂载时自动加载一次
onMounted(load)

// 上传文件的函数
function onFileChange(e) {
  file.value = e.target.files[0]
}

async function upload() {
  if (!file.value) {
    alert('请先选择 PDF')
    return
  }

  loading.value = true
  message.value = ''

  try {
    // 上传 PDF
    const form = new FormData()
    form.append('file', file.value)
    const { data } = await uploadPdf(form)
    message.value = `上传成功：${data.pdf_name}`

    setTimeout(() => {
      load()
    }, 1000)
  } catch (err) {
    console.error(err)
    alert('上传失败，请检查后端是否正常运行')
  } finally {
    loading.value = false
  }
}

async function batchDownloadPDF() {
  const selected = docs.value.filter(d => checkedKeys.value.includes(d.pdf_name))
  if (!selected.length) return
  try {
    const zip = new JSZip()
    for (const row of selected) {
      const res = await fetch(row.pdf_url)
      if (!res.ok) throw new Error(`下载失败：${row.pdf_name}`)
      const blob = await res.blob()
      zip.file(row.pdf_name, blob)
    }
    const content = await zip.generateAsync({ type: 'blob' })
    saveAs(content, 'pdfs.zip')
  } catch (e) {
    console.error('批量下载 PDF 失败', e)
    alert('批量下载 PDF 失败，请重试')
  }
}

async function batchDownloadMD() {
  const selected = docs.value.filter(
    d => checkedKeys.value.includes(d.pdf_name) && d.md_name !== 'UNKNOWN'
  )
  if (!selected.length) return
  const zip = new JSZip()
  for (const row of selected) {
    const blob = await fetch(row.md_url).then(r => r.blob())
    zip.file(row.md_name, blob)
  }
  const content = await zip.generateAsync({ type: 'blob' })
  saveAs(content, 'markdowns.zip')
}

async function batchDelete() {
  if (!confirm('确定要删除选中的文档吗？')) return
  const selected = docs.value.filter(d => checkedKeys.value.includes(d.pdf_name))
  await Promise.all(selected.map(row => deleteDoc(row.file_base, row.pdf_name)))
  await load()
}
</script>

<style scoped>
.my-card {
  min-width: 800px;
}

.markdown-body {
  max-height: 70vh;
  overflow: auto;
  padding: 1em;
  background: #ffffff;
  border-radius: 4px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
  line-height: 1.6;
  color: #24292e;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
}

.markdown-body p {
  margin: 0.5em 0;
}

.markdown-body a {
  color: #0366d6;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body code {
  background-color: rgba(27, 31, 35, 0.05);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, Courier, monospace;
}

.markdown-body pre {
  background-color: #f6f8fa;
  padding: 1em;
  overflow: auto;
  border-radius: 3px;
}

.markdown-body blockquote {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
}

.markdown-body ul,
.markdown-body ol {
  margin: 0.5em 0 0.5em 1.5em;
}

.markdown-body table {
  border-collapse: collapse;
  margin: 0.75em 0;
  width: 100%;
}

.markdown-body table th,
.markdown-body table td {
  border: 1px solid #dfe2e5;
  padding: 0.6em 1em;
}

.markdown-body table th {
  background-color: #f6f8fa;
  font-weight: 600;
}
</style>
