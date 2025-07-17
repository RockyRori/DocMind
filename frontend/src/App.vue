<!-- src/App.vue -->
<template>
  <div class="container mx-auto p-4 space-y-8">
    <!-- 上传区域 -->
    <UploadPDF />

    <hr />

    <!-- 文档列表区域 -->
    <DocumentList />
  </div>
</template>

<script setup>
import UploadPDF from '@/components/UploadPDF.vue'
import DocumentList from '@/components/DocumentList.vue'
</script>

<style>
.container {
  max-width: 800px;
}
</style>
