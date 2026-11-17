<template>
  <div>
    <el-row :gutter="16">
      <el-col v-for="card in cards" :key="card.key" :xs="12" :sm="8" :md="4">
        <div class="stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ summary[card.key] ?? 0 }}</div>
        </div>
      </el-col>
    </el-row>

    <div class="page-card quick-card">
      <div class="quick-title">快捷入口</div>
      <div class="quick-links">
        <el-button @click="router.push('/map/category')">分类管理</el-button>
        <el-button type="primary" @click="router.push('/map/label')">标签管理</el-button>
        <el-button type="success" @click="router.push('/map/release')">发布地图</el-button>
      </div>
      <div class="muted quick-tip">
        发布后地图 H5 会读取 <code>apps/map-web/data/map.json</code>，也可通过
        <code>/map-api/v1/bootstrap</code> 获取实时数据。
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'

import { getSummary } from '@/api/release'

const router = useRouter()
const summary = reactive({
  categories: 0,
  labels: 0,
  published: 0,
  routes: 0,
  areas: 0,
  releases: 0
})

const cards = [
  { key: 'categories', label: '分类' },
  { key: 'labels', label: '标签' },
  { key: 'published', label: '已发布' },
  { key: 'routes', label: '路线' },
  { key: 'areas', label: '区域' },
  { key: 'releases', label: '发布版本' }
]

onMounted(async () => {
  const res = await getSummary()
  Object.assign(summary, res.data)
})
</script>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
}

.stat-label {
  font-size: 12px;
  color: #64748b;
}

.stat-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
}

.quick-card {
  margin-top: 6px;
}

.quick-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 12px;
}

.quick-links {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.quick-tip {
  margin-top: 14px;
  font-size: 12px;
  line-height: 1.7;
}

code {
  background: #f1f5f9;
  padding: 1px 5px;
  border-radius: 4px;
}
</style>
