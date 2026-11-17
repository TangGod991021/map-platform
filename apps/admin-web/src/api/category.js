import request from '@/utils/request'

export const listCategories = () => request.get('/map/category/list')

export const createCategory = (data) => request.post('/map/category', data)

export const updateCategory = (id, data) => request.put(`/map/category/${id}`, data)

export const deleteCategory = (id) => request.delete(`/map/category/${id}`)
