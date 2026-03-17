<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import axios from 'axios';

const authStore = useAuthStore()
const router = useRouter()

// --- STATE ---
const dashboardData = ref(null)
const isLoading = ref(true)
const errorMessage = ref('')
const activeTab = ref('appointments') // 'appointments' or 'schedule'

// State for the Schedule Builder
const isSavingSchedule = ref(false)
const scheduleMessage = ref('')
const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

// Initialize a blank 7-day schedule array
const weeklySchedule = ref(daysOfWeek.map((day, index) => ({
    day_of_week: index,
    day_name: day,
    is_working: false,
    morning_start_time: '',
    morning_end_time: '',
    evening_start_time: '',
    evening_end_time: ''
})))

// --- METHODS ---

// Fetch data and populate the schedule form if data exists
const fetchDashboard = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/doctor/dashboard', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        dashboardData.value = response.data

        // Populate the Master Roster form with existing database times
        if (response.data.availability_schedule) {
            response.data.availability_schedule.forEach(savedSlot => {
                const dayObj = weeklySchedule.value.find(d => d.day_of_week === savedSlot.day_of_week)
                if (dayObj) {
                    dayObj.morning_start_time = savedSlot.morning_start_time || ''
                    dayObj.morning_end_time = savedSlot.morning_end_time || ''
                    dayObj.evening_start_time = savedSlot.evening_start_time || ''
                    dayObj.evening_end_time = savedSlot.evening_end_time || ''
                    
                    // If any time exists, mark the day as "Working"
                    if (dayObj.morning_start_time || dayObj.evening_start_time) {
                        dayObj.is_working = true
                    }
                }
            })
        }
    } catch (error) {
        console.error("Failed to load dashboard:", error)
        errorMessage.value = "Could not load dashboard data."
    } finally {
        isLoading.value = false
    }
}

