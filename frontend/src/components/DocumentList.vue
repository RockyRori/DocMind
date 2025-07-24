<template>
  <n-card class="my-card" title="">
    <div class="actions mb-4">
      <div class="p-4 max-w-xl mx-auto">
        <!-- 上传文件部分 -->
        <input type="file" accept="application/pdf" multiple @change="onFileChange" />
        <!-- 确认上传按钮 -->
        <button class="mt-2 px-4 py-2 rounded shadow bg-blue-500 text-white" :disabled="!files.length || loading"
          @click="uploadAll">
          {{ loading ? '上传中…' : '上传全部' }}
        </button>

        <div v-if="message" class="mt-4 text-green-600">{{ message }}</div>
        <n-button @click="batchDownloadAll" :disabled="!hasSelection">下载全部</n-button>
        <n-button @click="batchDelete" type="error" :disabled="!hasSelection">批量删除</n-button>
        <n-button @click="selectAll">全选</n-button>
        <n-button @click="invertSelect">反选</n-button>
        <br /><br />
        <n-button @click="batchDownloadPDF" :disabled="!hasSelection">批量下载 PDF</n-button>
        <n-button @click="batchDownloadDocx" :disabled="!hasSelection">批量下载 Docx</n-button>
        <n-button @click="batchDownloadJson" :disabled="!hasSelection">批量下载 JSON</n-button>
        <n-button @click="batchDownloadMD" :disabled="!hasSelection">批量下载 MD</n-button>
        <br /><br />
      </div>
    </div>

    <n-data-table :columns="columns" :data="sortedDocs" :row-key="rowKey" v-model:checked-row-keys="checkedKeys"
      class="w-full" />
    <!-- Markdown 预览弹框 -->
    <n-modal v-model:show="showMdModal" title="Markdown 预览" size="600px">
      <div class="markdown-body" v-html="renderedMd"></div>
    </n-modal>
    <!-- Docx Preview -->
    <n-modal v-model:show="showDocxModal" title="Docx 预览" size="80%">
      <div ref="docxContainer" class="docx-container"></div>
    </n-modal>
  </n-card>
</template>

<script setup>
import { ref, computed, onMounted, h, nextTick } from 'vue'
import { NCard, NButton, NDataTable, NCheckbox, NSpace } from 'naive-ui'
import MarkdownIt from 'markdown-it'
import JSZip from 'jszip'
import { saveAs } from 'file-saver'
import { renderAsync } from 'docx-preview'
import { uploadPdfs, fetchDocs, deleteDocs } from '@/api/pdf'

// State
const files = ref([])
const loading = ref(false)
const message = ref('')
const docsOriginal = ref([])  // 原始顺序
const checkedKeys = ref([])
const showMdModal = ref(false)
const renderedMd = ref('')
const showDocxModal = ref(false)
const docxContainer = ref(null)

