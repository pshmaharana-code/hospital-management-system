<script setup>
import { ref } from 'vue'
import axios from 'axios';
import { useRouter } from 'vue-router';

const router = useRouter()

const form = ref({
    name: '',
    contact: '',
    username: '',
    email: '',
    password: ''
})

const errorMessage = ref('')
const isLoading = ref(false)

const handleRegister = async () => {
    errorMessage.value = ''
    isLoading.value = true

    try {
        await axios.post('http://127.0.0.1:5000/api/auth/register', form.value)
        alert("Registration successful! Please log in.")
        router.push('/login')
    } catch (error) {
        if (error.response && error.response.data && error.response.data.msg) {
            errorMessage.value = error.response.data.msg
        } else {
            errorMessage.value = "Registration failed. Please try again."
        }
    } finally {
        isLoading.value = false
    }
}
</script>

<template>
    <div class="auth-page">
        <div class="aura-container">
            <div class="aura-blob aura-blob-1"></div>
            <div class="aura-blob aura-blob-2"></div>
        </div>

        <div class="auth-wrapper">
            <div class="brand-header" @click="$router.push('/')">
                <div class="logo-mark">+</div>
                <span class="logo-text">ApexMedical</span>
            </div>

            <div class="auth-card">
                <div class="card-header">
                    <h2>Create an Account</h2>
                    <p>Join the ApexMedical secure patient portal.</p>
                </div>

                <form class="auth-form" @submit.prevent="handleRegister">
                    
                    <div class="input-group">
                        <label for="name">Full Name</label>
                        <input type="text" id="name" v-model="form.name" required placeholder="e.g. John Doe" />
                    </div>

                    <div class="input-group">
                        <label for="contact">Contact Number</label>
                        <input type="text" id="contact" v-model="form.contact" required placeholder="e.g. +1 (555) 000-0000" />
                    </div>

                    <div class="input-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" v-model="form.username" required placeholder="Choose a unique username" />
                    </div>

                    <div class="input-group">
                        <label for="email">Email Address</label>
                        <input type="email" id="email" v-model="form.email" required placeholder="e.g. john@example.com" />
                    </div>

                    <div class="input-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" v-model="form.password" required placeholder="Create a strong password" />
                    </div>

                    <div v-if="errorMessage" class="error-alert">
                        {{ errorMessage }}
                    </div>

                    <button type="submit" class="btn-primary" :disabled="isLoading">
                        {{ isLoading ? 'Registering...' : 'Secure Sign Up' }}
                    </button>
                </form>

                <div class="login-prompt">
                    Already have an account? <router-link to="/login">Log in here</router-link>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* --- BASE SETUP & AURA --- */
.auth-page {
    font-family: 'Inter', -apple-system, sans-serif;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #f0f9ff 0%, #e6f2f2 100%);
    position: relative;
    overflow: hidden;
    padding: 2rem 0; /* Added padding so top/bottom don't cut off on small screens */
}

.aura-container {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    z-index: 0; pointer-events: none;
}

.aura-blob {
    position: absolute;
    width: 800px; height: 800px;
    border-radius: 50%;
    filter: blur(100px);
    opacity: 0.5;
}

.aura-blob-1 { background: #bae6fd; top: -20%; left: -10%; animation: float 20s infinite alternate ease-in-out; }
.aura-blob-2 { background: #99f6e4; bottom: -20%; right: -10%; animation: float 25s infinite alternate ease-in-out reverse; }

@keyframes float {
    0% { transform: translate(0, 0) scale(1); }
    100% { transform: translate(50px, 50px) scale(1.1); }
}

/* --- WRAPPER & BRAND --- */
.auth-wrapper {
    position: relative;
    z-index: 10;
    width: 100%;
    max-width: 460px; /* Slightly wider than login for the longer form */
    padding: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.brand-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 2rem;
    cursor: pointer;
    transition: transform 0.2s ease;
}

.brand-header:hover { transform: scale(1.02); }

.logo-mark { background: #0f766e; color: white; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 10px; font-weight: bold; font-size: 1.2rem; }
.logo-text { font-size: 1.5rem; font-weight: 800; color: #0f172a; letter-spacing: -0.5px; }

/* --- GLASSMORPHIC CARD --- */
.auth-card {
    width: 100%;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.7) 0%, rgba(255, 255, 255, 0.3) 100%);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.9);
    border-radius: 24px;
    padding: 2.5rem;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0,0,0,0.05);
}

.card-header { text-align: center; margin-bottom: 2rem; }
.card-header h2 { color: #0f172a; font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; letter-spacing: -0.5px; }
.card-header p { color: #64748b; font-size: 0.95rem; }

/* --- FORM INPUTS --- */
.auth-form { display: flex; flex-direction: column; gap: 1.2rem; } /* Tighter gap for longer form */

.input-group { display: flex; flex-direction: column; gap: 0.4rem; }
.input-group label { font-size: 0.85rem; font-weight: 600; color: #334155; }

.input-group input {
    padding: 0.85rem 1.2rem;
    border-radius: 12px;
    border: 1px solid #cbd5e1;
    background: rgba(255, 255, 255, 0.9);
    font-size: 0.95rem;
    color: #0f172a;
    transition: all 0.3s ease;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
}

.input-group input::placeholder { color: #94a3b8; font-weight: 400; }

.input-group input:focus {
    outline: none;
    border-color: #0f766e;
    box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.1);
    background: #ffffff;
}

/* --- ERROR ALERT --- */
.error-alert {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: #dc2626;
    padding: 0.8rem;
    border-radius: 10px;
    font-size: 0.9rem;
    text-align: center;
    font-weight: 600;
}

/* --- BUTTON & FOOTER --- */
.btn-primary {
    background: #0f766e;
    color: white;
    border: none;
    padding: 1rem;
    border-radius: 12px;
    font-size: 1.05rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 14px rgba(15, 118, 110, 0.25);
    margin-top: 0.5rem;
}

.btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(15, 118, 110, 0.4);
}

.btn-primary:disabled {
    opacity: 0.7;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

.login-prompt {
    text-align: center;
    margin-top: 2rem;
    font-size: 0.9rem;
    color: #64748b;
}

.login-prompt a {
    color: #0f766e;
    font-weight: 600;
    text-decoration: none;
    transition: color 0.2s;
}

.login-prompt a:hover { color: #042f2c; text-decoration: underline; }
</style>