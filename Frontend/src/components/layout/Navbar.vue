<template>
  <nav class="navbar" :class="{ 'navbar--scrolled': isScrolled }">
    <div class="navbar__container container">
      <RouterLink to="/" class="navbar__logo">
        <span class="navbar__logo-icon">📚</span>
        <span class="navbar__logo-text">StudyReady</span>
      </RouterLink>

      <div class="navbar__links">
        <RouterLink to="/" class="navbar__link">Home</RouterLink>
        <RouterLink to="/pricing" class="navbar__link">Pricing</RouterLink>
        <RouterLink to="/about" class="navbar__link">About</RouterLink>
      </div>

      <div class="navbar__actions">
        <template v-if="authStore.isAuthenticated">
          <RouterLink to="/generate" class="btn btn--primary">
            Generate Paper
          </RouterLink>
          <button @click="handleLogout" class="btn btn--ghost">
            Logout
          </button>
        </template>
        <template v-else>
          <button @click="toggleTheme" class="btn btn--icon" :title="isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
            <Sun v-if="isDark" />
            <Moon v-else />
          </button>
          <RouterLink to="/login" class="btn btn--primary">
            Get Started
          </RouterLink>
        </template>
      </div>

      <button class="navbar__mobile-toggle" @click="mobileOpen = !mobileOpen">
        <span></span>
        <span></span>
        <span></span>
      </button>
    </div>

    <!-- Mobile menu -->
    <div class="navbar__mobile" :class="{ 'navbar__mobile--open': mobileOpen }">
      <RouterLink to="/" class="navbar__mobile-link" @click="mobileOpen = false">Home</RouterLink>
      <RouterLink to="/pricing" class="navbar__mobile-link" @click="mobileOpen = false">Pricing</RouterLink>
      <RouterLink to="/about" class="navbar__mobile-link" @click="mobileOpen = false">About</RouterLink>
      <template v-if="authStore.isAuthenticated">
        <RouterLink to="/generate" class="navbar__mobile-link" @click="mobileOpen = false">Generate</RouterLink>
        <button @click="handleLogout" class="navbar__mobile-link">Logout</button>
      </template>
      <template v-else>
        <RouterLink to="/login" class="navbar__mobile-link" @click="mobileOpen = false">Login</RouterLink>
      </template>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { Sun, Moon } from 'lucide-vue-next'

const authStore = useAuthStore()
const router = useRouter()

const isScrolled = ref(false)
const mobileOpen = ref(false)
const isDark = ref(true)

function toggleTheme() {
  isDark.value = !isDark.value
  document.body.className = isDark.value ? 'theme-dark' : 'theme-light'
}

function handleScroll() {
  isScrolled.value = window.scrollY > 50
}

function handleLogout() {
  authStore.logout()
  router.push('/')
  mobileOpen.value = false
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: var(--z-sticky);
  padding: var(--space-md) 0;
  transition: all var(--transition-base);
}

.navbar--scrolled {
  background: var(--surface);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border-bottom: 1px solid var(--glass-border-color);
}

.navbar__container {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar__logo {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--font-size-xl);
  font-weight: 700;
}

.navbar__logo-icon {
  font-size: 1.5em;
}

.navbar__links {
  display: flex;
  gap: var(--space-xl);
}

.navbar__link {
  font-weight: 500;
  opacity: 0.8;
  transition: opacity var(--transition-fast);
}

.navbar__link:hover,
.navbar__link.router-link-active {
  opacity: 1;
}

.navbar__actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) var(--space-lg);
  font-weight: 600;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.btn--primary {
  background: var(--accent-blue);
  color: white;
}

.btn--primary:hover {
  background: var(--accent-blue-hover);
  box-shadow: var(--shadow-glow-blue);
}

.btn--ghost {
  background: transparent;
  color: var(--text);
  opacity: 0.8;
}

.btn--ghost:hover {
  opacity: 1;
}

.btn--icon {
  background: transparent;
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: var(--radius-full);
  color: var(--text);
}

.btn--icon:hover {
  background: var(--bg-2);
  color: var(--accent-blue);
}

/* Mobile toggle */
.navbar__mobile-toggle {
  display: none;
  flex-direction: column;
  gap: 4px;
  padding: var(--space-sm);
}

.navbar__mobile-toggle span {
  width: 24px;
  height: 2px;
  background: var(--text);
  transition: all var(--transition-fast);
}

/* Mobile menu */
.navbar__mobile {
  display: none;
  flex-direction: column;
  padding: var(--space-md);
  background: var(--surface);
  backdrop-filter: blur(var(--glass-blur));
}

.navbar__mobile-link {
  padding: var(--space-md);
  font-weight: 500;
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}

.navbar__mobile-link:hover {
  background: var(--accent-blue-t-light);
}

/* Responsive */
@media (max-width: 768px) {
  .navbar__links,
  .navbar__actions {
    display: none;
  }

  .navbar__mobile-toggle {
    display: flex;
  }

  .navbar__mobile--open {
    display: flex;
  }
}
</style>
