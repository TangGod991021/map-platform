<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-brand">
        <div class="mark"></div>
        <div>
          <div class="title">黔山漫游 · 管理后台</div>
          <div class="subtitle">QIANSHAN MANYOU ADMIN</div>
        </div>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" size="large" placeholder="请输入账号" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            size="large"
            show-password
            placeholder="请输入密码"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="onSubmit">
          登录
        </el-button>
      </el-form>

      <div class="tips">默认账号：admin / admin123（生产环境请修改）</div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({
  username: 'admin',
  password: 'admin123'
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const onSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  loading.value = true
  try {
    await auth.login(form)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(60% 80% at 20% 10%, rgba(0, 229, 255, 0.12), transparent),
    radial-gradient(50% 60% at 90% 90%, rgba(139, 92, 246, 0.14), transparent),
    #0b1224;
}

.login-card {
  width: 380px;
  padding: 30px 28px 22px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.mark {
  width: 14px;
  height: 14px;
  background: #00b8d4;
  transform: rotate(45deg);
  box-shadow: 0 0 16px rgba(0, 184, 212, 0.6);
}

.title {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.subtitle {
  margin-top: 2px;
  font-size: 10px;
  letter-spacing: 2px;
  color: #64748b;
}

.login-btn {
  width: 100%;
  margin-top: 4px;
}

.tips {
  margin-top: 16px;
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
}
</style>
