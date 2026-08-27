<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useBookmarksStore } from '../stores/bookmarks'
import { useMetaStore } from '../stores/meta'

const visible = defineModel<boolean>({ default: false })
const store = useBookmarksStore()
const meta = useMetaStore()

const url = ref('')
const categoryName = ref('')
const tags = ref<string[]>([])
const submitting = ref(false)

async function submit() {
  const u = url.value.trim()
  if (!u) {
    ElMessage.warning('请输入网址')
    return
  }
  submitting.value = true
  try {
    const bm = await store.create({ url: u, category_name: categoryName.value.trim() || null, tags: tags.value })
    ElMessage.success(`已收藏：${bm.title}`)
    visible.value = false
    url.value = ''
    categoryName.value = ''
    tags.value = []
  } catch {
    // 错误已在拦截器提示
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog v-model="visible" title="添加收藏" width="520px" :close-on-click-modal="false" append-to-body>
    <el-form label-position="top" @submit.prevent>
      <el-form-item label="网址">
        <el-input
          v-model="url"
          placeholder="粘贴网址，如 https://example.com/article"
          clearable
          @keyup.enter="submit"
        />
      </el-form-item>
      <el-form-item label="分类">
        <el-select
          v-model="categoryName"
          placeholder="选择或输入分类（可选）"
          clearable
          filterable
          allow-create
          default-first-option
          style="width: 100%"
        >
          <el-option v-for="c in meta.categories" :key="c.id" :label="c.name" :value="c.name" />
        </el-select>
      </el-form-item>
      <el-form-item label="标签">
        <el-select
          v-model="tags"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="输入或选择标签，回车新建"
          style="width: 100%"
        >
          <el-option v-for="t in meta.tags" :key="t.id" :label="t.name" :value="t.name" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">收藏</el-button>
    </template>
  </el-dialog>
</template>
