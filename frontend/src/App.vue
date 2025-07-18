<!-- src/App.vue -->
<template>
  <div class="container mx-auto p-4 space-y-8">
    <!-- 文档列表区域 -->
    <DocumentList />
  </div>
</template>

<script setup>
import DocumentList from '@/components/DocumentList.vue'
</script>

<style>
.container {
  max-width: 800px;
}
</style>
