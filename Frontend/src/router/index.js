import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// Lazy load pages for better performance
const Landing = () => import('../pages/Landing.vue')
const Generate = () => import('../pages/Generate.vue')
const Pricing = () => import('../pages/Pricing.vue')
const About = () => import('../pages/About.vue')
const Login = () => import('../pages/Login.vue')

const routes = [
    {
        path: '/',
        name: 'home',
        component: Landing,
        meta: { theme: 'dark' }
    },
    {
        path: '/generate',
        name: 'generate',
        component: Generate,
        meta: { theme: 'light', requiresAuth: true }
    },
    {
        path: '/pricing',
        name: 'pricing',
        component: Pricing,
        meta: { theme: 'light' }
    },
    {
        path: '/about',
        name: 'about',
        component: About,
        meta: { theme: 'light' }
    },
    {
        path: '/login',
        name: 'login',
        component: Login,
        meta: { theme: 'light' }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes,
    scrollBehavior(to, from, savedPosition) {
        if (savedPosition) {
            return savedPosition
        } else {
            return { top: 0 }
        }
    }
})

// Navigation guard for protected routes
router.beforeEach((to, from, next) => {
    const authStore = useAuthStore()

    // Check if route requires authentication
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        next({
            name: 'login',
            query: { redirect: to.fullPath }
        })
    } else {
        next()
    }
})

// Update theme class on route change
router.afterEach((to) => {
    const theme = to.meta.theme || 'light'
    document.body.className = `theme-${theme}`
})

export default router
