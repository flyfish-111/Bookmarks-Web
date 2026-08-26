<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { Bookmark } from '../types'
import { useBookmarksStore } from '../stores/bookmarks'
import { useMetaStore } from '../stores/meta'

const props = defineProps<{ bookmark: Bookmark }>()
const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{ saved: [bookmark: Bookmark] }>()

const store = useBookmarksStore()
const meta = useMetaStore()

const title = ref('')
const description = ref('')
const categoryName = ref('')
const tags = ref<string[]>([])
const isFavorite = ref(false)
const submitting = ref(false)

watch(visible, (isOpen) => {
  if (!isOpen) return
  title.value = props.bookmark.title
  description.value = props.bookmark.description
  categoryName.value = props.bookmark.category?.name ?? ''
  tags.value = props.bookmark.tags.map((t) => t.name)
  isFavorite.value = props.bookmark.is_favorite
})

async function submit() {
  submitting.value = true
  try {
    const updated = await store.update(props.bookmark.id, {
      title: title.value,
      description: description.value,
      category_name: (categoryName.value ?? '').trim() || null,
      tags: tags.value,
      is_favorite: isFavorite.value,
    })
    ElMessage.success('已保存')
    visible.value = false
    emit('saved', updated)
  } catch {
    // 错误已在拦截器提示
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog v-model="visible" title="编辑收藏" width="520px" :close-on-click-modal="false" append-to-body>
    <el-form label-position="top">
      <el-form-item label="标题">
        <el-input v-model="title" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="description" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item label="分类">
        <el-select
          v-model="categoryName"
          placeholder="选择或输入分类"
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
      <el-form-item>
        <el-checkbox v-model="isFavorite">标为星标</el-checkbox>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>
