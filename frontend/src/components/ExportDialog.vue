<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { bookmarksApi } from '../api'
import { useMetaStore } from '../stores/meta'

const visible = defineModel<boolean>({ default: false })
const meta = useMetaStore()

const scope = ref<'all' | 'category' | 'tag'>('all')
const categoryId = ref<number | null>(null)
const tagId = ref<number | null>(null)
const format = ref<'json' | 'html'>('json')
const exporting = ref(false)

async function doExport() {
  if (scope.value === 'category' && categoryId.value == null) {
    ElMessage.warning('请选择要导出的分类')
    return
  }
  if (scope.value === 'tag' && tagId.value == null) {
    ElMessage.warning('请选择要导出的标签')
    return
  }
  exporting.value = true
  try {
    const params: { category_id?: number; tag_id?: number } = {}
    if (scope.value === 'category') params.category_id = categoryId.value!
    if (scope.value === 'tag') params.tag_id = tagId.value!
    await bookmarksApi.exportFile(format.value, params)
    ElMessage.success('导出完成')
    visible.value = false
  } catch {
    // 错误已由拦截器提示
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <el-dialog v-model="visible" title="导出收藏" width="480px" append-to-body>
    <el-form label-position="top">
      <el-form-item label="导出范围">
        <el-radio-group v-model="scope">
          <el-radio value="all">全部收藏</el-radio>
          <el-radio value="category">指定分类</el-radio>
          <el-radio value="tag">指定标签</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item v-if="scope === 'category'" label="选择分类">
        <el-select v-model="categoryId" placeholder="选择要导出的分类" style="width: 100%">
          <el-option v-for="c in meta.categories" :key="c.id" :label="`${c.name}（${c.count}）`" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="scope === 'tag'" label="选择标签">
        <el-select v-model="tagId" placeholder="选择要导出的标签" style="width: 100%">
          <el-option v-for="t in meta.tags" :key="t.id" :label="`${t.name}（${t.count}）`" :value="t.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="导出格式">
        <el-radio-group v-model="format">
          <el-radio value="json">JSON（完整备份，可再导入）</el-radio>
          <el-radio value="html">HTML（可导入浏览器）</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="exporting" @click="doExport">导出</el-button>
    </template>
  </el-dialog>
</template>
