<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import gsap from 'gsap'

const router = useRouter()
const authStore = useAuthStore()

const handleActionClick = () => {
    if (authStore.isAuthenticated) {
        if (authStore.user?.role === 'doctor') {
            router.push('/doctor-dashboard')
        } else {
            router.push('/patient-dashboard')
        }
    } else {
        router.push('/login')
    }
}

const handleBookClick = () => {
    if (authStore.isAuthenticated) {
        router.push('/book-appointment')
    } else {
        alert("Please login as a patient to book an appointment.")
        router.push('/login')
    }
}

onMounted(() => {
    // 1. Navbar drops in
    gsap.fromTo('.navbar', 
        { y: -50, opacity: 0 }, 
        { y: 0, opacity: 1, duration: 1, ease: 'power3.out' }
    )

    // 2. Hero Text Stagger
    gsap.fromTo(['.badge', '.hero-title', '.hero-subtitle', '.hero-actions'], 
        { y: 40, opacity: 0 }, 
        { y: 0, opacity: 1, duration: 1, stagger: 0.2, ease: 'power3.out', delay: 0.2 }
    )

    // 3. Floating Glass Cards Reveal
    gsap.fromTo('.glass-card',
        { y: 60, opacity: 0, scale: 0.9 },
        { y: 0, opacity: 1, scale: 1, duration: 1.2, stagger: 0.2, ease: 'back.out(1.2)', delay: 0.6 }
    )

    // 4. Continuous Floating Animation for the cards
    gsap.to('.card-top', { y: -15, duration: 3, repeat: -1, yoyo: true, ease: 'sine.inOut', delay: 2 })
    gsap.to('.card-main', { y: -20, duration: 4, repeat: -1, yoyo: true, ease: 'sine.inOut', delay: 2.5 })
    gsap.to('.card-bottom', { y: -10, duration: 3.5, repeat: -1, yoyo: true, ease: 'sine.inOut', delay: 2.2 })

    // 5. Stronger Dynamic Aura Background
    gsap.to('.aura-blob-1', { x: 150, y: 150, duration: 15, repeat: -1, yoyo: true, ease: 'sine.inOut' })
    gsap.to('.aura-blob-2', { x: -150, y: -100, duration: 20, repeat: -1, yoyo: true, ease: 'sine.inOut', delay: 2 })
})
</script>

<template>
    <div class="landing-page">
        <div class="aura-container">
            <div class="aura-blob aura-blob-1"></div>
            <div class="aura-blob aura-blob-2"></div>
        </div>

        <div class="announcement-wrapper">
            <div class="announcement-bar">
                <span class="pulse-dot"></span>
                <p><strong>Ranked #1</strong> Regional Hospital for Cardiology & Neurology</p>
            </div>
        </div>

        <nav class="navbar">
            <div class="nav-brand">
                <div class="logo-mark">+</div>
                <span class="logo-text">ApexMedical</span>
            </div>
            
            <div class="nav-links">
                <a href="#services">Specialties</a>
                <a href="#doctors">Our Doctors</a>
                <a href="#contact">Contact</a>
            </div>

            <button @click="handleActionClick" class="btn-nav">
                {{ authStore.isAuthenticated ? 'Go to Dashboard' : 'Patient Login' }}
            </button>
        </nav>

        <header class="hero-section">
            <div class="hero-content">
                <div class="badge">Premium Healthcare</div>
                <h1 class="hero-title">Exceptional Care,<br> Without the Wait.</h1>
                <p class="hero-subtitle">
                    Experience a new standard of medical excellence. Book appointments instantly, manage your records securely, and connect with top-tier specialists.
                </p>
                
                <div class="hero-actions">
                    <button @click="handleBookClick" class="btn-primary">
                        Book an Appointment
                    </button>
                    <button @click="handleActionClick" class="btn-secondary">
                        Access Portal
                    </button>
                </div>
            </div>

            <div class="hero-visual">
                <div class="floating-ui-container">
                    
                    <div class="glass-card card-top">
                        <div class="icon-circle teal"></div>
                        <div class="lines">
                            <div class="line short"></div>
                            <div class="line long"></div>
                        </div>
                    </div>

                    <div class="glass-card card-main">
                        <div class="card-avatar"></div>
                        <div class="card-info">
                            <h4>Dr. Sarah Jenkins</h4>
                            <p>Senior Cardiologist</p>
                        </div>
                        <div class="status-badge">Available Today</div>
                    </div>

                    <div class="glass-card card-bottom">
                        <span class="time-slot">10:30 AM</span>
                        <span class="time-slot active">11:00 AM</span>
                        <span class="time-slot">01:15 PM</span>
                    </div>

                </div>
            </div>
        </header>
    </div>
</template>

