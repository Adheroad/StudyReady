<template>
  <section class="features section" ref="sectionRef">
    <div class="container">
      <div class="features__header">
        <h2 class="features__title">
          Why Choose <span class="text-gradient">StudyReady</span>?
        </h2>
        <p class="features__subtitle">
          Powered by AI, designed for excellence
        </p>
      </div>

      <div class="features__grid" ref="gridRef">
        <div class="feature-card glass-card" v-for="feature in features" :key="feature.title">
          <div class="feature-card__icon">
            <component :is="feature.icon" />
          </div>
          <h3 class="feature-card__title">{{ feature.title }}</h3>
          <p class="feature-card__description">{{ feature.description }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { FileText, Languages, Brain, Zap } from 'lucide-vue-next'
import { useGsap } from '../../composables/useGsap'

const { animateOnScroll, animateFadeUp } = useGsap()

const sectionRef = ref(null)
const gridRef = ref(null)

const features = [
  {
    icon: Brain,
    title: 'AI-Powered Generation',
    description: 'Smart question selection using RAG technology and vector embeddings for contextually relevant papers.'
  },
  {
    icon: FileText,
    title: 'CBSE Compliant',
    description: 'Pixel-perfect formatting matching official CBSE 2025 standards with proper sections and blueprints.'
  },
  {
    icon: Languages,
    title: 'Bilingual Support',
    description: 'Generate papers in English, Hindi, or both with professional split-layout formatting.'
  },
  {
    icon: Zap,
    title: 'Instant Download',
    description: 'Get your question paper as PDF or DOCX in seconds, ready for print or digital distribution.'
  }
]

onMounted(() => {
  animateFadeUp('.features__header > *', { delay: 0.2 })
  animateOnScroll('.feature-card', { stagger: 0.15 })
})
</script>

<style scoped>
.features {
  background: var(--bg-2);
}

.features__header {
  text-align: center;
  margin-bottom: var(--space-3xl);
}

.features__title {
  font-size: clamp(2rem, 4vw, 3rem);
  margin-bottom: var(--space-md);
}

.features__subtitle {
  font-size: var(--font-size-lg);
  color: var(--text-muted);
}

.features__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--space-xl);
}

.feature-card {
  text-align: center;
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-lg);
}

.feature-card__icon {
  width: 60px;
  height: 60px;
  margin: 0 auto var(--space-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-blue-t-light);
  border-radius: var(--radius-lg);
  color: var(--accent-blue);
}

.feature-card__icon svg {
  width: 28px;
  height: 28px;
}

.feature-card__title {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-sm);
}

.feature-card__description {
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}
</style>
