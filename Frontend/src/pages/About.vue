<template>
  <div class="about-page">
    <div class="container">
      <section class="about-hero">
        <h1 class="about-title">
          About <span class="text-gradient">StudyReady</span>
        </h1>
        <p class="about-lead">
          We're on a mission to democratize quality education preparation for every student in India.
        </p>
      </section>

      <section class="about-section">
        <h2 class="section-title">Our Mission</h2>
        <p class="section-text">
          At StudyReady, we believe that every student deserves access to high-quality practice 
          materials. Our AI-powered platform generates CBSE-compliant question papers instantly, 
          helping students and teachers save time and focus on what matters most — learning.
        </p>
      </section>

      <section class="about-section">
        <h2 class="section-title">Who We Are</h2>
        <p class="section-text">
          We're a team of educators, engineers, and AI enthusiasts passionate about transforming 
          how students prepare for exams. Built with cutting-edge RAG technology and deep 
          understanding of CBSE curriculum patterns.
        </p>
      </section>

      <section class="about-section about-values">
        <h2 class="section-title">Our Values</h2>
        <div class="values-grid">
          <div class="value-card glass-card">
            <Target class="value-icon" />
            <h3>Accuracy First</h3>
            <p>Every paper we generate meets official CBSE standards and blueprints.</p>
          </div>
          <div class="value-card glass-card">
            <Users class="value-icon" />
            <h3>Student-Centric</h3>
            <p>Designed for students, by people who understand academic challenges.</p>
          </div>
          <div class="value-card glass-card">
            <Sparkles class="value-icon" />
            <h3>Innovation</h3>
            <p>Leveraging AI and NLP to create the best educational tools possible.</p>
          </div>
        </div>
      </section>

      <section class="about-cta glass-card">
        <h2>Ready to Get Started?</h2>
        <p>Join thousands of students preparing smarter with StudyReady.</p>
        <RouterLink to="/login" class="btn btn--primary btn--large">
          Start Free
        </RouterLink>
      </section>
    </div>
  </div>
</template>

<script setup>
import { Target, Users, Sparkles } from 'lucide-vue-next'
</script>

<style scoped>
.about-page {
  padding: var(--space-3xl) 0;
}

.about-hero {
  text-align: center;
  margin-bottom: var(--space-3xl);
}

.about-title {
  font-size: clamp(2.5rem, 5vw, 4rem);
  margin-bottom: var(--space-lg);
}

.about-lead {
  font-size: var(--font-size-xl);
  color: var(--text-muted);
  max-width: 600px;
  margin: 0 auto;
}

.about-section {
  max-width: 700px;
  margin: 0 auto var(--space-3xl);
}

.section-title {
  font-size: var(--font-size-2xl);
  margin-bottom: var(--space-md);
}

.section-text {
  font-size: var(--font-size-lg);
  color: var(--text-muted);
  line-height: 1.8;
}

.about-values {
  max-width: 900px;
}

.values-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--space-xl);
  margin-top: var(--space-xl);
}

.value-card {
  text-align: center;
}

.value-icon {
  width: 40px;
  height: 40px;
  color: var(--accent-blue);
  margin-bottom: var(--space-md);
}

.value-card h3 {
  margin-bottom: var(--space-sm);
}

.value-card p {
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.about-cta {
  max-width: 600px;
  margin: var(--space-3xl) auto 0;
  text-align: center;
}

.about-cta h2 {
  font-size: var(--font-size-2xl);
  margin-bottom: var(--space-sm);
}

.about-cta p {
  color: var(--text-muted);
  margin-bottom: var(--space-xl);
}

.btn {
  display: inline-flex;
  align-items: center;
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
}
</style>
