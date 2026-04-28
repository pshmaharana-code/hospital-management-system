<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// --- VUE 3 REACTIVITY (Goodbye data() block!) ---
// We use ref('') to create reactive variables. 
// When the user types in the input boxes, these update automatically!
const identifier = ref('')
const password = ref('')
const errorMessage = ref('')

const router = useRouter() // Activate the router.
const authStore = useAuthStore() //Activate the Vault.

// --- THE LOGIN ACTION ---
// This function runs when the user clicks the "Login" button
const handleLogin = async () => {
  // Clear any old error messages first
  errorMessage.value = ''

  try {
    // 1. Axios (the mail carrier) takes our data and POSTs it to Flask on Port 5000
    // Notice we use .value to get the actual text typed by the user
    const response = await axios.post('http://127.0.0.1:5000/api/login', {
      username: identifier.value,
      password: password.value,
    })

    // 2. If Flask says "200 OK", we save the data to the Vault.
    const data = response.data
    authStore.saveLogin(data.access_token, data.user, data.user.role)

    // Alert for testin , then redirect based on role.
    alert(`Welcome ${data.user.username}! You are logged in as ${data.user.role}.`)

    // 3. Send them to dashboard.
    if (data.user.role == 'patient') {
      router.push('/patient-dashboard')
    } else if (data.user.role == 'admin') {
      router.push('/admin-dashboard')
    } else {
      router.push('/doctor-dashboard')
    }
  } catch (error) {
    console.error("Login Failed:", error)
    
    // CRITICAL FIX: We tell Vue to look inside Flask's error response payload (error.response.data.msg). 
    // If Flask didn't send a specific message, ONLY THEN do we fall back to the generic "Invalid credentials" string.
    errorMessage.value = error.response?.data?.msg || "Invalid username or password. Please try again."
  }
}
</script>


<template>
    <div class="login-page">
        <div class="aura-container">
            <div class="aura-blob aura-blob-1"></div>
            <div class="aura-blob aura-blob-2"></div>
        </div>

        <div class="login-wrapper">
            <div class="brand-header" @click="$router.push('/')">
                <div class="logo-mark">+</div>
                <span class="logo-text">ApexMedical</span>
            </div>

            <div class="login-card">
                <div class="card-header">
                    <h2>System Login</h2>
                    <p>Sign in to access your secure portal.</p>
                </div>

                <form class="login-form" @submit.prevent="handleLogin">
                    <div class="input-group">
                        <label for="identifier">Email Address or Username</label>
                        <input 
                            type="text" 
                            id="identifier"
                            v-model="identifier"
                            placeholder="e.g. smith123@gmail.com or dr_smith" 
                            required 
                        />
                    </div>

                    <div class="input-group">
                        <label for="password">Password</label>
                        <input 
                            type="password" 
                            id="password"
                            v-model="password"
                            placeholder="••••••••" 
                            required 
                        />
                    </div>

                    <div class="form-options">
                        <label class="remember-me">
                            <input type="checkbox" />
                            <span>Remember me</span>
                        </label>
                        <router-link to="/forgot-password" class="forgot-link">Forgot Password?</router-link>
                    </div>

                    <div v-if="errorMessage" class="error-alert">
                        {{ errorMessage }}
                    </div>

                    <button type="submit" class="btn-primary">Secure Login</button>
                </form>

                <div class="register-prompt">
                    New user? <router-link to="/register">Register here</router-link>
                </div>
            </div>
        </div>
    </div>
</template>



<style>
/* --- BASE SETUP & AURA --- */
.login-page {
    font-family: 'Inter', -apple-system, sans-serif;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #f0f9ff 0%, #e6f2f2 100%);
    position: relative;
    overflow: hidden;
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
.login-wrapper {
    position: relative;
    z-index: 10;
    width: 100%;
    max-width: 440px;
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
.login-card {
    width: 100%;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.7) 0%, rgba(255, 255, 255, 0.3) 100%);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.9);
    border-radius: 24px;
    padding: 3rem 2.5rem;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0,0,0,0.05);
}

.card-header { text-align: center; margin-bottom: 2.5rem; }
.card-header h2 { color: #0f172a; font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; letter-spacing: -0.5px; }
.card-header p { color: #64748b; font-size: 0.95rem; }

/* --- FORM INPUTS --- */
.login-form { display: flex; flex-direction: column; gap: 1.5rem; }

.input-group { display: flex; flex-direction: column; gap: 0.5rem; }
.input-group label { font-size: 0.85rem; font-weight: 600; color: #334155; }

.input-group input {
    padding: 0.9rem 1.2rem;
    border-radius: 12px;
    border: 1px solid #cbd5e1;
    background: rgba(255, 255, 255, 0.9);
    font-size: 0.95rem;
    color: #0f172a;
    transition: all 0.3s ease;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
}

.input-group input:focus {
    outline: none;
    border-color: #0f766e;
    box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.1);
    background: #ffffff;
}

.input-group input::placeholder {
    color: #94a3b8;
    font-weight: 400;
}

/* --- FORM OPTIONS --- */
.form-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
    margin-top: -0.5rem;
}

.remember-me { display: flex; align-items: center; gap: 0.5rem; color: #475569; cursor: pointer; }
.remember-me input { accent-color: #0f766e; width: 16px; height: 16px; cursor: pointer; margin: 0; }

.forgot-link { color: #0f766e; text-decoration: none; font-weight: 600; transition: color 0.2s; }
.forgot-link:hover { color: #042f2c; }

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

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(15, 118, 110, 0.4);
}

.register-prompt {
    text-align: center;
    margin-top: 2rem;
    font-size: 0.9rem;
    color: #64748b;
}

.register-prompt a {
    color: #0f766e;
    font-weight: 600;
    text-decoration: none;
    transition: color 0.2s;
}

.register-prompt a:hover { color: #042f2c; text-decoration: underline; }
</style>