import { createRouter, createWebHistory } from 'vue-router'

const Login = () => import('@/views/login/index.vue')
const Layout = () => import('@/layout/index.vue')
const Dashboard = () => import('@/views/dashboard/index.vue')
const MapCategory = () => import('@/views/map/category/index.vue')
const MapLabel = () => import('@/views/map/label/index.vue')
const MapRoute = () => import('@/views/map/route/index.vue')
const MapArea = () => import('@/views/map/area/index.vue')
const MapRelease = () => import('@/views/map/release/index.vue')

const routes = [
  {
    path: '/login',
    component: Login,
    meta: { public: true, title: '登录' }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: Dashboard, meta: { title: '首页' } },
      { path: 'map/category', component: MapCategory, meta: { title: '分类管理' } },
      { path: 'map/label', component: MapLabel, meta: { title: '标签管理' } },
      { path: 'map/route', component: MapRoute, meta: { title: '路线管理' } },
      { path: 'map/area', component: MapArea, meta: { title: '区域管理' } },
      { path: 'map/release', component: MapRelease, meta: { title: '发布管理' } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const token = localStorage.getItem('map_platform_token')
  if (!to.meta.public && !token) {
    return '/login'
  }
  if (to.path === '/login' && token) {
    return '/dashboard'
  }
  return true
})

export default router
