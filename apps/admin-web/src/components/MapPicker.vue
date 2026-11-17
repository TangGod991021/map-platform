<template>
  <div class="map-picker">
    <el-button @click="open">地图选点</el-button>
    <span class="muted coord-text">
      {{ Number(modelValue?.lng || 0).toFixed(6) }}, {{ Number(modelValue?.lat || 0).toFixed(6) }}
    </span>

    <el-dialog v-model="visible" title="地图选点" width="760px">
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
import { nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ lng: 106.6302, lat: 26.647, })
  }
})
const emit = defineEmits(['update:modelValue'])

const tk = import.meta.env.VITE_TIANDITU_TK || ''
const visible = ref(false)
const mapRef = ref()
const manualLng = ref(Number(props.modelValue?.lng || 106.6302))
const manualLat = ref(Number(props.modelValue?.lat || 26.647))
let map = null

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

const initMap = () => {
  if (!mapRef.value) return
  if (!map) {
    map = new window.T.Map(mapRef.value)
    map.enableScrollWheelZoom(true)
  }
  map.centerAndZoom(new window.T.LngLat(manualLng.value, manualLat.value), 13)
}

const open = async () => {
  manualLng.value = Number(props.modelValue?.lng || 106.6302)
  manualLat.value = Number(props.modelValue?.lat || 26.647)
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
