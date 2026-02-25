<template>
  <section class="hero">
    <!-- Background -->
    <div class="hero__background">
      <div class="hero__grid"></div>
      <div class="hero__glow hero__glow--blue"></div>
      <div class="hero__glow hero__glow--gold"></div>
    </div>

    <!-- Audio player (hidden) -->
    <audio ref="audioRef" loop preload="auto">
      <source src="/ambient-music.mp3" type="audio/mpeg" />
    </audio>

    <!-- Music toggle button -->
    <button 
      class="music-toggle" 
      @click="toggleMusic" 
      :aria-label="isPlaying ? 'Mute music' : 'Play music'"
    >
      <Volume2 v-if="isPlaying" class="music-icon" />
      <VolumeX v-else class="music-icon" />
    </button>

    <div class="hero__container container">
      <!-- Left: Content -->
      <div class="hero__content" ref="contentRef">
        <h1 class="hero__title">
          <span class="hero__title-line">Generate CBSE</span>
          <span class="hero__title-line text-gradient">Question Papers</span>
        </h1>
        
        <p class="hero__subtitle">
          AI-powered precision for students and teachers. Create customized CBSE papers instantly.
        </p>

        <!-- Inline Form -->
        <div class="hero__form glass-card" ref="formRef">
          <div class="form-group">
            <label class="form-label">Subject</label>
            <select v-model="form.subject" class="form-input">
              <option value="">Select Subject</option>
              <option value="Commercial Art">Commercial Art</option>
              <option value="Mathematics">Mathematics</option>
              <option value="Physics">Physics</option>
              <option value="Chemistry">Chemistry</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">Total Marks</label>
            <input 
              type="number" 
              v-model.number="form.total_marks" 
              class="form-input"
              placeholder="36"
              min="20" 
              max="100"
            />
          </div>

          <div class="form-group">
            <label class="form-label">Language</label>
            <div class="language-toggle">
              <button 
                type="button"
                :class="['lang-btn', { active: form.language === 'en' }]"
                @click="form.language = 'en'"
              >English</button>
              <button 
                type="button"
                :class="['lang-btn', { active: form.language === 'hi' }]"
                @click="form.language = 'hi'"
              >Hindi</button>
              <button 
                type="button"
                :class="['lang-btn', { active: form.language === 'both' }]"
                @click="form.language = 'both'"
              >Both</button>
            </div>
          </div>

          <RouterLink to="/generate" class="btn btn--primary btn--full">
            Generate Now
          </RouterLink>
        </div>
      </div>

      <!-- Right: Visual -->
      <div class="hero__visual" ref="visualRef">
        <div class="hero__orb">
          <div class="orb-inner"></div>
        </div>
        <div class="hero__symbols">
          <span class="symbol symbol--1">π</span>
          <span class="symbol symbol--2">∑</span>
          <span class="symbol symbol--3">∫</span>
          <span class="symbol symbol--4">√</span>
        </div>
      </div>
    </div>

    <!-- Scroll indicator -->
    <div class="hero__scroll" ref="scrollRef">
      <ChevronDown class="scroll-icon" />
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { Volume2, VolumeX, ChevronDown } from 'lucide-vue-next'
import { useGsap } from '../../composables/useGsap'

const { gsap } = useGsap()

const contentRef = ref(null)
const formRef = ref(null)
const visualRef = ref(null)
const scrollRef = ref(null)
const audioRef = ref(null)

const isPlaying = ref(false)

const form = reactive({
  subject: '',
  total_marks: 36,
  language: 'both'
})

function toggleMusic() {
  if (audioRef.value) {
    if (isPlaying.value) {
      audioRef.value.pause()
    } else {
      audioRef.value.volume = 0.3
      audioRef.value.play().catch(() => {})
    }
    isPlaying.value = !isPlaying.value
  }
}

