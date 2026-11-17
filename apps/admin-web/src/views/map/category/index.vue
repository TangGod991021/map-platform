<template>
  <div class="page-card">
    <div class="toolbar">
      <div>
        <div class="page-heading">分类管理</div>
        <div class="muted">管理景点、美食、特产、非遗等地图分类</div>
      </div>
      <div class="toolbar-spacer"></div>
      <el-button type="primary" @click="openCreate">新增分类</el-button>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-table v-loading="loading" :data="list" border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="name" label="名称" width="120" />
      <el-table-column label="颜色" width="100">
        <template #default="{ row }">
          <span class="color-swatch" :style="{ background: row.color }"></span>
          <span class="muted">{{ row.color }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="icon" label="图标 URL" min-width="180" show-overflow-tooltip />
      <el-table-column prop="sort" label="排序" width="80" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '0' ? 'success' : 'info'">
            {{ row.status === '0' ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑分类' : '新增分类'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="form.code" placeholder="scenic / food / specialty / heritage" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="景点" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="form.color" />
          <span class="muted color-text">{{ form.color }}</span>
        </el-form-item>
        <el-form-item label="图标 URL">
          <el-input v-model="form.icon" placeholder="/profile/xxx.png" />
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

import { createCategory, deleteCategory, listCategories, updateCategory } from '@/api/category'

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()

const emptyForm = () => ({
  code: '',
  name: '',
  color: '#00e5ff',
  icon: '',
  sort: 0,
  status: '0'
})

const form = reactive(emptyForm())

const rules = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

const load = async () => {
  loading.value = true
  try {
    const res = await listCategories()
    list.value = res.data || []
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingId.value = null
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

const openEdit = (row) => {
  editingId.value = row.id
  Object.assign(form, {
    code: row.code,
    name: row.name,
    color: row.color,
    icon: row.icon,
    sort: row.sort,
    status: row.status
  })
  dialogVisible.value = true
}

const save = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    if (editingId.value) {
      await updateCategory(editingId.value, { ...form })
      ElMessage.success('修改成功')
    } else {
      await createCategory({ ...form })
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除分类「${row.name}」？`, '提示', { type: 'warning' })
  } catch (error) {
    return
  }
  await deleteCategory(row.id)
  ElMessage.success('删除成功')
  await load()
}

onMounted(load)
</script>

<style scoped>
.page-heading {
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 4px;
}

.color-swatch {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
  border: 1px solid rgba(15, 23, 42, 0.12);
}

.color-text {
  margin-left: 10px;
  font-size: 12px;
}
</style>
