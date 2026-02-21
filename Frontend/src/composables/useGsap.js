import { onMounted, onUnmounted } from 'vue'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

// Register ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger)

export function useGsap() {
    const ctx = gsap.context(() => { })

    onUnmounted(() => {
        ctx.revert() // Cleanup all GSAP animations
    })

    // Hero text stagger animation
    function animateHeroText(selector, options = {}) {
        return gsap.from(selector, {
            y: 50,
            opacity: 0,
            duration: 1,
            stagger: 0.2,
            ease: 'power3.out',
            ...options
        })
    }

    // Fade up animation for elements
    function animateFadeUp(selector, options = {}) {
        return gsap.from(selector, {
            y: 30,
            opacity: 0,
            duration: 0.8,
            stagger: 0.1,
            ease: 'power2.out',
            ...options
        })
    }

    // ScrollTrigger fade up animation
    function animateOnScroll(selector, options = {}) {
        return gsap.from(selector, {
            y: 40,
            opacity: 0,
            duration: 0.8,
            stagger: 0.15,
            ease: 'power2.out',
            scrollTrigger: {
                trigger: selector,
                start: 'top 80%',
                toggleActions: 'play none none reverse',
                ...options.scrollTrigger
            },
            ...options
        })
    }

    // Floating animation for hero elements
    function animateFloat(selector, options = {}) {
        return gsap.to(selector, {
            y: -15,
            duration: 2,
            repeat: -1,
            yoyo: true,
            ease: 'power1.inOut',
            ...options
        })
    }

    // Scale in animation
    function animateScaleIn(selector, options = {}) {
        return gsap.from(selector, {
            scale: 0.8,
            opacity: 0,
            duration: 1,
            ease: 'back.out(1.5)',
            ...options
        })
    }

    // Glow pulse animation
    function animateGlow(selector) {
        return gsap.to(selector, {
            boxShadow: '0 0 40px rgba(67, 97, 238, 0.5)',
            duration: 1,
            repeat: -1,
            yoyo: true,
            ease: 'power1.inOut'
        })
    }

    return {
        gsap,
        ctx,
        animateHeroText,
        animateFadeUp,
        animateOnScroll,
        animateFloat,
        animateScaleIn,
        animateGlow
    }
}
