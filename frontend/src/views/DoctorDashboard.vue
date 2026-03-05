<script setup>
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';

// 1. open the vault
const authStore = useAuthStore()
const router = useRouter()

const handleLogout = () => {
    authStore.logout()  // this instantly implies the vault
    router.push('/')   // change the channel back to the login page.
}
</script>

<template>
    <div class="dashboard-container">
        <h2>Doctor Dashboard</h2>

        <div class="welcome-card" v-if="authStore.user">
            
            <h3>Welcome Dr. {{  authStore.user.username }}!</h3>
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