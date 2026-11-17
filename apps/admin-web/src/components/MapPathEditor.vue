<template>
  <div class="map-path-editor">
    <el-button @click="open">{{ mode === 'route' ? '地图绘制路线' : '地图绘制区域' }}</el-button>
    <span class="muted point-text">{{ (modelValue || []).length }} 个顶点</span>

    <el-dialog
      v-model="visible"
      :title="mode === 'route' ? '绘制路线' : '绘制区域'"
      width="820px"
      append-to-body
      @closed="onClosed"
    >
      <el-alert
        v-if="!tk"
        title="未配置 VITE_TIANDITU_TK，无法使用地图绘制，请在 apps/admin-web/.env 中配置后重启"
        type="warning"
        :closable="false"
        show-icon
        class="tip"
      />

      <div v-if="tk" class="editor-toolbar">
        <el-button size="small" @click="undo" :disabled="!draft.length">撤销上一点</el-button>
        <el-button size="small" @click="clearDraft" :disabled="!draft.length">清空</el-button>
        <span class="muted hint">
          单击地图添加顶点{{ mode === 'area' ? '（至少 3 个点）' : '（至少 2 个点）' }}
        </span>
      </div>

      <div v-if="tk" ref="mapRef" class="editor-map"></div>

      <template #footer>
        <span class="footer-count muted">当前 {{ draft.length }} 个顶点</span>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="confirm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  mode: {
    type: String,
    default: 'route' // route | area
  },
  color: {
    type: String,
    default: '#00e5ff'
  },
  weight: {
    type: Number,
    default: 4
  }
})
const emit = defineEmits(['update:modelValue'])

const tk = import.meta.env.VITE_TIANDITU_TK || ''
const visible = ref(false)
const mapRef = ref()
const draft = ref([])

let map = null
let overlays = []

const loadScript = () =>
  new Promise((resolve, reject) => {
    if (window.T) return resolve()
    const existing = document.querySelector('script[data-tianditu]')
    if (existing) {
      existing.addEventListener('load', resolve)
      existing.addEventListener('error', reject)
      return
    }
    const script = document.createElement('script')
    script.dataset.tianditu = '1'
    script.src = `https://api.tianditu.gov.cn/api?v=4.0&tk=${encodeURIComponent(tk)}`
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })

const clearOverlays = () => {
  if (!map) return
  overlays.forEach((overlay) => map.removeOverLay(overlay))
  overlays = []
}

const render = () => {
  clearOverlays()
  if (!map || !draft.value.length) return

  const path = draft.value.map((p) => new window.T.LngLat(p[0], p[1]))
  if (draft.value.length >= 2) {
    if (props.mode === 'area') {
      overlays.push(
        new window.T.Polygon(path, {
          color: props.color,
          weight: 2,
          fillColor: props.color,
          fillOpacity: 0.3
        })
      )
    } else {
      overlays.push(
        new window.T.Polyline(path, {
          color: props.color,
          weight: props.weight,
          opacity: 0.95
        })
      )
    }
  }

  draft.value.forEach((p) => {
    overlays.push(
      new window.T.Circle(new window.T.LngLat(p[0], p[1]), 80, {
        color: props.color,
        weight: 1,
        fillColor: props.color,
        fillOpacity: 0.9
      })
    )
  })

  overlays.forEach((overlay) => map.addOverLay(overlay))
}

const onMapClick = (e) => {
  if (!visible.value) return
  draft.value.push([
    Number(Number(e.lnglat.lng).toFixed(6)),
    Number(Number(e.lnglat.lat).toFixed(6))
  ])
  render()
}

const initMap = () => {
  if (!mapRef.value) return
  if (!map) {
    map = new window.T.Map(mapRef.value)
    map.enableScrollWheelZoom(true)
    map.addEventListener('click', onMapClick)
  }
  const first = draft.value[0]
  const center = first
    ? new window.T.LngLat(first[0], first[1])
    : new window.T.LngLat(106.6302, 26.647)
  map.centerAndZoom(center, draft.value.length ? 12 : 10)
  if (map.checkResize) map.checkResize()
  render()
}

const open = async () => {
  draft.value = (props.modelValue || []).map((p) => [Number(p[0]), Number(p[1])])
  visible.value = true
  if (!tk) return
  await nextTick()
  try {
    await loadScript()
    await new Promise((resolve) => setTimeout(resolve, 380))
    await nextTick()
    initMap()
  } catch (error) {
    ElMessage.error('天地图加载失败，请检查 VITE_TIANDITU_TK 与域名白名单')
  }
}

const undo = () => {
  draft.value.pop()
  render()
}

const clearDraft = () => {
  draft.value = []
  render()
}

const confirm = () => {
  const minimum = props.mode === 'area' ? 3 : 2
  if (draft.value.length < minimum) {
    ElMessage.warning(
      props.mode === 'area' ? '区域至少需要 3 个顶点' : '路线至少需要 2 个顶点'
    )
    return
  }
  emit(
    'update:modelValue',
    draft.value.map((p) => [p[0], p[1]])
  )
  visible.value = false
}

const onClosed = () => {
  clearOverlays()
}

watch(
  () => [props.color, props.weight, props.mode],
  () => {
    if (visible.value) render()
  }
)
</script>

<style scoped>
.map-path-editor {
  display: flex;
  align-items: center;
  gap: 10px;
}

.point-text {
  font-size: 12px;
}

.tip {
  margin-bottom: 12px;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.hint {
  font-size: 12px;
}

.editor-map {
  width: 100%;
  height: 440px;
  border-radius: 8px;
  overflow: hidden;
  background: #0b1220;
}

.footer-count {
  margin-right: 12px;
  font-size: 12px;
}
</style>