const mdParser = new MarkdownIt()
mdParser.use((md) => {
  const defaultImage = md.renderer.rules.image
  md.renderer.rules.image = (tokens, idx, options, env, self) => {
    const token = tokens[idx]
    let src = token.attrGet("src")
    if (src && src.startsWith("images/")) {
      src = env.imgPrefix + src.replace(/^images\//, "")
      token.attrSet("src", src)
    }
    return (defaultImage || self.renderToken)(tokens, idx, options, env, self)
  }
})

// Sorting state
const sortKey = ref(null)         // 'pdf_name' | 'pdf_time' | 'pdf_size'
const sortOrder = ref(null)       // 'asc' | 'desc' | null
const sortedDocs = computed(() => { // Compute displayed docs
  const arr = docsOriginal.value.slice()
  if (!sortKey.value || !sortOrder.value) {
    return arr
  }
  return arr.sort((a, b) => {
    let valA = a[sortKey.value]
    let valB = b[sortKey.value]
    // parse sizes if sorting size
    if (sortKey.value === 'pdf_size') {
      const toNum = s => parseFloat(s)
      valA = toNum(valA)
      valB = toNum(valB)
    }
    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })
})

// Toggle sort cycle: null -> asc -> desc -> null
function changeSort(key) {
  if (sortKey.value !== key) {
    sortKey.value = key
    sortOrder.value = 'asc'
  } else {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : sortOrder.value === 'desc' ? null : 'asc'
    if (!sortOrder.value) sortKey.value = null
  }
}

const hasSelection = computed(() => checkedKeys.value.length > 0)
function rowKey(row) {
  return row.pdf_name
}

// Columns with sort icons
const columns = [
  { type: 'selection', title: '勾选', width: '8px' },
  {
    key: 'pdf_name',
    title: () => h('div', {
      style: { display: 'flex', alignItems: 'center', cursor: 'pointer' },
      onClick: () => changeSort('pdf_name')
    }, [
      'PDF原件 ',
      sortIcon('pdf_name')
    ]),
    width: '80px'
  },
  {
    key: 'pdf_time',
    title: () => h('div', {
      style: { display: 'flex', alignItems: 'center', cursor: 'pointer' },
      onClick: () => changeSort('pdf_time')
    }, [
      '上传时间 ',
      sortIcon('pdf_time')
    ]),
    width: '80px'
  },
  {
    key: 'pdf_size',
    title: () => h('div', {
      style: { display: 'flex', alignItems: 'center', cursor: 'pointer' },
      onClick: () => changeSort('pdf_size')
    }, [
      '体积 ',
      sortIcon('pdf_size')
    ]),
    width: '60px'
  },
  {
    key: 'docx_name',
    title: 'Docx识别', width: '100px',
    render: row => row.docx_name === 'UNKNOWN' ? h('span', 'Docx生成中') : h('a', {
      onClick: async () => {
        try {
          const buf = await fetch(row.docx_url).then(r => r.arrayBuffer())
          await nextTick()
          showDocxModal.value = true
          await nextTick()
          await renderAsync(buf, docxContainer.value)
        } catch (e) {
          console.error('Docx 渲染失败', e)
          window.open(row.docx_url, '_blank')
        }
      }, style: { cursor: 'pointer', color: '#409EFF' }
    }, row.docx_name)
  },
  {
    key: 'json_name',
    title: 'Json识别', width: '100px',
    render: row => row.json_name === 'UNKNOWN' ? h('span', 'Json生成中') : h('a', { href: row.json_url, target: '_blank' }, row.json_name)
  },
  {
    key: 'md_name',
    title: 'Markdown识别',
    render: row => row.md_name === 'UNKNOWN'
      ? h('span', 'Markdown生成中')
      : h('a', {
        onClick: async () => {
          const res = await fetch(row.md_url)
          const text = await res.text()
          renderedMd.value = mdParser.render(text, { imgPrefix: row.img_prefix })
          showMdModal.value = true
        }, style: { cursor: 'pointer', color: '#409EFF' }
      }, row.md_name), width: '100px'
  }
]

function sortIcon(key) {
  if (sortKey.value !== key) return '↕'
  return sortOrder.value === 'asc' ? '▲' : sortOrder.value === 'desc' ? '▼' : '↕'
}

function selectAll() { checkedKeys.value = docsOriginal.value.map(d => d.pdf_name) }
function invertSelect() {
  const all = docsOriginal.value.map(d => d.pdf_name)
  checkedKeys.value = all.filter(k => !checkedKeys.value.includes(k))
}

// Load docs
async function load() {
  try {
    const res = await fetchDocs()
    docsOriginal.value = res.data
  } catch (e) {
    console.error('加载文件列表失败', e)
  }
}

onMounted(load)
// 上传文件的函数
function onFileChange(e) {
  files.value = Array.from(e.target.files)
}

// Batch upload
async function uploadAll() {
  if (!files.value.length) return alert('请先选择至少一个 PDF')
  loading.value = true; message.value = ''
  try {
    const form = new FormData(); files.value.forEach(f => form.append('files', f))
    const { data } = await uploadPdfs(form)
    message.value = `上传成功：${data.map(i => i.pdf_name).join('，')}`
    setTimeout(load, 1000)
  } catch { alert('上传失败') } finally { loading.value = false }
}

async function addToZip(zipFolder, urlKey, nameKey, row, includeImages = false) {
  // 主文件
  try {
    const res = await fetch(row[urlKey])
    if (res.ok) {
      const blob = await res.blob()
      zipFolder.file(row[nameKey], blob)
    }
  } catch (e) {
    console.warn(`下载 ${row[nameKey]} 失败`, e)
  }

  // 如果是 Markdown，并且要求包含 images/
  if (includeImages) {
    try {
      const resMd = await fetch(row[urlKey])
      if (!resMd.ok) return
      const text = await resMd.text()
      // 提取 images/xxx.jpg
      const imgs = Array.from(text.matchAll(/!\[.*?\]\(images\/([^\)\s]+)\)/g)).map(m => m[1])
      if (imgs.length) {
        const imgFolder = zipFolder.folder('images')
        for (const imgName of imgs) {
          try {
            const imgRes = await fetch(row.img_prefix + imgName)
            if (imgRes.ok) {
              const blob = await imgRes.blob()
              imgFolder.file(imgName, blob)
            }
          } catch { }
        }
      }
    } catch (e) {
      console.warn(`打包 ${row[nameKey]} 的图片失败`, e)
    }
  }
}

