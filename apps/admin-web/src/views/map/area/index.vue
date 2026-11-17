<template>
  <div class="page-card">
    <div class="toolbar">
      <div>
        <div class="page-heading">区域管理</div>
        <div class="muted">维护地图上的面状区域（多边形），发布后由地图 H5 展示</div>
      </div>
      <div class="toolbar-spacer"></div>
      <el-button type="primary" @click="openCreate">新增区域</el-button>
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
      <el-table-column label="顶点数" width="85">
        <template #default="{ row }">{{ (row.polygon || []).length }}</template>
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
      :title="editingId ? '编辑区域' : '新增区域'"
      width="760px"
      append-to-body
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="如：甲秀楼景区范围" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="form.color" />
          <span class="muted color-text">{{ form.color }}</span>
        </el-form-item>
        <el-form-item label="区域">
          <MapPathEditor v-model="form.polygon" mode="area" :color="form.color" />
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

import { createArea, deleteArea, listAreas, updateArea } from '@/api/area'
import MapPathEditor from '@/components/MapPathEditor.vue'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)
const formRef = ref()

const emptyForm = () => ({
  name: '',
  color: '#8b5cf6',
  description: '',
  polygon: [],
  sort: 0,
  status: '0'
})

const form = reactive(emptyForm())

const rules = {
  name: [{ required: true, message: '请输入区域名称', trigger: 'blur' }]
}

const load = async () => {
  loading.value = true
  try {
    const res = await listAreas()
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
    color: row.color || '#8b5cf6',
    description: row.description || '',
    polygon: (row.polygon || []).map((p) => [Number(p[0]), Number(p[1])]),
    sort: row.sort ?? 0,
    status: row.status ?? '0'
  })
  editingId.value = row.id
  dialogVisible.value = true
}

const save = async () => {
  await formRef.value.validate()
  if (form.polygon.length < 3) {
    ElMessage.warning('区域至少需要 3 个顶点，请先在地图上绘制')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateArea(editingId.value, { ...form })
    } else {
      await createArea({ ...form })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

const remove = async (row) => {
  await ElMessageBox.confirm(`确定删除区域「${row.name}」？`, '提示', { type: 'warning' })
  await deleteArea(row.id)
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
