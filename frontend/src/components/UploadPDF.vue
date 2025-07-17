<template>
  <div class="p-4 max-w-xl mx-auto">
    <h2 class="text-2xl mb-4">上传 PDF</h2>

    <input type="file" accept="application/pdf" @change="onFileChange" />
    <button
      class="mt-2 px-4 py-2 rounded shadow bg-blue-500 text-white"
      :disabled="!file || loading"
      @click="upload"
    >
      {{ loading ? '上传中…' : '上传' }}
    </button>

    <div v-if="message" class="mt-4 text-green-600">{{ message }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { uploadPdf, fetchDocs } from '@/api/pdf'

const file = ref(null)
const loading = ref(false)
const message = ref('')

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
    // 1. 上传 PDF
    const form = new FormData()
    form.append('file', file.value)
    const { data } = await uploadPdf(form)
    message.value = `上传成功：${data.pdf_name}`

    // 2. 可选：刷新列表（示例打印，改为发事件或调用父组件方法）
    const listRes = await fetchDocs()
    console.log('当前文档列表：', listRes.data)
  } catch (err) {
    console.error(err)
    alert('上传失败，请检查后端是否正常运行')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
textarea {
  font-family: monospace;
}
</style>