// Save the 7-day roster back to Flask
const saveSchedule = async () => {
    isSavingSchedule.value = true
    scheduleMessage.value = ''
    
    // Clean the data: If marked as NOT working, erase the times for that day
    const payload = weeklySchedule.value.map(day => ({
        day_of_week: day.day_of_week,
        morning_start_time: day.is_working ? day.morning_start_time : '',
        morning_end_time: day.is_working ? day.morning_end_time : '',
        evening_start_time: day.is_working ? day.evening_start_time : '',
        evening_end_time: day.is_working ? day.evening_end_time : ''
    }))

    try {
        await axios.post('http://127.0.0.1:5000/api/doctor/schedule', payload, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        scheduleMessage.value = "Schedule saved successfully!"
        setTimeout(() => scheduleMessage.value = '', 3000)
    } catch (error) {
        console.error("Failed to save schedule:", error)
        scheduleMessage.value = "Failed to save schedule. Please try again."
    } finally {
        isSavingSchedule.value = false
    }
}

const handleLogout = () => {
    authStore.logout()  
    router.push('/login')   
}

const startConsultation = (appointmentId) => {
    alert(`We will build the Consultation Form for appointment #${appointmentId} next!`)
}

onMounted(() => {
    fetchDashboard()
})
</script>

<template>
    <div class="dashboard-container">
        
        <div class="dashboard-header">
            <h2>Doctor Command Center</h2>
            <button @click="handleLogout" class="logout-btn">Logout</button>
        </div>

        <div v-if="isLoading" class="loading-state">Loading your dashboard...</div>
        <div v-else-if="errorMessage" class="error-message">{{ errorMessage }}</div>

        <div v-else>
            <div class="info-card">
                <h3>Welcome, {{ dashboardData.doctor_name }}</h3>
                <p><strong>Department:</strong> {{ dashboardData.department || 'Not Assigned' }}</p>
            </div>

            <div class="tabs">
                <button :class="{ active: activeTab === 'appointments' }" @click="activeTab = 'appointments'">
                    Today's Patients
                </button>
                <button :class="{ active: activeTab === 'schedule' }" @click="activeTab = 'schedule'">
                    Manage Master Schedule
                </button>
            </div>

            <div v-if="activeTab === 'appointments'" class="tab-content">
                <h3>Upcoming Appointments</h3>
                
                <div v-if="dashboardData.upcoming_appointments.length > 0" class="table-responsive">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Time</th>
                                <th>Patient Name</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="appt in dashboardData.upcoming_appointments" :key="appt.id">
                                <td><strong>{{ appt.date }}</strong></td>
                                <td>{{ appt.time }}</td>
                                <td>{{ appt.patient_name }}</td>
                                <td>
                                    <button @click="startConsultation(appt.id)" class="btn-primary">Consult</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div v-else class="empty-state">
                    <p>Your queue is empty. No patients currently booked.</p>
                </div>
            </div>

            <div v-if="activeTab === 'schedule'" class="tab-content">
                <div class="schedule-header">
                    <h3>7-Day Master Roster</h3>
                    <p class="subtitle">Set your standard weekly working hours. Leave a shift blank if you are off.</p>
                </div>

                <form @submit.prevent="saveSchedule" class="schedule-form">
                    <div v-for="day in weeklySchedule" :key="day.day_of_week" class="day-row">
                        
                        <div class="day-toggle">
                            <label class="switch">
                                <input type="checkbox" v-model="day.is_working">
                                <span class="slider round"></span>
                            </label>
                            <span class="day-name" :class="{ 'text-disabled': !day.is_working }">{{ day.day_name }}</span>
                        </div>

                        <div class="time-inputs" v-if="day.is_working">
                            <div class="shift-block">
                                <label>Morning Shift</label>
                                <div class="time-group">
                                    <input type="time" v-model="day.morning_start_time">
                                    <span>to</span>
                                    <input type="time" v-model="day.morning_end_time">
                                </div>
                            </div>
                            <div class="shift-block">
                                <label>Evening Shift</label>
                                <div class="time-group">
                                    <input type="time" v-model="day.evening_start_time">
                                    <span>to</span>
                                    <input type="time" v-model="day.evening_end_time">
                                </div>
                            </div>
                        </div>
                        <div v-else class="off-badge">Day Off</div>
                        
                    </div>

                    <div class="form-actions">
                        <button type="submit" class="btn-save" :disabled="isSavingSchedule">
                            {{ isSavingSchedule ? 'Saving...' : 'Save Weekly Schedule' }}
                        </button>
                        <span v-if="scheduleMessage" :class="['message', scheduleMessage.includes('success') ? 'success' : 'error']">
                            {{ scheduleMessage }}
                        </span>
                    </div>
                </form>
            </div>

        </div>
    </div>
</template>

<style scoped>
.dashboard-container { max-width: 1000px; margin: 2rem auto; padding: 1rem; font-family: Arial, sans-serif; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
.info-card { background: #e8f4f8; padding: 1.5rem; border-radius: 8px; border-left: 5px solid #3498db; margin-bottom: 2rem; }
.info-card h3 { margin-top: 0; color: #2980b9; }

/* Tabs */
.tabs { display: flex; gap: 10px; margin-bottom: 1rem; border-bottom: 2px solid #eee; }
.tabs button { padding: 10px 20px; border: none; background: none; font-size: 1rem; font-weight: bold; color: #7f8c8d; cursor: pointer; border-bottom: 3px solid transparent; transition: 0.2s; }
.tabs button:hover { color: #3498db; }
.tabs button.active { color: #3498db; border-bottom-color: #3498db; }
.tab-content { background: white; padding: 2rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }

/* Schedule Builder Styles */
.schedule-header { margin-bottom: 2rem; }
.subtitle { color: #7f8c8d; font-size: 0.9rem; margin-top: 0.2rem; }
.day-row { display: flex; align-items: center; padding: 1.5rem 0; border-bottom: 1px solid #eee; gap: 2rem; }
.day-toggle { width: 150px; display: flex; align-items: center; gap: 10px; }
.day-name { font-weight: bold; font-size: 1.1rem; color: #2c3e50; }
.text-disabled { color: #bdc3c7; text-decoration: line-through; }
.off-badge { background: #f1f2f6; color: #a4b0be; padding: 0.5rem 1rem; border-radius: 20px; font-weight: bold; font-size: 0.9rem; margin-left: auto;}

.time-inputs { display: flex; gap: 2rem; flex: 1; flex-wrap: wrap; }
.shift-block { display: flex; flex-direction: column; gap: 0.5rem; }
.shift-block label { font-size: 0.85rem; color: #7f8c8d; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
.time-group { display: flex; align-items: center; gap: 10px; }
input[type="time"] { padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; font-family: inherit; }

/* Toggle Switch CSS */
.switch { position: relative; display: inline-block; width: 44px; height: 24px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; }
.slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 4px; bottom: 4px; background-color: white; transition: .4s; }
input:checked + .slider { background-color: #2ecc71; }
input:checked + .slider:before { transform: translateX(20px); }
.slider.round { border-radius: 34px; }
.slider.round:before { border-radius: 50%; }

/* Buttons & Tables */
.btn-save { background-color: #2ecc71; color: white; padding: 0.75rem 2rem; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 2rem; font-size: 1rem;}
.btn-save:hover { background-color: #27ae60; }
.btn-primary { background-color: #3498db; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; }
.logout-btn { background-color: #e74c3c; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; }
.message { margin-left: 1rem; font-weight: bold; }
.success { color: #2ecc71; }
.error { color: #e74c3c; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 1rem; border-bottom: 1px solid #eee; text-align: left;}
</style>