// 批量下载 PDF
async function batchDownloadPDF() {
  const selected = docsOriginal.value.filter(d => checkedKeys.value.includes(d.pdf_name))
  if (!selected.length) return
  const zip = new JSZip()
  for (const row of selected) {
    const folder = zip.folder(row.pdf_name.replace(/\.pdf$/i, ''))
    await addToZip(folder, 'pdf_url', 'pdf_name', row)
  }
  const content = await zip.generateAsync({ type: 'blob' })
  saveAs(content, 'pdfs.zip')
}

// 批量下载 Docx
async function batchDownloadDocx() {
  const selected = docsOriginal.value.filter(
    d => checkedKeys.value.includes(d.pdf_name) && d.docx_name !== 'UNKNOWN'
  )
  if (!selected.length) return
  const zip = new JSZip()
  for (const row of selected) {
    const folder = zip.folder(row.pdf_name.replace(/\.pdf$/i, ''))
    await addToZip(folder, 'docx_url', 'docx_name', row)
  }
  const content = await zip.generateAsync({ type: 'blob' })
  saveAs(content, 'docxs.zip')
}

// 批量下载 JSON
async function batchDownloadJson() {
  const selected = docsOriginal.value.filter(
    d => checkedKeys.value.includes(d.pdf_name) && d.json_name !== 'UNKNOWN'
  )
  if (!selected.length) return
  const zip = new JSZip()
  for (const row of selected) {
    const folder = zip.folder(row.pdf_name.replace(/\.pdf$/i, ''))
    await addToZip(folder, 'json_url', 'json_name', row)
  }
  const content = await zip.generateAsync({ type: 'blob' })
  saveAs(content, 'jsons.zip')
}

// 批量下载 MD（包含 images/）
async function batchDownloadMD() {
  const selected = docsOriginal.value.filter(
    d => checkedKeys.value.includes(d.pdf_name) && d.md_name !== 'UNKNOWN'
  )
  if (!selected.length) return
  const zip = new JSZip()
  for (const row of selected) {
    const folder = zip.folder(row.pdf_name.replace(/\.pdf$/i, ''))
    await addToZip(folder, 'md_url', 'md_name', row, true)
  }
  const content = await zip.generateAsync({ type: 'blob' })
  saveAs(content, 'markdowns.zip')
}

// 下载全部：PDF、MD+images、Docx、JSON
async function batchDownloadAll() {
  const selected = docsOriginal.value.filter(d => checkedKeys.value.includes(d.pdf_name))
  if (!selected.length) return
  const zip = new JSZip()
  for (const row of selected) {
    const baseName = row.pdf_name.replace(/\.pdf$/i, '')
    const folder = zip.folder(baseName)
    await addToZip(folder, 'pdf_url', 'pdf_name', row)
    if (row.md_name !== 'UNKNOWN') {
      await addToZip(folder, 'md_url', 'md_name', row, true)
    }
    if (row.docx_name !== 'UNKNOWN') {
      await addToZip(folder, 'docx_url', 'docx_name', row)
    }
    if (row.json_name !== 'UNKNOWN') {
      await addToZip(folder, 'json_url', 'json_name', row)
    }
  }
  const content = await zip.generateAsync({ type: 'blob' })
  saveAs(content, 'all_files.zip')
}

async function batchDelete() { if (!confirm('删除?')) return; await Promise.all(docsOriginal.value.filter(d => checkedKeys.value.includes(d.pdf_name)).map(r => deleteDocs(r.file_base, r.pdf_name))); load() }

</script>

<style scoped>
.my-card {
  min-width: 1000px;
}

.docx-container {
  width: 100%;
  height: 90vh;
  overflow: auto;
}

.markdown-body {
  max-height: 88vh;
  overflow: auto;
  padding: 1em;
  background: #fff;
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
