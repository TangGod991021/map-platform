<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="brand">
        <div class="brand-mark"></div>
        <div>
          <div class="brand-title">黔山漫游</div>
          <div class="brand-sub">QIANSHAN MANYOU ADMIN</div>
        </div>
      </div>

      <el-menu
        :default-active="route.path"
        router
        class="menu"
        background-color="#0f172a"
        text-color="#94a3b8"
        active-text-color="#00e5ff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-sub-menu index="/map">
          <template #title>
            <el-icon><MapLocation /></el-icon>
            <span>地图管理</span>
          </template>
          <el-menu-item index="/map/category">分类管理</el-menu-item>
          <el-menu-item index="/map/label">标签管理</el-menu-item>
          <el-menu-item index="/map/release">发布管理</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="page-title">{{ route.meta.title || '地图管理' }}</div>
        <el-dropdown trigger="click" @command="onCommand">
          <span class="user">{{ auth.nickname }} <el-icon><ArrowDown /></el-icon></span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

onMounted(async () => {
  if (!auth.user) {
    try {
      await auth.fetchInfo()
    } catch (error) {
      console.warn(error)
    }
  }
})

const onCommand = (command) => {
  if (command === 'logout') {
    auth.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
}

.aside {
  background: #0f172a;
  display: flex;
  flex-direction: column;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 18px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.brand-mark {
  width: 12px;
  height: 12px;
  background: #00e5ff;
  transform: rotate(45deg);
  box-shadow: 0 0 14px #00e5ff;
}

.brand-title {
  color: #f8fafc;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
}

.brand-sub {
  margin-top: 2px;
  color: #475569;
  font-size: 10px;
  letter-spacing: 1px;
}

.menu {
  border-right: none;
  flex: 1;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.page-title {
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
}

.user {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #334155;
  cursor: pointer;
  outline: none;
}

.main {
  padding: 18px;
  background: #f5f7fb;
  overflow-y: auto;
}
</style>
