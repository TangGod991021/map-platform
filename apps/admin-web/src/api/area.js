import request from '@/utils/request'

export const listAreas = () => request.get('/map/area/list')

export const createArea = (data) => request.post('/map/area', data)

export const updateArea = (id, data) => request.put(`/map/area/${id}`, data)

export const deleteArea = (id) => request.delete(`/map/area/${id}`)
