<template>
  <n-card title="文档列表">
    <div class="actions mb-4">
      <n-button @click="batchDownload" :disabled="!hasSelection">批量下载 MD</n-button>
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
        <a
          v-if="row.md_name !== 'UNKNOWN'"
          :href="row.md_url"
          download
        >
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
import { fetchDocs, deleteDoc } from '@/api/pdf'

const docs = ref([])
const columns = [
  { type: 'selection', key: '_checked', title: '' },
  { key: 'pdf_name', title: '文件名' },
  { key: 'pdf_time', title: '上传日期' },
  { key: 'pdf_size', title: '文件体积' },
  { key: 'mdAction', title: 'Markdown' }
]

onMounted(load)
async function load() {
  try {
    const res = await fetchDocs()
    docs.value = res.data.map(d => ({ ...d, _checked: false }))
  } catch (e) {
    console.error('加载文件列表失败', e)
  }
}

const hasSelection = computed(() => docs.value.some(d => d._checked))
function selectAll() { docs.value.forEach(d => (d._checked = true)) }
function invertSelect() { docs.value.forEach(d => (d._checked = !d._checked)) }

async function batchDownload() {
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

<style scoped>
</style>
