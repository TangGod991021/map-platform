import request from '@/utils/request'

export const login = (data) => request.post('/login', data)

export const getInfo = () => request.get('/getInfo')

export const getRouters = () => request.get('/getRouters')
