import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api/v1'

export const useAuthStore = defineStore('auth', () => {
    // State
    const user = ref(null)
    const token = ref(localStorage.getItem('token') || null)
    const loading = ref(false)
    const error = ref(null)

    // Getters
    const isAuthenticated = computed(() => !!token.value)
    const userName = computed(() => user.value?.name || 'User')

    // Set auth header for axios if token exists
    if (token.value) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    }

    // Actions
    async function login(email, password) {
        loading.value = true
        error.value = null
        try {
            const response = await axios.post(`${API_BASE}/auth/login`, {
                email,
                password
            })
            // Store the token
            const accessToken = response.data.access_token
            token.value = accessToken
            localStorage.setItem('token', accessToken)
            axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`

            // Fetch user info
            await fetchUser()

            return { success: true }
        } catch (err) {
            error.value = err.response?.data?.detail || 'Login failed'
            return { success: false, error: error.value }
        } finally {
            loading.value = false
        }
    }

    async function fetchUser() {
        if (!token.value) return
        try {
            const response = await axios.get(`${API_BASE}/auth/me`)
            user.value = response.data
        } catch (err) {
            // Token invalid, logout
            logout()
        }
    }

    function logout() {
        token.value = null
        user.value = null
        localStorage.removeItem('token')
        delete axios.defaults.headers.common['Authorization']
    }

    // Auto-fetch user on init if token exists
    if (token.value && !user.value) {
        fetchUser()
    }

    return {
        user,
        token,
        loading,
        error,
        isAuthenticated,
        userName,
        login,
        fetchUser,
        logout
    }
})
