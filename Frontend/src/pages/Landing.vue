<template>
  <div class="landing">
    <Hero />
    <Features />
    <HowItWorks />
  </div>
</template>

<script setup>
import Hero from '../components/landing/Hero.vue'
import Features from '../components/landing/Features.vue'
import HowItWorks from '../components/landing/HowItWorks.vue'
</script>

<style scoped>
.landing {
  overflow-x: hidden;
}
</style>
