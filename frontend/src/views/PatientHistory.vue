<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore()
const history = ref([])

const fetchHistory = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/patient/history', {
            headers: { Authorization: `Bearer ${authStore.token}`}
        })
        history.value = response.data
    } catch (error) {
        console.log("Failed to fetch history:", error)
        alert("Could not load your appointment history.")
    }
}

onMounted(() => {
    fetchHistory()
})
</script>

<template>
    <div class="history-container">
        <div class="header-section">
            <h2>My Medical History</h2>
            <router-link to="/patient-dashboard" class="back-link">&larr; Back to Dashboard</router-link>
        </div>

        <div v-if="history.length > 0" class="table-responsive">
            <table class="data-table">
                <thead>
                <tr>
                    <th>Date</th>
                    <th>Doctor</th>
                    <th>Status</th>
                    <th>Medical Details</th> </tr>
                </thead>
                <tbody>
                <tr v-for="appt in history" :key="appt.id">
                    <td>
                    <strong>{{ appt.date }}</strong><br>
                    <span class="time-text">{{ appt.time }}</span>
                    </td>
                    <td>
                    <strong>Dr. {{ appt.doctor_name }}</strong><br>
                    <span class="time-text">{{ appt.department }}</span>
                    </td>
                    <td>
                    <span :class="['status-badge', appt.status.toLowerCase()]">
                        {{ appt.status }}
                    </span>
                    </td>
                    
                    <td class="medical-cell">
                    <p><strong>Diagnosis:</strong> {{ appt.diagnosis }}</p>
                    <p><strong>Prescription:</strong> {{ appt.prescription }}</p>
                    <p class="notes-text"><strong>Notes:</strong> {{ appt.notes }}</p>
                    </td>
                </tr>
                </tbody>
            </table>
        </div>

        <div v-else class="empty-state">
            <p>You have no past appointments on record.</p>
        </div>
    </div>
</template>

<style scoped>
.history-container { max-width: 1000px; margin: 2rem auto; padding: 1rem; }
.header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
.back-link { color: #3498db; text-decoration: none; font-weight: bold; }
.back-link:hover { text-decoration: underline; }

/* Table Styles */
.table-responsive { overflow-x: auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.data-table { width: 100%; border-collapse: collapse; text-align: left; }
.data-table th, .data-table td { padding: 1rem; border-bottom: 1px solid #eee; }
.data-table th { background-color: #f8f9fa; color: #2c3e50; }
.time-text { font-size: 0.85rem; color: #7f8c8d; }
.notes-cell { max-width: 250px; font-style: italic; color: #555; }

/* Status Badges */
.status-badge { padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.85rem; font-weight: bold; }
.status-badge.completed { background-color: #e8f8ec; color: #27ae60; }
.status-badge.cancelled { background-color: #fce4e4; color: #c0392b; }

.empty-state { text-align: center; padding: 3rem; background: #f9f9f9; border-radius: 8px; color: #7f8c8d; }
.medical-cell p { margin: 0 0 0.3rem 0; font-size: 0.9rem; }
.notes-text { font-style: italic; color: #555; }
</style>