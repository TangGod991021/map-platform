<template>
  <div>
    <div class="page-card release-hero">
      <div>
        <div class="page-heading">发布管理</div>
        <div class="muted release-desc">
          发布会把当前“已发布”的标签、路线、区域写成静态快照，供地图 H5 读取。
          快照输出到 <code>apps/map-web/data/map.json</code>，同时写入版本清单。
        </div>
      </div>
      <el-button type="success" size="large" :loading="publishing" @click="publish">
        发布地图快照
      </el-button>
    </div>

    <div class="page-card">
      <div class="toolbar">
        <div class="section-title">发布记录</div>
        <div class="toolbar-spacer"></div>
        <el-button @click="load">刷新</el-button>
      </div>

      <el-table v-loading="loading" :data="releases" border>
        <el-table-column prop="version" label="版本" width="90">
          <template #default="{ row }">v{{ row.version }}</template>
        </el-table-column>
        <el-table-column prop="note" label="发布说明" min-width="160" show-overflow-tooltip />
        <el-table-column prop="created_by" label="发布人" width="110" />
        <el-table-column label="发布时间" width="190">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="snapshot_path" label="快照路径" min-width="260" show-overflow-tooltip />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { listReleases, publishMap } from '@/api/release'

const releases = ref([])
const loading = ref(false)
const publishing = ref(false)

const formatTime = (value) => {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 19)
}

const load = async () => {
  loading.value = true
  try {
    const res = await listReleases()
    releases.value = res.data || []
  } finally {
    loading.value = false
  }
}

const publish = async () => {
  let result
  try {
    result = await ElMessageBox.prompt('请输入本次发布说明', '发布地图快照', {
      inputPlaceholder: '例如：新增甲秀楼、喷水池点位',
      confirmButtonText: '发布',
      cancelButtonText: '取消'
    })
  } catch (error) {
    return
  }
  publishing.value = true
  try {
    const res = await publishMap({ note: result.value || '后台发布' })
    const version = res.data?.version
    ElMessage.success(`发布成功：v${version}`)
    await load()
  } finally {
    publishing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.release-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 16px;
}

.page-heading {
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 4px;
}

.release-desc {
  max-width: 720px;
  font-size: 13px;
  line-height: 1.7;
}

.section-title {
  font-size: 15px;
  font-weight: 700;
}

code {
  background: #f1f5f9;
  padding: 1px 5px;
  border-radius: 4px;
}
</style>
