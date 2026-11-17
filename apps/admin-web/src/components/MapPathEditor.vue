<template>
  <div class="map-path-editor">
    <el-button @click="open">{{ mode === 'route' ? '地图绘制路线' : '地图绘制区域' }}</el-button>
    <span class="muted point-text">{{ (modelValue || []).length }} 个顶点</span>

    <el-dialog
      v-model="visible"
      :title="mode === 'route' ? '绘制路线' : '绘制区域'"
      width="820px"
      append-to-body
      @opened="onOpened"
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
        <el-button size="small" @click="toggleEdit" :disabled="draft.length < 2">
          {{ editing ? '结束编辑' : '编辑顶点' }}
        </el-button>
        <span class="muted hint">
          单击地图添加顶点{{ mode === 'area' ? '（至少 3 个点）' : '（至少 2 个点）' }}；编辑时可拖动顶点
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
import L from 'leaflet'
import '@geoman-io/leaflet-geoman-free'
import 'leaflet/dist/leaflet.css'
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css'

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
const editing = ref(false)

let map = null
let shapeLayer = null
let vertexLayer = null

// 天地图卫星影像 WMTS；Leaflet 占位符为 {z} / {x} / {y}
const tiandituTileUrl = () =>
  'https://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0' +
  '&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles' +
  `&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${encodeURIComponent(tk)}`

const stopEdit = () => {
  if (shapeLayer && shapeLayer.pm && shapeLayer.pm.enabled()) shapeLayer.pm.disable()
  editing.value = false
}

const removeLayers = () => {
  stopEdit()
  if (shapeLayer && map) {
    map.removeLayer(shapeLayer)
  }
  if (vertexLayer && map) {
    map.removeLayer(vertexLayer)
  }
  shapeLayer = null
  vertexLayer = null
}

const syncFromLayer = () => {
  if (!shapeLayer) return
  let latlngs = shapeLayer.getLatLngs()
  if (props.mode === 'area' && Array.isArray(latlngs[0])) latlngs = latlngs[0]
  const points = latlngs.map((p) => [
    Number(p.lng.toFixed(6)),
    Number(p.lat.toFixed(6))
  ])
  // GeoJSON/Leaflet 多边形会首尾闭合，转回顶点数组时去掉重复的末点
  if (
    points.length > 1 &&
    points[0][0] === points[points.length - 1][0] &&
    points[0][1] === points[points.length - 1][1]
  ) {
    points.pop()
  }
  draft.value = points
}

const render = () => {
  if (!map) return
  removeLayers()
  if (!draft.value.length) return

  const latlngs = draft.value.map((p) => [p[1], p[0]])
  if (draft.value.length >= 2) {
    const options = {
      color: props.color,
      weight: props.mode === 'area' ? 2 : props.weight,
      opacity: 0.95,
      bubblingMouseEvents: false
    }
    if (props.mode === 'area') {
      options.fillColor = props.color
      options.fillOpacity = 0.18
      shapeLayer = L.polygon(latlngs, options)
    } else {
      shapeLayer = L.polyline(latlngs, options)
    }
    shapeLayer.addTo(map)
    shapeLayer.on(
      'pm:vertexadded pm:vertexremoved pm:markerdragend pm:update',
      syncFromLayer
    )
  }

  vertexLayer = L.layerGroup(
    draft.value.map((p) =>
      L.circleMarker([p[1], p[0]], {
        radius: 4,
        color: props.color,
        weight: 1,
        fillColor: props.color,
        fillOpacity: 1,
        bubblingMouseEvents: false
      })
    )
  ).addTo(map)
}

const onMapClick = (event) => {
  if (!visible.value || editing.value) return
  draft.value.push([
    Number(Number(event.latlng.lng).toFixed(6)),
    Number(Number(event.latlng.lat).toFixed(6))
  ])
  render()
}

const fitDraft = () => {
  if (!map) return
  const latlngs = draft.value.map((p) => [p[1], p[0]])
  if (latlngs.length >= 2) {
    map.fitBounds(L.latLngBounds(latlngs).pad(0.25), { maxZoom: 15 })
  } else if (latlngs.length === 1) {
    map.setView(latlngs[0], 12)
  } else {
    map.setView([26.647, 106.6302], 10)
  }
}

const initMap = () => {
  if (!mapRef.value) return
  if (!map) {
    map = L.map(mapRef.value, {
      zoomControl: true,
      attributionControl: false,
      minZoom: 6,
      maxZoom: 18
    })
    L.tileLayer(tiandituTileUrl(), { maxZoom: 18 }).addTo(map)
    map.on('click', onMapClick)
  }
  map.invalidateSize()
  fitDraft()
  render()
}

const open = () => {
  draft.value = (props.modelValue || []).map((p) => [Number(p[0]), Number(p[1])])
  visible.value = true
}

const onOpened = async () => {
  if (!tk) return
  await nextTick()
  try {
    initMap()
  } catch (error) {
    ElMessage.error('天地图加载失败，请检查 VITE_TIANDITU_TK 与域名白名单')
  }
}

const toggleEdit = () => {
  if (!shapeLayer || draft.value.length < 2) return
  if (editing.value) {
    stopEdit()
    syncFromLayer()
    render()
    return
  }
  editing.value = true
  if (vertexLayer) {
    map.removeLayer(vertexLayer)
    vertexLayer = null
  }
  shapeLayer.pm.enable({
    allowSelfIntersection: false,
    limitMarkersToCount: 0
  })
}

const undo = () => {
  if (editing.value) {
    stopEdit()
    syncFromLayer()
  }
  draft.value.pop()
  render()
}

const clearDraft = () => {
  stopEdit()
  draft.value = []
  render()
}

const confirm = () => {
  if (editing.value) {
    stopEdit()
    syncFromLayer()
  }
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
  removeLayers()
}

watch(
  () => [props.color, props.weight, props.mode],
  () => {
    if (visible.value && !editing.value) render()
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
  flex-wrap: wrap;
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
