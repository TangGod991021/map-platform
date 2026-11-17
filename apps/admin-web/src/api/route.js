import request from '@/utils/request'

export const listRoutes = () => request.get('/map/route/list')

export const createRoute = (data) => request.post('/map/route', data)

export const updateRoute = (id, data) => request.put(`/map/route/${id}`, data)

export const deleteRoute = (id) => request.delete(`/map/route/${id}`)
