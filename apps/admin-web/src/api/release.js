import request from '@/utils/request'

export const publishMap = (data) => request.post('/map/release/publish', data)

export const listReleases = () => request.get('/map/release/list')

export const getSummary = () => request.get('/dashboard/summary')
