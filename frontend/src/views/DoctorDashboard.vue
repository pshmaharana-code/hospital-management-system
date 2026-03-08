<script setup>
import { ref, onMounted} from 'vue'
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import axios from 'axios';

// 1. open the vault
const authStore = useAuthStore()
const router = useRouter()

// 2. state the variable for massive API Payload
const dashboardData = ref(null)
const isLoading = ref(true)
const errorMessage = ref(null)

// Fetch the data from flask
const fetchDashboard = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/doctor/dashboard', {
            headers: {Authorization: `Bearer ${authStore.token}`}
        })
        dashboardData.value = response.data
    } catch (error) {
        console.error("Failed to load dashboard:", error)
        errorMessage.value = "Could not load dashboard data."
    } finally {
        isLoading.value = false
    }
}

// Handle Logout
const handleLogout = () => {
    authStore.logout()  // this instantly implies the vault
    router.push('/login')   // change the channel back to the login page.
}

// Placeholder for Consultation features
const startConsultation = (appointmentId) => {
    alert(`we wil build the consultation form for appointment #${appointmentId} nexd!`)
} 

onMounted(() => {
    fetchDashboard()
}) 
</script>

<template>
    <div class="dashboard-container">
        <div class="dashboard-header">
            <h2>Doctor Dashboard</h2>
            <button @click="handleLogout" class="logout-btn">Logout</button>
        </div>

        <div v-if="isLoading" class="loading-state">Loading your schedule...</div>
        <div v-else-if="errorMessage" class="error-message">{{ errorMessage }}</div>

        <div v-else>
            <div class="info-card">
                <h3>Welcome Dr. {{ dashboardData.doctor_name }}</h3>
                <p><strong>Department:</strong>{{ dashboardData.department || 'Not Assigned' }}</p>
            </div>

            <div class="appointments-section">
                <h3>Today's & Upcomming Patients</h3>

                <div v-if="dashboardData.upcoming_appointments.length > 0" class="table-responsive">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Time</th>
                                <th>Patient Name</th>
                                <th>Contact</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="appt in dashboardData.upcoming_appointments" :key="appt.id">
                                <td><strong>{{ appt.date }}</strong></td>
                                <td>{{ appt.time }}</td>
                                <td>{{ appt.patient_name }}</td>
                                <td>{{ appt.patient_contact }}</td>
                                <td>
                                    <button @click="startConsultation(appt.id)" class="btn-primary">
                                        Consult Patient
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div v-else class="empty-state">
                    <p>You have no upcoming appointmetn in your queue.</p>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.dashboard-container { max-width: 1000px; margin: 2rem auto; padding: 1rem; font-family: Arial, sans-serif; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
.dashboard-header h2 { margin: 0; color: #2c3e50; }

.info-card { background: #e8f4f8; padding: 1.5rem; border-radius: 8px; border-left: 5px solid #3498db; margin-bottom: 2rem; }
.info-card h3 { margin-top: 0; color: #2980b9; }

/* Table Styles */
.appointments-section h3 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 0.5rem; }
.table-responsive { overflow-x: auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 1rem; }
.data-table { width: 100%; border-collapse: collapse; text-align: left; }
.data-table th, .data-table td { padding: 1rem; border-bottom: 1px solid #eee; }
.data-table th { background-color: #f8f9fa; color: #2c3e50; }

/* Buttons */
.btn-primary { background-color: #2ecc71; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
.btn-primary:hover { background-color: #27ae60; }
.logout-btn { padding: 0.5rem 1.2rem; background-color: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
.logout-btn:hover { background-color: #c0392b; }

.empty-state { text-align: center; padding: 3rem; background: #f9f9f9; border-radius: 8px; color: #7f8c8d; margin-top: 1rem; }
.loading-state { text-align: center; padding: 3rem; color: #3498db; font-weight: bold; font-size: 1.2rem; }
.error-message { color: #e74c3c; text-align: center; font-weight: bold; padding: 2rem; }
</style>