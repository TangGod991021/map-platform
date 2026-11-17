<template>
  <div class="page-card">
    <div class="toolbar">
      <div>
        <div class="page-heading">路线管理</div>
        <div class="muted">维护地图上的推荐路线（折线），发布后由地图 H5 展示</div>
      </div>
      <div class="toolbar-spacer"></div>
      <el-button type="primary" @click="openCreate">新增路线</el-button>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-table v-loading="loading" :data="list" border>
      <el-table-column prop="id" label="ID" width="65" />
      <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
      <el-table-column label="颜色" width="110">
        <template #default="{ row }">
          <span class="color-swatch" :style="{ background: row.color }"></span>
          <span class="muted">{{ row.color }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="weight" label="线宽" width="75" />
      <el-table-column label="顶点数" width="85">
        <template #default="{ row }">{{ (row.points || []).length }}</template>
      </el-table-column>
      <el-table-column prop="description" label="说明" min-width="180" show-overflow-tooltip />
      <el-table-column prop="sort" label="排序" width="75" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '0' ? 'success' : 'info'">
            {{ row.status === '0' ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑路线' : '新增路线'"
      width="760px"
      append-to-body
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="如：南明河漫步路线" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="form.color" />
          <span class="muted color-text">{{ form.color }}</span>
        </el-form-item>
        <el-form-item label="线宽">
          <el-input-number v-model="form.weight" :min="1" :max="12" />
        </el-form-item>
        <el-form-item label="路线">
          <MapPathEditor v-model="form.points" mode="route" :color="form.color" :weight="form.weight" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="0">启用</el-radio>
            <el-radio value="1">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { createRoute, deleteRoute, listRoutes, updateRoute } from '@/api/route'
import MapPathEditor from '@/components/MapPathEditor.vue'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)
const formRef = ref()

const emptyForm = () => ({
  name: '',
  color: '#00e5ff',
  weight: 4,
  description: '',
  points: [],
  sort: 0,
  status: '0'
})

const form = reactive(emptyForm())

const rules = {
  name: [{ required: true, message: '请输入路线名称', trigger: 'blur' }]
}

const load = async () => {
  loading.value = true
  try {
    const res = await listRoutes()
    list.value = res.data || []
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, emptyForm())
  editingId.value = null
  dialogVisible.value = true
}

const openEdit = (row) => {
  Object.assign(form, {
    name: row.name,
    color: row.color || '#00e5ff',
    weight: row.weight || 4,
    description: row.description || '',
    points: (row.points || []).map((p) => [Number(p[0]), Number(p[1])]),
    sort: row.sort ?? 0,
    status: row.status ?? '0'
  })
  editingId.value = row.id
  dialogVisible.value = true
}

const save = async () => {
  await formRef.value.validate()
  if (form.points.length < 2) {
    ElMessage.warning('路线至少需要 2 个顶点，请先在地图上绘制')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateRoute(editingId.value, { ...form })
    } else {
      await createRoute({ ...form })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

const remove = async (row) => {
  await ElMessageBox.confirm(`确定删除路线「${row.name}」？`, '提示', { type: 'warning' })
  await deleteRoute(row.id)
  ElMessage.success('删除成功')
  await load()
}

onMounted(load)
</script>

<style scoped>
.color-swatch {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 3px;
  margin-right: 6px;
  vertical-align: middle;
}

.color-text {
  margin-left: 10px;
  font-size: 12px;
}
</style>
