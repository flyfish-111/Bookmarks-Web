<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const mode = ref<'login' | 'register'>('login')
const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function submit() {
  if (!form.username.trim() || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(form.username.trim(), form.password)
    } else {
      await auth.register(form.username.trim(), form.password)
    }
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.push(redirect)
  } catch {
    // 错误提示已由 axios 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card" shadow="never">
      <div class="brand">📌 网址收藏夹</div>
      <el-tabs v-model="mode" class="tabs" stretch>
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>
      <el-input
        v-model="form.username"
        placeholder="用户名"
        size="large"
        clearable
        class="field"
        @keyup.enter="submit"
      />
      <el-input
        v-model="form.password"
        type="password"
        placeholder="密码"
        size="large"
        show-password
        class="field"
        @keyup.enter="submit"
      />
      <el-button type="primary" size="large" class="submit" :loading="loading" @click="submit">
        {{ mode === 'login' ? '登录' : '注册并登录' }}
      </el-button>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7f2ec;
}
.login-card {
  width: 360px;
  border: 1px solid #ece2d6;
  border-radius: 14px;
}
.brand {
  text-align: center;
  font-size: 20px;
  font-weight: 700;
  color: #403931;
  margin-bottom: 12px;
}
.tabs {
  margin-bottom: 8px;
}
.field {
  margin-bottom: 14px;
}
.submit {
  width: 100%;
}
</style>
