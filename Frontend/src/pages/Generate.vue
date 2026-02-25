<template>
  <div class="generate-page">
    <div class="container">
      <div class="generate-header">
        <h1 class="generate-title">Generate Question Paper</h1>
        <p class="generate-subtitle">
          Create a CBSE-compliant question paper in seconds
        </p>
      </div>

      <div class="generate-card glass-card">
        <form @submit.prevent="handleGenerate" class="generate-form">
          <div class="form-row">
            <div class="form-group">
              <label for="subject" class="form-label">Subject</label>
              <select id="subject" v-model="form.subject" class="form-select" required>
                <option value="">Select subject</option>
                <option value="Commercial Art">Commercial Art</option>
                <option value="Mathematics">Mathematics</option>
                <option value="Physics">Physics</option>
                <option value="Chemistry">Chemistry</option>
                <option value="Biology">Biology</option>
              </select>
            </div>

            <div class="form-group">
              <label for="grade" class="form-label">Grade</label>
              <select id="grade" v-model="form.grade" class="form-select" required>
                <option value="">Select grade</option>
                <option value="XII">Class XII</option>
                <option value="XI">Class XI</option>
                <option value="X">Class X</option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="marks" class="form-label">Total Marks</label>
              <input
                id="marks"
                v-model.number="form.total_marks"
                type="number"
                class="form-input"
                min="20"
                max="100"
                placeholder="36"
                required
              />
            </div>

            <div class="form-group">
              <label class="form-label">Language</label>
              <div class="form-toggle-group">
                <button
                  type="button"
                  class="form-toggle"
                  :class="{ active: form.language === 'en' }"
                  @click="form.language = 'en'"
                >
                  English
                </button>
                <button
                  type="button"
                  class="form-toggle"
                  :class="{ active: form.language === 'hi' }"
                  @click="form.language = 'hi'"
                >
                  Hindi
                </button>
                <button
                  type="button"
                  class="form-toggle"
                  :class="{ active: form.language === 'both' }"
                  @click="form.language = 'both'"
                >
                  Both
                </button>
              </div>
            </div>
          </div>

          <div v-if="error" class="form-error">
            {{ error }}
          </div>

          <button type="submit" class="btn btn--primary btn--large btn--full" :disabled="loading">
            <Loader2 v-if="loading" class="btn__icon spin" />
            <FileDown v-else class="btn__icon" />
            {{ loading ? 'Generating...' : 'Generate Paper' }}
          </button>
        </form>

        <!-- Success state -->
        <div v-if="paperId" class="generate-success">
          <CheckCircle class="success-icon" />
          <h3>Paper Generated Successfully!</h3>
          <p>Your question paper is ready for download.</p>
          <div class="success-actions">
            <button @click="downloadPaper('pdf')" class="btn btn--primary">
              <FileDown class="btn__icon" /> Download PDF
            </button>
            <button @click="downloadPaper('docx')" class="btn btn--outline">
              <FileDown class="btn__icon" /> Download DOCX
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'
import { FileDown, Loader2, CheckCircle } from 'lucide-vue-next'

const API_BASE = 'http://localhost:8000/api/v1'

const loading = ref(false)
const error = ref('')
const paperId = ref(null)

const form = reactive({
  subject: '',
  grade: '',
  total_marks: 36,
  language: 'both'
})

async function handleGenerate() {
  loading.value = true
  error.value = ''
  paperId.value = null

  try {
    const response = await axios.post(`${API_BASE}/papers/generate`, form)
    paperId.value = response.data.paper_id
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to generate paper'
  } finally {
    loading.value = false
  }
}

function downloadPaper(format) {
  window.open(`${API_BASE}/papers/${paperId.value}/download?format=${format}`, '_blank')
}
</script>

<style scoped>
.generate-page {
  padding: var(--space-3xl) 0;
}

.generate-header {
  text-align: center;
  margin-bottom: var(--space-2xl);
}

.generate-title {
  font-size: clamp(2rem, 4vw, 3rem);
  margin-bottom: var(--space-sm);
}

.generate-subtitle {
  color: var(--text-muted);
  font-size: var(--font-size-lg);
}

.generate-card {
  max-width: 600px;
  margin: 0 auto;
}

.generate-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.form-label {
  font-weight: 500;
}

.form-input,
.form-select {
  padding: var(--space-md);
  background: var(--bg-2);
  border: 1px solid var(--glass-border-color);
  border-radius: var(--radius-md);
  color: var(--text);
  font-size: var(--font-size-base);
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-toggle-group {
  display: flex;
  gap: var(--space-sm);
}

.form-toggle {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-2);
  border: 1px solid var(--glass-border-color);
  border-radius: var(--radius-md);
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  transition: all var(--transition-fast);
}

.form-toggle.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.form-error {
  padding: var(--space-md);
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-md);
  color: #ef4444;
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

.btn--large {
  padding: var(--space-lg) var(--space-2xl);
  font-size: var(--font-size-lg);
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

.btn--outline {
  background: transparent;
  border: 2px solid var(--glass-border-color);
}

.btn--outline:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
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

/* Success state */
.generate-success {
  text-align: center;
  padding: var(--space-2xl);
  margin-top: var(--space-xl);
  border-top: 1px solid var(--glass-border-color);
}

.success-icon {
  width: 60px;
  height: 60px;
  color: #22c55e;
  margin-bottom: var(--space-lg);
}

.generate-success h3 {
  margin-bottom: var(--space-sm);
}

.generate-success p {
  color: var(--text-muted);
  margin-bottom: var(--space-xl);
}

.success-actions {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .success-actions {
    flex-direction: column;
  }
}
</style>