onMounted(() => {
  const tl = gsap.timeline({ defaults: { ease: 'power3.out' } })

  // Stagger content reveal
  tl.from('.hero__title-line', {
    y: 60,
    opacity: 0,
    duration: 1,
    stagger: 0.2
  })
  .from('.hero__subtitle', {
    y: 30,
    opacity: 0,
    duration: 0.8
  }, '-=0.5')
  .from(formRef.value, {
    y: 40,
    opacity: 0,
    duration: 0.8
  }, '-=0.4')
  .from(visualRef.value, {
    scale: 0.8,
    opacity: 0,
    duration: 1,
    ease: 'back.out(1.2)'
  }, '-=0.6')
  .from(scrollRef.value, {
    opacity: 0,
    duration: 0.5
  }, '-=0.3')

  // Float orb
  gsap.to('.hero__orb', {
    y: -20,
    duration: 3,
    repeat: -1,
    yoyo: true,
    ease: 'power1.inOut'
  })

  // Float symbols
  gsap.to('.symbol', {
    y: -10,
    duration: 2,
    stagger: 0.3,
    repeat: -1,
    yoyo: true,
    ease: 'power1.inOut'
  })

  // Scroll indicator
  gsap.to(scrollRef.value, {
    y: 10,
    duration: 1.5,
    repeat: -1,
    yoyo: true,
    ease: 'power1.inOut'
  })
})
</script>

<style scoped>
.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  overflow: hidden;
  padding: var(--space-3xl) 0;
}

.hero__background {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero__grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(67, 97, 238, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(67, 97, 238, 0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: linear-gradient(transparent, black 30%, black 70%, transparent);
}

.hero__glow {
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.25;
}

.hero__glow--blue {
  top: -150px;
  right: 10%;
  background: var(--accent-blue);
}

.hero__glow--gold {
  bottom: -150px;
  left: 0;
  background: var(--accent-gold);
  opacity: 0.15;
}

/* Music toggle */
.music-toggle {
  position: fixed;
  bottom: var(--space-xl);
  right: var(--space-xl);
  z-index: 100;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
  background: var(--surface);
  border: 1px solid var(--glass-border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  transition: all var(--transition-base);
}

.music-toggle:hover {
  color: var(--accent-blue);
  border-color: var(--accent-blue);
}

.music-icon {
  width: 20px;
  height: 20px;
}

/* Container */
.hero__container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3xl);
  align-items: center;
}

.hero__content {
  z-index: 1;
}

.hero__title {
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: var(--space-lg);
}

.hero__title-line {
  display: block;
}

.hero__subtitle {
  font-size: var(--font-size-lg);
  color: var(--text-muted);
  margin-bottom: var(--space-xl);
  max-width: 450px;
}

/* Form */
.hero__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  max-width: 350px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.form-label {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-muted);
}

.form-input {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-2);
  border: 1px solid var(--glass-border-color);
  border-radius: var(--radius-md);
  color: var(--text);
  font-size: var(--font-size-base);
}

.form-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.language-toggle {
  display: flex;
  gap: var(--space-xs);
}

.lang-btn {
  flex: 1;
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-2);
  border: 1px solid var(--glass-border-color);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  transition: all var(--transition-fast);
}

.lang-btn.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

/* Button */
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

.btn--primary:hover {
  background: var(--accent-blue-hover);
  box-shadow: var(--shadow-glow-blue);
  transform: translateY(-2px);
}

.btn--full {
  width: 100%;
  margin-top: var(--space-sm);
}

/* Visual */
.hero__visual {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.hero__orb {
  width: 280px;
  height: 280px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, rgba(67, 97, 238, 0.4), rgba(67, 97, 238, 0.1));
  box-shadow: 
    0 0 60px rgba(67, 97, 238, 0.3),
    inset 0 0 40px rgba(67, 97, 238, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.orb-inner {
  width: 60%;
  height: 60%;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 214, 10, 0.3), rgba(67, 97, 238, 0.3));
  box-shadow: 0 0 30px rgba(255, 214, 10, 0.2);
}

.hero__symbols {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.symbol {
  position: absolute;
  font-size: 2.5rem;
  font-weight: 700;
  opacity: 0.6;
}

.symbol--1 { top: 10%; left: 10%; color: var(--accent-gold); }
.symbol--2 { top: 5%; right: 20%; color: var(--accent-blue); }
.symbol--3 { bottom: 15%; right: 10%; color: var(--accent-gold); }
.symbol--4 { bottom: 25%; left: 15%; color: var(--accent-blue); }

/* Scroll */
.hero__scroll {
  position: absolute;
  bottom: var(--space-xl);
  left: 50%;
  transform: translateX(-50%);
  color: var(--text-subtle);
}

.scroll-icon {
  width: 28px;
  height: 28px;
}

@media (max-width: 968px) {
  .hero__container {
    grid-template-columns: 1fr;
    text-align: center;
  }

  .hero__subtitle {
    margin: 0 auto var(--space-xl);
  }

  .hero__form {
    margin: 0 auto;
  }

  .hero__visual {
    order: -1;
    height: 300px;
  }

  .hero__orb {
    width: 200px;
    height: 200px;
  }
}
</style>
