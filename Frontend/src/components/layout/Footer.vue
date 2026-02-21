<template>
  <footer class="footer">
    <div class="footer__container container">
      <div class="footer__brand">
        <span class="footer__logo">📚 StudyReady</span>
        <p class="footer__tagline">Getting you ready before you believe you are.</p>
      </div>

      <div class="footer__links">
        <div class="footer__column">
          <h4 class="footer__heading">Product</h4>
          <RouterLink to="/generate" class="footer__link">Generate Paper</RouterLink>
          <RouterLink to="/pricing" class="footer__link">Pricing</RouterLink>
        </div>
        <div class="footer__column">
          <h4 class="footer__heading">Company</h4>
          <RouterLink to="/about" class="footer__link">About Us</RouterLink>
          <a href="mailto:hello@studyready.in" class="footer__link">Contact</a>
        </div>
      </div>

      <div class="footer__bottom">
        <p class="footer__copyright">© {{ currentYear }} StudyReady. All rights reserved.</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
const currentYear = new Date().getFullYear()
</script>

<style scoped>
.footer {
  padding: var(--space-3xl) 0 var(--space-xl);
  border-top: 1px solid var(--glass-border-color);
  margin-top: auto;
}

.footer__container {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-3xl);
}

.footer__brand {
  max-width: 300px;
}

.footer__logo {
  font-size: var(--font-size-xl);
  font-weight: 700;
}

.footer__tagline {
  margin-top: var(--space-sm);
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.footer__links {
  display: flex;
  gap: var(--space-3xl);
}

.footer__column {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.footer__heading {
  font-size: var(--font-size-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-sm);
  opacity: 0.6;
}

.footer__link {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  transition: color var(--transition-fast);
}

.footer__link:hover {
  color: var(--accent-blue);
}

.footer__bottom {
  grid-column: 1 / -1;
  padding-top: var(--space-xl);
  border-top: 1px solid var(--glass-border-color);
  margin-top: var(--space-xl);
}

.footer__copyright {
  font-size: var(--font-size-sm);
  color: var(--text-subtle);
}

@media (max-width: 768px) {
  .footer__container {
    grid-template-columns: 1fr;
    gap: var(--space-xl);
  }

  .footer__links {
    gap: var(--space-xl);
  }
}
</style>
