import request from '@/utils/request'

export const listLabels = (params) => request.get('/map/label/list', { params })

export const getLabel = (id) => request.get(`/map/label/${id}`)

export const createLabel = (data) => request.post('/map/label', data)

export const updateLabel = (id, data) => request.put(`/map/label/${id}`, data)

export const deleteLabel = (id) => request.delete(`/map/label/${id}`)

export const updateLabelStatus = (id, status) =>
  request.put(`/map/label/${id}/status`, null, { params: { status } })
