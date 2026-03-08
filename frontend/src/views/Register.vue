<script setup>
import { ref } from 'vue'
import axios from 'axios';
import { useRouter } from 'vue-router';

const router = useRouter()

const form = ref({
    name: '',
    contact: '',
    username: '',
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
    <div class="auth-container">
        <div class="auth-card">
            <h2>Create an Account</h2>
            <p class="subtitle">Join the Hospital Management System</p>

            <form @submit.prevent="handleRegister">
                <div class="form-group">
                    <label>Full Name</label>
                    <input type="text" v-model="form.name" required placeholder="John Deo" />
                </div>
                <div class="form-group">
                    <label>Contact Number</label>
                    <input type="text" v-model="form.contact" required placeholder="Phone Number" />
                </div>
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" v-model="form.username" required placeholder="Choose a username" />
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" v-model="form.password" required placeholder="Create a password" />
                </div>
                <div v-if="errorMessage" class="error-message">
                    {{ errorMessage }}
                </div>
                <button type="submit" class="btn-primary" :disabled="isLoading">
                    {{ isLoading ? 'Registering...' : 'Sign Up' }}
                </button>
            </form>
            <div class="auth-footer">
                <p>Already have an account? <router-link to="/login">Log in here</router-link></p>
            </div>
        </div>
    </div>
</template>

<style scoped>
.auth-container { display: flex; justify-content: center; align-items: center; min-height: 80vh; }
.auth-card { background: white; padding: 2.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
h2 { margin-top: 0; margin-bottom: 0.5rem; text-align: center; color: #2c3e50; }
.subtitle { text-align: center; color: #7f8c8d; margin-bottom: 2rem; }

.form-group { margin-bottom: 1.2rem; }
label { display: block; font-weight: bold; margin-bottom: 0.5rem; color: #34495e; font-size: 0.9rem; }
input { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
input:focus { outline: none; border-color: #3498db; box-shadow: 0 0 0 2px rgba(52,152,219,0.2); }

.btn-primary { width: 100%; background-color: #3498db; color: white; padding: 0.8rem; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 1rem; transition: background 0.2s; }
.btn-primary:hover:not(:disabled) { background-color: #2980b9; }
.btn-primary:disabled { opacity: 0.7; cursor: not-allowed; }

.error-message { color: #e74c3c; font-size: 0.9rem; margin-top: 0.5rem; text-align: center; }
.auth-footer { margin-top: 1.5rem; text-align: center; font-size: 0.9rem; }
.auth-footer a { color: #3498db; text-decoration: none; font-weight: bold; }
.auth-footer a:hover { text-decoration: underline; }
</style>