<template>
  <div class="p-4 max-w-xl mx-auto">
    <h2 class="text-2xl mb-4">上传 PDF 转 Markdown</h2>
    <input type="file" accept="application/pdf" @change="onFileChange" />
    <button
      class="mt-2 px-4 py-2 rounded shadow bg-blue-500 text-white"
      :disabled="!file || loading"
      @click="upload"
    >
      {{ loading ? '上传中…' : '上传并转换' }}
    </button>

    <div v-if="markdown" class="mt-6">
      <h3 class="text-xl mb-2">转换结果</h3>
      <textarea
        v-model="markdown"
        class="w-full h-64 p-2 border rounded font-mono"
      ></textarea>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { uploadPdf, fetchMarkdown } from '@/api/pdf'

const file = ref(null)
const markdown = ref('')
const loading = ref(false)

function onFileChange(e) {
  file.value = e.target.files[0]
}

async function upload() {
  if (!file.value) return
  loading.value = true
  const form = new FormData()
  form.append('file', file.value)
  try {
    const { data } = await uploadPdf(form)
    const res = await fetchMarkdown(data.id)
    markdown.value = res.data.markdown
  } catch (err) {
    console.error(err)
    alert('上传或转换失败，请检查后端是否正常运行')
  } finally {
    loading.value = false
  }
}
</script>
