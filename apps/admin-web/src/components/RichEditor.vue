<template>
  <QuillEditor
    v-model:content="content"
    content-type="html"
    theme="snow"
    :toolbar="toolbar"
    class="rich-editor"
  />
</template>

<script setup>
import { computed } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})
const emit = defineEmits(['update:modelValue'])

const content = computed({
  get: () => props.modelValue || '',
  set: (value) => emit('update:modelValue', value)
})

const toolbar = [
  ['bold', 'italic', 'underline'],
  [{ color: [] }, { background: [] }],
  [{ list: 'ordered' }, { list: 'bullet' }],
  ['link'],
  ['clean']
]
</script>

<style>
.rich-editor {
  min-height: 180px;
  background: #fff;
}

.rich-editor .ql-container {
  min-height: 150px;
}
</style>
