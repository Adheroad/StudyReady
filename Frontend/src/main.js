import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/base.css'
import './styles/animations.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// Set initial theme based on current route
router.isReady().then(() => {
    const theme = router.currentRoute.value.meta.theme || 'dark'
    document.body.className = `theme-${theme}`
})

app.mount('#app')

