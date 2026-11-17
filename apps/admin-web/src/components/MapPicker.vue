<template>
  <div class="map-picker">
    <el-button @click="open">地图选点</el-button>
    <span class="muted coord-text">
      {{ Number(modelValue?.lng || 0).toFixed(6) }}, {{ Number(modelValue?.lat || 0).toFixed(6) }}
    </span>

    <el-dialog
      v-model="visible"
      title="地图选点"
      width="760px"
      @opened="onOpened"
      @closed="onClosed"
    >
      <el-alert
        v-if="!tk"
        title="未配置 VITE_TIANDITU_TK，当前只能手动输入坐标"
        type="warning"
        :closable="false"
        show-icon
        class="tip"
      />

      <div v-if="tk" class="map-picker-map" ref="mapRef">
        <div class="map-picker-crosshair"></div>
      </div>

      <div class="manual-row">
        <span class="muted">手动坐标</span>
        <el-input-number v-model="manualLng" :precision="6" :step="0.0001" controls-position="right" />
        <el-input-number v-model="manualLat" :precision="6" :step="0.0001" controls-position="right" />
      </div>

      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button v-if="tk" type="primary" @click="useCenter">使用地图中心</el-button>
        <el-button v-else type="primary" @click="applyManual">使用手动坐标</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ lng: 106.6302, lat: 26.647 })
  }
})
const emit = defineEmits(['update:modelValue'])

const tk = import.meta.env.VITE_TIANDITU_TK || ''
const visible = ref(false)
const mapRef = ref()
const manualLng = ref(Number(props.modelValue?.lng || 106.6302))
const manualLat = ref(Number(props.modelValue?.lat || 26.647))
let map = null

// 天地图卫星影像 WMTS；Leaflet 占位符为 {z} / {x} / {y}
const tiandituTileUrl = () =>
  'https://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0' +
  '&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles' +
  `&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${encodeURIComponent(tk)}`

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
  }
  map.setView([manualLat.value, manualLng.value], 13)
  map.invalidateSize()
}

const open = () => {
  manualLng.value = Number(props.modelValue?.lng || 106.6302)
  manualLat.value = Number(props.modelValue?.lat || 26.647)
  visible.value = true
}

const onOpened = () => {
  if (!tk) return
  initMap()
}

const onClosed = () => {
  // 地图实例保留在弹窗 DOM 中，下次打开只需重新计算尺寸并定位
  if (map) map.closePopup()
}

const useCenter = () => {
  if (!map) return
  const center = map.getCenter()
  emit('update:modelValue', {
    lng: Number(center.lng.toFixed(6)),
    lat: Number(center.lat.toFixed(6))
  })
  visible.value = false
}

const applyManual = () => {
  emit('update:modelValue', {
    lng: Number(manualLng.value),
    lat: Number(manualLat.value)
  })
  visible.value = false
}
</script>

<style scoped>
.map-picker {
  display: flex;
  align-items: center;
  gap: 10px;
}

.coord-text {
  font-family: monospace;
  font-size: 12px;
}

.tip {
  margin-bottom: 12px;
}

.manual-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
  flex-wrap: wrap;
}
</style>