<style scoped>
/* --- BASE SETUP --- */
.landing-page {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    min-height: 100vh;
    color: #0f172a;
    position: relative;
    overflow-x: hidden;
    /* Replaced flat gray with a very soft, cool blue-tinted gradient */
    background: linear-gradient(135deg, #f0f9ff 0%, #e6f2f2 100%); 
}

/* --- 2. MORE VIBRANT AURA --- */
.aura-container {
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    z-index: 0; pointer-events: none;
}

.aura-blob {
    position: absolute;
    width: 800px; /* Made them larger to fill the white space */
    height: 800px;
    border-radius: 50%;
    filter: blur(90px); /* Tighter blur for more intense color */
    opacity: 0.65;
    mix-blend-mode: multiply;
}

/* Deepened the colors so they pop through the glass */
.aura-blob-1 { background: #7dd3fc; top: -10%; left: -5%; } 
.aura-blob-2 { background: #34d399; bottom: 0%; right: -5%; }

/* --- NEW ANNOUNCEMENT PILL --- */
.announcement-wrapper {
    display: flex;
    justify-content: center;
    padding-top: 1.5rem;
    position: relative;
    z-index: 101;
}

.announcement-bar {
    background: linear-gradient(90deg, #0f172a, #1e293b);
    color: #f8fafc;
    padding: 0.5rem 1.5rem;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 12px;
    border-radius: 30px; /* Transforms it into a sleek pill */
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.15); /* Soft drop shadow */
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.pulse-dot {
    width: 8px;
    height: 8px;
    background-color: #10b981; 
    border-radius: 50%;
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* --- UPGRADED FLOATING NAVBAR --- */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    margin: 1.5rem 5% 0; 
    position: sticky;
    top: 1.5rem; 
    z-index: 100;
    
    /* True Translucent Glass Gradient */
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.5) 0%, rgba(255, 255, 255, 0.1) 100%);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: 24px; 
    box-shadow: 0 8px 32px rgba(15, 118, 110, 0.08); /* Slight teal tint in the shadow */
}

.nav-brand { display: flex; align-items: center; gap: 0.6rem; }
.logo-mark { background: #0f766e; color: white; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 10px; font-weight: bold; font-size: 1.2rem; }
.logo-text { font-size: 1.3rem; font-weight: 800; color: #0f172a; letter-spacing: -0.5px; }
.nav-links a { text-decoration: none; color: #64748b; font-weight: 600; font-size: 0.95rem; margin: 0 1.5rem; transition: color 0.3s; }
.nav-links a:hover { color: #0f766e; }

.btn-nav { 
    background: white; 
    border: 1px solid #e2e8f0; 
    padding: 0.6rem 1.5rem; 
    border-radius: 30px; 
    font-weight: 600; 
    color: #0f172a; 
    cursor: pointer; 
    transition: all 0.3s ease; 
    box-shadow: 0 2px 10px rgba(0,0,0,0.02);
}
.btn-nav:hover { border-color: #0f766e; color: #0f766e; box-shadow: 0 4px 15px rgba(15, 118, 110, 0.1); }

/* --- HERO SECTION TWEAK --- */
/* Just make sure your hero section has a little less top padding now so it doesn't feel too distant */
.hero-section {
    position: relative;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6rem 5% 4rem; /* Adjusted top padding from 8rem to 6rem */
    max-width: 1400px;
    margin: 0 auto;
}

.hero-content {
    flex: 1;
    max-width: 600px;
}

.badge { display: inline-block; background: rgba(255,255,255,0.8); border: 1px solid #e2e8f0; color: #0f766e; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 1.5rem; }
.hero-title { font-size: 4rem; font-weight: 800; line-height: 1.1; color: #0f172a; margin-bottom: 1.5rem; letter-spacing: -1.5px; }
.hero-subtitle { font-size: 1.2rem; line-height: 1.6; color: #475569; margin-bottom: 2.5rem; }

/* --- BUTTONS --- */
.hero-actions { display: flex; gap: 1rem; }
.btn-primary { background: #0f766e; color: white; border: none; padding: 1rem 2rem; border-radius: 8px; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: transform 0.2s ease, box-shadow 0.2s ease; box-shadow: 0 4px 14px rgba(15, 118, 110, 0.25); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(15, 118, 110, 0.4); }
.btn-secondary { background: rgba(255,255,255,0.5); backdrop-filter: blur(4px); color: #0f172a; border: 2px solid #cbd5e1; padding: 1rem 2rem; border-radius: 8px; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
.btn-secondary:hover { background: white; border-color: #94a3b8; }

/* --- NEW FLOATING UI (SKEUOMORPHIC) --- */
.hero-visual {
    flex: 1;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    position: relative;
    height: 500px;
}

.floating-ui-container {
    position: relative;
    width: 450px;
    height: 100%;
}

.glass-card {
    position: absolute;
    /* True Translucent Glass Gradient */
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.5) 0%, rgba(255, 255, 255, 0.1) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: 20px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.05);
    padding: 1.5rem;
}

/* Small top card */
.card-top {
    top: 10%;
    left: 10%;
    width: 220px;
    display: flex;
    align-items: center;
    gap: 1rem;
    z-index: 2;
}

.icon-circle { width: 40px; height: 40px; border-radius: 50%; }
.icon-circle.teal { background: #ccfbf1; border: 2px solid #14b8a6; }
.lines { display: flex; flex-direction: column; gap: 8px; flex: 1; }
.line { height: 8px; border-radius: 4px; background: #e2e8f0; }
.line.short { width: 60%; }
.line.long { width: 100%; }

/* Main center card */
.card-main {
    top: 30%;
    right: 5%;
    width: 320px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    z-index: 3;
    /* I REMOVED the solid white background override that was ruining this card! */
}

.card-avatar {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, #0f766e, #38bdf8);
    border-radius: 50%;
    margin-bottom: 1rem;
    border: 4px solid white;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

.card-info h4 { margin: 0 0 0.2rem 0; color: #0f172a; font-size: 1.2rem; }
.card-info p { margin: 0 0 1rem 0; color: #64748b; font-size: 0.9rem; }
.status-badge { background: #dcfce7; color: #166534; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }

/* Bottom time slots card */
.card-bottom {
    bottom: 15%;
    left: 0;
    width: 300px;
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    z-index: 4;
}

.time-slot {
    /* Changed from solid white to sheer glass */
    background: rgba(255, 255, 255, 0.3);
    padding: 0.6rem 0.8rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.5);
}

.time-slot.active {
    background: #0f766e;
    color: white;
    border-color: #0f766e;
    box-shadow: 0 4px 10px rgba(15, 118, 110, 0.3);
}
</style>