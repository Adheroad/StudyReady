<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card glass-card">
        <h1 class="login-title">Welcome Back</h1>
        <p class="login-subtitle">Sign in to your account</p>

        <form @submit.prevent="handleSubmit" class="login-form">
          <div class="form-group">
            <label for="email" class="form-label">Email</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              class="form-input"
              placeholder="you@example.com"
              required
            />
          </div>

          <div class="form-group">
            <label for="password" class="form-label">Password</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              class="form-input"
              placeholder="••••••••"
              required
              minlength="6"
            />
          </div>

          <div v-if="error" class="form-error">
            {{ error }}
          </div>

          <button type="submit" class="btn btn--primary btn--full" :disabled="loading">
            <Loader2 v-if="loading" class="btn__icon spin" />
            <span v-else>Sign In</span>
          </button>
        </form>

        <!-- Signup disabled notice -->
        <div class="signup-notice">
          <Lock class="notice-icon" />
          <p>We are not accepting new users at this time.<br/>Please check back later.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Loader2, Lock } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref('')

const form = reactive({
  email: '',
  password: ''
})

async function handleSubmit() {
  loading.value = true
  error.value = ''

  const result = await authStore.login(form.email, form.password)
  
  loading.value = false

  if (result.success) {
    const redirect = route.query.redirect || '/generate'
    router.push(redirect)
  } else {
    error.value = result.error
  }
}
</script>

<style scoped>
.login-page {
  min-height: calc(100vh - 60px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
}

.login-container {
  width: 100%;
  max-width: 420px;
}

.login-card {
  padding: var(--space-2xl);
}

.login-title {
  font-size: var(--font-size-3xl);
  margin-bottom: var(--space-xs);
}

.login-subtitle {
  color: var(--text-muted);
  margin-bottom: var(--space-xl);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.form-label {
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.form-input {
  padding: var(--space-md);
  background: var(--bg-2);
  border: 1px solid var(--glass-border-color);
  border-radius: var(--radius-md);
  color: var(--text);
  transition: border-color var(--transition-fast);
}

.form-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-input::placeholder {
  color: var(--text-subtle);
}

.form-error {
  padding: var(--space-md);
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-md);
  color: #ef4444;
  font-size: var(--font-size-sm);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-xl);
  font-weight: 600;
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}

.btn--primary {
  background: var(--accent-blue);
  color: white;
}

.btn--primary:hover:not(:disabled) {
  background: var(--accent-blue-hover);
  box-shadow: var(--shadow-glow-blue);
}

.btn--primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn--full {
  width: 100%;
}

.btn__icon {
  width: 20px;
  height: 20px;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Signup disabled notice */
.signup-notice {
  margin-top: var(--space-xl);
  padding: var(--space-lg);
  background: var(--accent-gold-t-light);
  border: 1px solid var(--accent-gold-t);
  border-radius: var(--radius-md);
  text-align: center;
}

.notice-icon {
  width: 24px;
  height: 24px;
  color: var(--accent-gold);
  margin-bottom: var(--space-sm);
}

.signup-notice p {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  line-height: 1.5;
}
</style>
