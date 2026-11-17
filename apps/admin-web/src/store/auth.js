import { defineStore } from 'pinia'

import { getInfo, login } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('map_platform_token') || '',
    user: null
  }),
  getters: {
    nickname: (state) => state.user?.nickname || state.user?.username || '管理员'
  },
  actions: {
    async login(form) {
      const res = await login(form)
      this.token = res.data.access_token
      localStorage.setItem('map_platform_token', this.token)
      await this.fetchInfo()
    },
    async fetchInfo() {
      const res = await getInfo()
      this.user = res.data
      return this.user
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('map_platform_token')
    }
  }
})
