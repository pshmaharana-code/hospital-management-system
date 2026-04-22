<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

// UI State
const currentStep = ref(1) // 1: Username, 2: OTP, 3: New Password
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// Form Data
const username = ref('')
const otp = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

// --- API CALLS ---

const requestResetCode = async () => {
    if (!username.value) return
    isLoading.value = true; errorMessage.value = ''; successMessage.value = ''
    
    try {
        const response = await axios.post('http://127.0.0.1:5000/api/auth/forgot-password', {
            username: username.value
        })
        successMessage.value = response.data.msg
        setTimeout(() => {
            successMessage.value = ''
            currentStep.value = 2 // Move to Step 2!
        }, 1500)
    } catch (error) {
        errorMessage.value = error.response?.data?.msg || "Failed to request code."
    } finally { isLoading.value = false }
}

const verifyCode = async () => {
    if (!otp.value) return
    isLoading.value = true; errorMessage.value = ''; successMessage.value = ''
    
    try {
        const response = await axios.post('http://127.0.0.1:5000/api/auth/verify-otp', {
            username: username.value,
            otp: otp.value
        })
        successMessage.value = response.data.msg
        setTimeout(() => {
            successMessage.value = ''
            currentStep.value = 3 // Move to Step 3!
        }, 1000)
    } catch (error) {
        errorMessage.value = error.response?.data?.msg || "Invalid code."
    } finally { isLoading.value = false }
}

const submitNewPassword = async () => {
    if (newPassword.value !== confirmPassword.value) {
        errorMessage.value = "Passwords do not match!"
        return
    }
    
    isLoading.value = true; errorMessage.value = ''; successMessage.value = ''
    
    try {
        const response = await axios.post('http://127.0.0.1:5000/api/auth/reset-password', {
            username: username.value,
            otp: otp.value,
            password: newPassword.value // Matches your updated Python code!
        })
        successMessage.value = response.data.msg
        
        // Redirect to login after 2 seconds
        setTimeout(() => {
            router.push('/login')
        }, 2000)
    } catch (error) {
        errorMessage.value = error.response?.data?.msg || "Failed to reset password."
    } finally { isLoading.value = false }
}
</script>

<template>
  <div class="recovery-container">
    <div class="recovery-card">
      
      <h2>Password Recovery</h2>
      <p class="subtitle" v-if="currentStep === 1">Enter your username to receive a 6-digit recovery code.</p>
      <p class="subtitle" v-if="currentStep === 2">We've generated a secure code. Please enter it below.</p>
      <p class="subtitle" v-if="currentStep === 3">Code verified! Create your new password.</p>

      <div v-if="errorMessage" class="alert error">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert success">{{ successMessage }}</div>

      <form v-if="currentStep === 1" @submit.prevent="requestResetCode" class="flow-form">
        <div class="input-group">
            <label>Username</label>
            <input type="text" v-model="username" required placeholder="Enter your username" />
        </div>
        <button type="submit" class="btn-primary" :disabled="isLoading">
            {{ isLoading ? 'Sending...' : 'Send Recovery Code' }}
        </button>
      </form>

      <form v-if="currentStep === 2" @submit.prevent="verifyCode" class="flow-form">
        <div class="input-group">
            <label>6-Digit Recovery Code</label>
            <input type="text" v-model="otp" required placeholder="e.g., 123456" maxlength="6" class="text-center letter-spacing" />
        </div>
        <button type="submit" class="btn-primary" :disabled="isLoading">
            {{ isLoading ? 'Verifying...' : 'Verify Code' }}
        </button>
        <button type="button" @click="currentStep = 1" class="btn-link">Cancel / Back</button>
      </form>

      <form v-if="currentStep === 3" @submit.prevent="submitNewPassword" class="flow-form">
        <div class="input-group">
            <label>New Password</label>
            <input type="password" v-model="newPassword" required placeholder="Enter new password" />
        </div>
        <div class="input-group">
            <label>Confirm Password</label>
            <input type="password" v-model="confirmPassword" required placeholder="Confirm new password" />
        </div>
        <button type="submit" class="btn-success" :disabled="isLoading">
            {{ isLoading ? 'Saving...' : 'Reset Password' }}
        </button>
      </form>

      <div class="card-footer" v-if="currentStep === 1">
        <router-link to="/login" class="back-link">&larr; Back to Login</router-link>
      </div>

    </div>
  </div>
</template>

<style scoped>
.recovery-container { display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: #f4f7f6; padding: 1rem; }
.recovery-card { background: white; padding: 2.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); width: 100%; max-width: 400px; text-align: center; }
h2 { margin-top: 0; color: #2c3e50; }
.subtitle { color: #7f8c8d; margin-bottom: 2rem; font-size: 0.95rem; }

.alert { padding: 0.8rem; border-radius: 6px; margin-bottom: 1.5rem; font-weight: bold; font-size: 0.9rem; }
.alert.error { background-color: #fdedec; color: #e74c3c; border: 1px solid #fadbd8; }
.alert.success { background-color: #e8f8f5; color: #27ae60; border: 1px solid #d1f2eb; }

.flow-form { display: flex; flex-direction: column; gap: 1.5rem; }
.input-group { text-align: left; display: flex; flex-direction: column; }
label { font-weight: bold; margin-bottom: 0.5rem; color: #34495e; font-size: 0.9rem; }
input { padding: 0.8rem; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; }
input:focus { outline: none; border-color: #3498db; }

.text-center { text-align: center; }
.letter-spacing { letter-spacing: 5px; font-weight: bold; font-size: 1.2rem; }

.btn-primary { background-color: #3498db; color: white; padding: 0.8rem; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s; font-size: 1rem; }
.btn-primary:hover:not(:disabled) { background-color: #2980b9; }
.btn-success { background-color: #2ecc71; color: white; padding: 0.8rem; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s; font-size: 1rem; }
.btn-success:hover:not(:disabled) { background-color: #27ae60; }
.btn-primary:disabled, .btn-success:disabled { opacity: 0.7; cursor: not-allowed; }

.btn-link { background: none; border: none; color: #95a5a6; cursor: pointer; font-size: 0.9rem; text-decoration: underline; margin-top: -0.5rem;}
.btn-link:hover { color: #7f8c8d; }

.card-footer { margin-top: 2rem; border-top: 1px solid #eee; padding-top: 1.5rem; }
.back-link { color: #3498db; text-decoration: none; font-weight: bold; font-size: 0.9rem; }
.back-link:hover { text-decoration: underline; }
</style>