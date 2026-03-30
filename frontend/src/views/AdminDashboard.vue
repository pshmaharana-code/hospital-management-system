<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { mapActions } from 'pinia';

// 1. open the vault
const authStore = useAuthStore()
const router = useRouter()

const activeTab = ref('overview')
const stats = ref({
    total_doctors: 0,
    total_patients: 0,
    total_appointments: 0,
    total_activity: []
})

const isLoading = ref(true)
const errorMessage = ref('')

const fetchDashboard = async () => {
    try {
        const response = await axios.get('https://127.0.0.1:5000/api/admin/dashboard', {
            headers: {Authorization: `Bearer ${authStore.token}`}
        })
        stats.value = response.data
    } catch (error) {
        console.error("Failed to load admin dashboard:", error)
        errorMessage.value = "Could not load hospital analytics. Are you logged in as Admin?"
    } finally {
        isLoading = false
    }
}

const handleLogout = () => {
    authStore.logout()  // this instantly implies the vault
    router.push('/login')   // change the channel back to the login page.
}
</script>

<template>
    <div class="dashboard-container">
        
        <div class="dashboard-header">
            <h2>Admin Command Center</h2>
            <button @click="handleLogout" class="logout-btn">Logout</button>
        </div>

        <div class="tabs">
            <button :class="{ active: activeTab === 'overview' }" @click="activeTab = 'overview'">
                System Overview
            </button>
            <button :class="{ active: activeTab === 'staff'}" @click="activeTab = 'staff'">
                Manage Staff
            </button>
        </div>
        <div v-if="isLoading" class="loading-state">Aggregating hospital data...</div>
        <div v-else-if="errorMessage" class="error-message">{{ errorMessage }}</div>

        <div v-else>
            <!-- Tab1: Analytic Overview -->
            <div v-if="activeTab === 'overview'" class="tab-content">
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Patients</h3>
                        <p class="stat-number">{{ stats.total_patients }}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Total Doctors</h3>
                        <p class="stat-number">{{ stats.total_doctors }}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Total Appointments</h3>
                        <p class="stat-number">{{ stats.total_appointments }}</p>
                    </div>
                </div>

                <div class="recent-activity">
                    <h3>Live Hospital Feed (Recent Appointments)</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Appt ID</th>
                                <th>Date</th>
                                <th>Doctor</th>
                                <th>Patient</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="appt in stats.recent_activity" :key="appt.id">
                                <td><strong>#{{ appt.id }}</strong></td>
                                <td>{{ appt.date }}</td>
                                <td>Dr. {{ appt.doctor }}</td>
                                <td>{{ appt.patient }}</td>
                                <td><span :class="['status-badge', appt.status.toLowerCase()]">{{ appt.status }}</span></td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="stats.recent_activity.length === 0" class="empty-state">
                        <p>No activity found in the system.</p>
                    </div>
                </div>
            </div>
            <!-- Tab 2: Staff Management (Placeholder for next step) -->
            <div v-if="activeTab === 'staff'" class="tab-content">
                <div class="empty-state">
                    <h3>Staff Management Engine</h3>
                    <p>This secure sector is reversed for registering new Doctor into the HMS</p>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* Core Layout (Matching existing HMS styles) */
.dashboard-container { max-width: 1100px; margin: 2rem auto; padding: 1rem; font-family: Arial, sans-serif; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 3px solid #2c3e50; padding-bottom: 1rem; }
.dashboard-header h2 { color: #2c3e50; margin: 0; }
.logout-btn { background-color: #e74c3c; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }

/* Tabs */
.tabs { display: flex; gap: 10px; margin-bottom: 1rem; border-bottom: 2px solid #eee; }
.tabs button { padding: 10px 20px; border: none; background: none; font-size: 1rem; font-weight: bold; color: #7f8c8d; cursor: pointer; border-bottom: 3px solid transparent; transition: 0.2s; }
.tabs button.active { color: #8e44ad; border-bottom-color: #8e44ad; }
.tab-content { background: white; padding: 2rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }

/* Analytics Cards */
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 3rem; }
.stat-card { background: #f8f9fa; padding: 2rem; border-radius: 8px; text-align: center; border-top: 4px solid #8e44ad; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.stat-card h3 { margin: 0 0 1rem 0; color: #7f8c8d; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px; }
.stat-number { font-size: 3rem; font-weight: bold; color: #2c3e50; margin: 0; }

/* Data Table */
.recent-activity h3 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 0.5rem; margin-bottom: 1.5rem; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 1rem; border-bottom: 1px solid #eee; text-align: left; }
.data-table th { background: #f8f9fa; color: #2c3e50; }

/* Status Badges */
.status-badge { padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
.status-badge.booked { background: #e8f4f8; color: #3498db; }
.status-badge.completed { background: #e8f8f5; color: #27ae60; }
.status-badge.cancelled { background: #fdedec; color: #e74c3c; }

/* States */
.error-message { background: #ffeaa7; color: #d63031; padding: 1rem; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 1rem; }
.empty-state, .loading-state { text-align: center; padding: 3rem; color: #7f8c8d; font-style: italic; background: #f8f9fa; border-radius: 8px; }
</style>