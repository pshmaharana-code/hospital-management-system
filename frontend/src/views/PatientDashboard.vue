<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import axios from 'axios';


// 1. open the vault
const authStore = useAuthStore()
const router = useRouter()

// 3. Create a reactive variable to hold the appointments once they arrive from Flask
const appointments = ref([])

const fetchDashboardData = async () => {
    try {
        // We must pin the VIP Badge (token) to the header of our request
        const response = await axios.get('http://127.0.0.1:5000/api/patient/dashboard',{
            headers: {
                Authorization: `Bearer ${authStore.token}`
            }
        })
        // Look at the Flask code: you named the list "upcomming_appointments"
        appointments.value = response.data.upcomming_appointments

        console.log('Appointments fetched successfully', appointments.value)
    } catch (error) {
        console.log('Failed to fetch dashboard data:', error)
        if (error.response && error.response.status == 401) {
            alert("Your session expaired. Please log in again.")
            handleLogout()
        }
    }
}

// 5. onMounted runs exactly ONE time, the millisecond the page loads
onMounted(() => {
    fetchDashboardData()
})


const handleLogout = () => {
    authStore.logout()  // this instantly implies the vault
    router.push('/')   // change the channel back to the login page.
}
</script>

<template>
    <div class="dashboard-container">
        <h2>Patient Dashboard</h2>

        <div class="welcome-card" v-if="authStore.user">
            
            <h3>Welcome back, {{  authStore.user.username }}!</h3>
            <p>Your Role: {{ authStore.user.role }}</p>

            <button @click="handleLogout" class="logout-btn">Logout</button>

        </div>
    </div>
</template>

<style scoped>
.dashboard-container {
    max-width: 600px;
    margin: 3rem auto;
    text-align: center;
    font-family: Arial, sans-serif;
}

.welcome-card {
    background: #e8f4f8;
    padding: 2rem;
    border-radius: 8px;
    border: 1px solid #bce8f1;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.logout-btn {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}
.logout-btn:hover {
  background-color: #c0392b;
}
</style>

