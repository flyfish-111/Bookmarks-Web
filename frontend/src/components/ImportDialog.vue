<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { bookmarksApi } from '../api'
import { useBookmarksStore } from '../stores/bookmarks'
import { useMetaStore } from '../stores/meta'

const visible = defineModel<boolean>({ default: false })
const store = useBookmarksStore()
const fileInput = ref<HTMLInputElement | null>(null)
const importing = ref(false)

function pickFile() {
  fileInput.value?.click()
}

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  importing.value = true
  try {
    const text = await file.text()
    const result = await bookmarksApi.importFile(text)
    ElMessage.success(`导入完成：新增 ${result.imported} 条，跳过 ${result.skipped} 条（已存在）`)
    await store.load()
    useMetaStore().loadAll()
    visible.value = false
  } catch {
    // 错误已由拦截器提示
  } finally {
    importing.value = false
    input.value = ''
  }
}
</script>

<template>
  <el-dialog v-model="visible" title="导入收藏" width="520px" append-to-body>
    <p class="tip">支持以下文件类型（自动识别，按网址去重）：</p>
    <ul class="formats">
      <li><b>JSON</b> —— 本应用导出的备份（含正文、分类、标签、星标）</li>
      <li><b>HTML</b> —— 浏览器书签导出文件（Chrome / Edge）</li>
      <li><b>TXT</b> —— 纯文本网址列表，每行一个网址（可带标题）</li>
    </ul>
    <p class="tip">选择文件后会自动抓取每个网址的页面信息（标题、正文）。</p>
    <div class="actions">
      <el-button type="primary" :loading="importing" @click="pickFile">
        {{ importing ? '正在导入并抓取网页信息…' : '选择文件并导入' }}
      </el-button>
    </div>
    <input ref="fileInput" type="file" accept=".json,.html,.htm,.txt" style="display: none" @change="onFileChange" />
  </el-dialog>
</template>

<style scoped>
.tip {
  color: #8c7c6c;
  font-size: 13px;
  margin: 0 0 8px;
}
.formats {
  margin: 0 0 12px;
  padding-left: 20px;
  color: #5c4f42;
  font-size: 13px;
  line-height: 2;
}
.actions {
  text-align: center;
}
</style>
