<template>
  <div class="pricing-page">
    <div class="container">
      <div class="pricing-header">
        <h1 class="pricing-title">
          Simple, Transparent <span class="text-gradient">Pricing</span>
        </h1>
        <p class="pricing-subtitle">
          Start free, upgrade when you're ready
        </p>
      </div>

      <div class="pricing-grid">
        <div
          v-for="plan in plans"
          :key="plan.name"
          class="pricing-card glass-card"
          :class="{ 'pricing-card--featured': plan.featured }"
        >
          <div v-if="plan.featured" class="pricing-badge">Most Popular</div>
          <h3 class="pricing-name">{{ plan.name }}</h3>
          <div class="pricing-price">
            <span class="pricing-currency">₹</span>
            <span class="pricing-amount">{{ plan.price }}</span>
            <span class="pricing-period" v-if="plan.price > 0">/month</span>
          </div>
          <p class="pricing-description">{{ plan.description }}</p>
          
          <ul class="pricing-features">
            <li v-for="feature in plan.features" :key="feature" class="pricing-feature">
              <Check class="pricing-feature-icon" />
              {{ feature }}
            </li>
          </ul>

          <RouterLink
            :to="plan.cta.link"
            class="btn"
            :class="plan.featured ? 'btn--primary' : 'btn--outline'"
          >
            {{ plan.cta.text }}
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Check } from 'lucide-vue-next'

const plans = [
  {
    name: 'Free',
    price: 0,
    description: 'Perfect for trying out StudyReady',
    features: [
      '3 papers per month',
      'PDF download',
      'Basic subjects',
      'English only'
    ],
    cta: { text: 'Get Started', link: '/login' }
  },
  {
    name: 'Pro',
    price: 299,
    description: 'For students and teachers',
    featured: true,
    features: [
      'Unlimited papers',
      'PDF & DOCX download',
      'All subjects',
      'Bilingual support',
      'Priority processing'
    ],
    cta: { text: 'Start Free Trial', link: '/login' }
  },
  {
    name: 'Enterprise',
    price: 999,
    description: 'For schools and institutions',
    features: [
      'Everything in Pro',
      'API access',
      'Bulk generation',
      'Custom branding',
      'Dedicated support'
    ],
    cta: { text: 'Contact Sales', link: '/about' }
  }
]
</script>

<style scoped>
.pricing-page {
  padding: var(--space-3xl) 0;
}

.pricing-header {
  text-align: center;
  margin-bottom: var(--space-3xl);
}

.pricing-title {
  font-size: clamp(2rem, 4vw, 3rem);
  margin-bottom: var(--space-md);
}

.pricing-subtitle {
  font-size: var(--font-size-lg);
  color: var(--text-muted);
}

.pricing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-xl);
  max-width: 1000px;
  margin: 0 auto;
}

.pricing-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: var(--space-2xl);
  transition: transform var(--transition-base);
}

.pricing-card:hover {
  transform: translateY(-5px);
}

.pricing-card--featured {
  border-color: var(--accent-blue);
  box-shadow: var(--shadow-glow-blue);
}

.pricing-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  padding: var(--space-xs) var(--space-md);
  background: var(--accent-blue);
  color: white;
  font-size: var(--font-size-xs);
  font-weight: 600;
  border-radius: var(--radius-full);
}

.pricing-name {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-md);
}

.pricing-price {
  margin-bottom: var(--space-md);
}

.pricing-currency {
  font-size: var(--font-size-xl);
  vertical-align: top;
}

.pricing-amount {
  font-size: var(--font-size-5xl);
  font-weight: 800;
}

.pricing-period {
  color: var(--text-muted);
}

.pricing-description {
  color: var(--text-muted);
  margin-bottom: var(--space-xl);
}

.pricing-features {
  flex: 1;
  margin-bottom: var(--space-xl);
}

.pricing-feature {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  font-size: var(--font-size-sm);
}

.pricing-feature-icon {
  width: 16px;
  height: 16px;
  color: var(--accent-blue);
  flex-shrink: 0;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md) var(--space-xl);
  font-weight: 600;
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
  text-align: center;
}

.btn--primary {
  background: var(--accent-blue);
  color: white;
}

.btn--primary:hover {
  background: var(--accent-blue-hover);
  box-shadow: var(--shadow-glow-blue);
}

.btn--outline {
  background: transparent;
  border: 2px solid var(--glass-border-color);
}

.btn--outline:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}
</style>
