<template>
  <n-card title="">
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
      </div>

      <n-button @click="batchDelete" type="error" :disabled="!hasSelection">批量删除</n-button>
      <n-space>
        <n-button @click="selectAll">全选</n-button>
        <n-button @click="invertSelect">反选</n-button>
      </n-space>
    </div>

    <n-data-table :columns="columns" :data="docs">
      <template #selection="{ row }">
        <n-checkbox v-model:value="row._checked" />
      </template>
      <template #pdf_name="{ row }">
        <a :href="row.pdf_url" target="_blank" rel="noopener">
          {{ row.pdf_name }}
        </a>
      </template>
      <template #mdAction="{ row }">
        <a v-if="row.md_name !== 'UNKNOWN'" :href="row.md_url" download>
          下载 Markdown
        </a>
        <span v-else>处理中…</span>
      </template>
    </n-data-table>
  </n-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  NCard,
  NButton,
  NDataTable,
  NCheckbox,
  NSpace
} from 'naive-ui'
import JSZip from 'jszip'
import { saveAs } from 'file-saver'
import { uploadPdf, fetchDocs, deleteDoc } from '@/api/pdf'

const docs = ref([])
const columns = [
  { type: 'selection', key: '_checked', title: '' },
  { key: 'pdf_name', title: '文件名' },
  { key: 'pdf_time', title: '上传日期' },
  { key: 'pdf_size', title: '文件体积' },
  { key: 'md_name', title: 'Markdown' }
]

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

    // 上传成功后，延迟 1s 再通知父组件刷新列表
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

const hasSelection = computed(() => docs.value.some(d => d._checked))
function selectAll() { docs.value.forEach(d => (d._checked = true)) }
function invertSelect() { docs.value.forEach(d => (d._checked = !d._checked)) }

async function batchDownloadPDF() {
  // 过滤出被选中的行
  const selected = docs.value.filter(d => d._checked)
  if (selected.length === 0) return

  try {
    const zip = new JSZip()
    // 逐个下载 PDF 并添加到 zip
    for (const row of selected) {
      const res = await fetch(row.pdf_url)
      if (!res.ok) {
        throw new Error(`下载失败：${row.pdf_name}`)
      }
      const blob = await res.blob()
      // 使用原文件名
      zip.file(row.pdf_name, blob)
    }
    // 生成并触发下载
    const content = await zip.generateAsync({ type: 'blob' })
    saveAs(content, 'pdfs.zip')
  } catch (e) {
    console.error('批量下载 PDF 失败', e)
    alert('批量下载 PDF 失败，请重试')
  }
}

async function batchDownloadMD() {
  const selected = docs.value.filter(d => d._checked && d.md_name !== 'UNKNOWN')
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
  const selected = docs.value.filter(d => d._checked)
  await Promise.all(selected.map(row => deleteDoc(row.file_base, row.pdf_name)))
  await load()
}
</script>

<style scoped></style>
