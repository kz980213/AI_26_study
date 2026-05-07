import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import UsersView from '../views/UsersView.vue'
import { getToken } from '../utils/storage'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/home',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/allUsers',
      name: 'allUsers',
      component: UsersView,
    },
  ],
})

router.beforeEach((to, from, next) => {
    const token = getToken()
    if (!token && to.path !== '/login') {
        next('/login')
        return;
    } 
    if (token && to.path === '/login') {
        next('/home')
        return;
    }
    next()
})


export default router