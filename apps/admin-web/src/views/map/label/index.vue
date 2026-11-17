<template>
  <div class="page-card">
    <div class="toolbar">
      <div>
        <div class="page-heading">标签管理</div>
        <div class="muted">维护地图点位、分类、坐标与详情内容</div>
      </div>
      <div class="toolbar-spacer"></div>
      <el-button type="primary" @click="openCreate">新增标签</el-button>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-form inline class="filter-form" @submit.prevent>
      <el-form-item label="分类">
        <el-select v-model="filter.categoryId" clearable placeholder="全部分类" style="width: 150px">
          <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filter.status" clearable placeholder="全部状态" style="width: 140px">
          <el-option label="草稿" value="0" />
          <el-option label="已发布" value="1" />
          <el-option label="已下线" value="2" />
        </el-select>
      </el-form-item>
      <el-form-item label="关键词">
        <el-input v-model="filter.keyword" clearable placeholder="名称 / 地址 / 摘要" style="width: 220px" @keyup.enter="search" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="search">搜索</el-button>
        <el-button @click="resetFilter">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="ID" width="65" />
      <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip />
      <el-table-column prop="category_code" label="分类" width="100" />
      <el-table-column label="坐标" width="190">
        <template #default="{ row }">
          <span class="mono">{{ Number(row.lng).toFixed(5) }}, {{ Number(row.lat).toFixed(5) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="sort" label="排序" width="75" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pageNo"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @current-change="load"
        @size-change="onSizeChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑标签' : '新增标签'" width="900px" top="5vh">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="名称" prop="name">
              <el-input v-model="form.name" placeholder="甲秀楼" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="category_id">
              <el-select v-model="form.category_id" placeholder="请选择分类" style="width: 100%">
                <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="副标题">
          <el-input v-model="form.subtitle" placeholder="一句话副标题" />
        </el-form-item>

        <el-form-item label="坐标" prop="lng">
          <MapPicker v-model="coord" />
        </el-form-item>

        <el-form-item label="地址">
          <el-input v-model="form.address" placeholder="南明区翠微巷8号" />
        </el-form-item>

        <el-form-item label="摘要">
          <el-input v-model="form.summary" type="textarea" :rows="2" maxlength="500" show-word-limit />
        </el-form-item>

        <el-form-item label="详情正文">
          <RichEditor v-model="form.description" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="封面 URL">
              <el-input v-model="form.cover_image" placeholder="/profile/xxx.jpg" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="form.phone" placeholder="可选" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="图片 URL">
          <el-input v-model="form.imagesText" type="textarea" :rows="2" placeholder="每行一个图片 URL" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="标签">
              <el-input v-model="form.tagsText" placeholder="逗号分隔，如：夜景,亲子" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="营业时间">
              <el-input v-model="form.business_hours" placeholder="09:00-22:00" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="form.sort" :min="0" :max="9999" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-radio-group v-model="form.status">
                <el-radio value="0">草稿</el-radio>
                <el-radio value="1">已发布</el-radio>
                <el-radio value="2">已下线</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import MapPicker from '@/components/MapPicker.vue'
import RichEditor from '@/components/RichEditor.vue'
import { listCategories } from '@/api/category'
import { createLabel, deleteLabel, listLabels, updateLabel } from '@/api/label'

const categories = ref([])
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()

const pageNo = ref(1)
const pageSize = ref(20)
const filter = reactive({
  categoryId: null,
  status: '',
  keyword: ''
})

const emptyForm = () => ({
  name: '',
  category_id: null,
  subtitle: '',
  lng: 106.6302,
  lat: 26.647,
  address: '',
  summary: '',
  description: '',
  cover_image: '',
  imagesText: '',
  tagsText: '',
  phone: '',
  business_hours: '',
  sort: 0,
  status: '0'
})

const form = reactive(emptyForm())

const coord = computed({
  get: () => ({ lng: Number(form.lng) || 0, lat: Number(form.lat) || 0 }),
  set: (value) => {
    form.lng = value.lng
    form.lat = value.lat
  }
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  lng: [{ required: true, message: '请选择坐标', trigger: 'change' }]
}

const statusLabel = (status) =>
  ({ '0': '草稿', '1': '已发布', '2': '已下线' })[status] || status
const statusType = (status) =>
  ({ '0': 'info', '1': 'success', '2': 'warning' })[status] || 'info'

const loadCategories = async () => {
  const res = await listCategories()
  categories.value = res.data || []
}

const load = async () => {
  loading.value = true
  try {
    const res = await listLabels({
      category_id: filter.categoryId || undefined,
      status: filter.status || undefined,
      keyword: filter.keyword || undefined,
      page_no: pageNo.value,
      page_size: pageSize.value
    })
    rows.value = res.rows || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

const search = () => {
  pageNo.value = 1
  load()
}

const resetFilter = () => {
  filter.categoryId = null
  filter.status = ''
  filter.keyword = ''
  pageNo.value = 1
  load()
}

const onSizeChange = () => {
  pageNo.value = 1
  load()
}

const openCreate = () => {
  editingId.value = null
  Object.assign(form, emptyForm())
  form.category_id = categories.value[0]?.id || null
  dialogVisible.value = true
}

const openEdit = (row) => {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    category_id: row.category_id,
    subtitle: row.subtitle || '',
    lng: row.lng,
    lat: row.lat,
    address: row.address || '',
    summary: row.summary || '',
    description: row.description || '',
    cover_image: row.cover_image || '',
    imagesText: (row.images || []).join('\n'),
    tagsText: (row.tags || []).join(','),
    phone: row.phone || '',
    business_hours: row.business_hours || '',
    sort: row.sort || 0,
    status: row.status || '0'
  })
  dialogVisible.value = true
}

const splitLines = (text) =>
  String(text || '')
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)

const splitComma = (text) =>
  String(text || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

const save = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = {
      name: form.name,
      category_id: form.category_id,
      subtitle: form.subtitle,
      lng: Number(form.lng),
      lat: Number(form.lat),
      address: form.address,
      summary: form.summary,
      description: form.description,
      cover_image: form.cover_image,
      images: splitLines(form.imagesText),
      tags: splitComma(form.tagsText),
      phone: form.phone,
      business_hours: form.business_hours,
      sort: Number(form.sort) || 0,
      status: form.status
    }
    if (editingId.value) {
      await updateLabel(editingId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await createLabel(payload)
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
    await ElMessageBox.confirm(`确认删除标签「${row.name}」？`, '提示', { type: 'warning' })
  } catch (error) {
    return
  }
  await deleteLabel(row.id)
  ElMessage.success('删除成功')
  await load()
}

onMounted(async () => {
  await loadCategories()
  await load()
})
</script>

<style scoped>
.page-heading {
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 4px;
}

.filter-form {
  margin-bottom: 6px;
}

.mono {
  font-family: monospace;
  font-size: 12px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}
</style>
