<template>
  <section class="how-it-works section">
    <div class="container">
      <div class="how-it-works__header">
        <h2 class="how-it-works__title">
          How It <span class="text-gradient">Works</span>
        </h2>
        <p class="how-it-works__subtitle">
          Generate your perfect question paper in 3 simple steps
        </p>
      </div>

      <div class="how-it-works__steps" ref="stepsRef">
        <div class="step" v-for="(step, index) in steps" :key="step.title">
          <div class="step__number">{{ index + 1 }}</div>
          <div class="step__content">
            <h3 class="step__title">{{ step.title }}</h3>
            <p class="step__description">{{ step.description }}</p>
          </div>
          <div class="step__connector" v-if="index < steps.length - 1"></div>
        </div>
      </div>

      <div class="how-it-works__cta">
        <RouterLink to="/generate" class="btn btn--primary btn--large">
          Start Generating
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useGsap } from '../../composables/useGsap'

const { animateOnScroll } = useGsap()

const stepsRef = ref(null)

const steps = [
  {
    title: 'Select Subject & Grade',
    description: 'Choose your subject, grade level, and total marks for the paper.'
  },
  {
    title: 'AI Generates Paper',
    description: 'Our AI selects the best questions from our database and formats them perfectly.'
  },
  {
    title: 'Download & Print',
    description: 'Get your CBSE-compliant question paper as PDF or DOCX, ready to use.'
  }
]

onMounted(() => {
  animateOnScroll('.step', { stagger: 0.2 })
})
</script>

<style scoped>
.how-it-works {
  position: relative;
}

.how-it-works__header {
  text-align: center;
  margin-bottom: var(--space-3xl);
}

.how-it-works__title {
  font-size: clamp(2rem, 4vw, 3rem);
  margin-bottom: var(--space-md);
}

.how-it-works__subtitle {
  font-size: var(--font-size-lg);
  color: var(--text-muted);
}

.how-it-works__steps {
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
  max-width: 600px;
  margin: 0 auto;
}

.step {
  position: relative;
  display: flex;
  gap: var(--space-lg);
  align-items: flex-start;
}

.step__number {
  flex-shrink: 0;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-blue);
  color: white;
  font-size: var(--font-size-xl);
  font-weight: 700;
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-glow-blue);
}

.step__content {
  flex: 1;
  padding-top: var(--space-xs);
}

.step__title {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-xs);
}

.step__description {
  color: var(--text-muted);
}

.step__connector {
  position: absolute;
  left: 24px;
  top: 60px;
  width: 2px;
  height: calc(100% + var(--space-xl) - 10px);
  background: linear-gradient(to bottom, var(--accent-blue), var(--accent-blue-t));
}

.how-it-works__cta {
  text-align: center;
  margin-top: var(--space-3xl);
}

/* Button styles */
.btn {
  display: inline-flex;
  align-items: center;
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

.btn--primary:hover {
  background: var(--accent-blue-hover);
  box-shadow: var(--shadow-glow-blue);
  transform: translateY(-2px);
}

@media (max-width: 640px) {
  .step {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .step__connector {
    display: none;
  }
}
</style>
