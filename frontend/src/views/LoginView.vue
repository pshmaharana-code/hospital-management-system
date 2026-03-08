<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// --- VUE 3 REACTIVITY (Goodbye data() block!) ---
// We use ref('') to create reactive variables. 
// When the user types in the input boxes, these update automatically!
const username = ref('')
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
      username: username.value,
      password: password.value
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
    // 4. If Flask says "401 Unauthorized" (wrong password), we show an error on the screen
    console.error("Login Failed:", error)
    errorMessage.value = "Invalid username or password. Please try again."
  }
}
</script>


<template>
  <div class="login-container">
    <h2>System Login</h2>

    <form @submit.prevent="handleLogin">
      <div class="input-group">
        <label>Username</label>
        <input type="text" v-model="username" required />
      </div>

      <div class="input-group">
        <label>Passowrd</label>
        <input type="password" v-model="password" required />
      </div>

      <button type="submit">Login</button>
    </form>
    <div class="auth-footer" style="margin-top: 1.5rem; text-align: center; font-size: 0.9rem;">
        <p>New user? <router-link to="/register" style="color: #3498db; font-weight: bold; text-decoration: none;">Register here</router-link></p>
    </div>

    <p v-if="errorMessage">{{ errorMessage }}</p>

  </div>
</template>



<style scoped>
/* A little bit of CSS to make it look like a clean, professional card */
.login-container {
  max-width: 400px;
  margin: 3rem auto;
  padding: 2rem;
  background: #f9f9f9;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.input-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box; 
}

button {
  width: 100%;
  padding: 0.75rem;
  background-color: #2c3e50;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1.1rem;
  cursor: pointer;
}

button:hover {
  background-color: #34495e;
}

.error-msg {
  color: red;
  margin-top: 1rem;
  text-align: center;
  font-weight: bold;
}
</style>