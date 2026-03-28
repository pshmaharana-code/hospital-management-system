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

// CONSULTATION MODAL STATE
const showConsultModal = ref(false)
const currentAppointmentId = ref(null)
const consultForm = ref({ diagnosis: '', prescription: '', notes: ''})
const isSubmitting = ref(false)

// Get today's date in local time (YYYY-MM-DD)
const getLocalToday = () => {
    const d = new Date()
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
}
const todayFormatted = ref(getLocalToday())



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

// ---LEAVE MANAGEMENT-----

const leaves = ref([])
const newLeaveDate =  ref('')
const isSubmitingLeave = ref(false)

const fetchLeaves = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/doctor/leaves', {
            headers: { Authorization: `Bearer ${authStore.token}`}
        })
        leaves.value = response.data
    } catch (error) {
        console.error("Failed to fetch leaves", error)
    }
}

const submitLeave = async () => {
    if(!newLeaveDate.value) return;
    isSubmitingLeave.value = true;

    try {
        const response = await axios.post('http://127.0.0.1:5000/api/doctor/leaves', {date: newLeaveDate.value}, {
            headers: { Authorization: `Bearer ${authStore.token}`}
        })
        newLeaveDate.value = ''
        fetchLeaves()
        alert("Time off scheduled successfully! Patients can no longer book on this date.")
    } catch (error) {
        console.error("Failed to submit leaves:", error)
        alert(error.response?.data?.msg || "Failed to schedule time off.")
    } finally {
        isSubmitingLeave.value = false;
    }
}

const handleLogout = () => {
    authStore.logout()  
    router.push('/login')   
}

// Open the Modal
const startConsultation = (appointmentId) => {
    currentAppointmentId.value = appointmentId
    consultForm.value = { diagnosis: '', prescription: '', notes: ''}
    showConsultModal.value = true
}

// Close the Modal
const closeConsultModal = () => {
    showConsultModal.value = false
    currentAppointmentId.value = null
}

// Send the data to Flask
const submitConsultation = async () => {
    isSubmitting.value = true
    try {
        await axios.post(`http://127.0.0.1:5000/api/doctor/appointment/${currentAppointmentId.value}/consult`, consultForm.value, {
            headers: {Authorization: `Bearer ${authStore.token}`}
        })
        alert("Cosultation Saved Successfully!")
        closeConsultModal()
        fetchDashboard() //referesh the queue to remove the complete patient!
    } catch(error) {
        console.error("Failed to save consultation:", error)
        alert("Failed to save consultation. Please check your connection.")
    } finally {
        isSubmitting.value = false
    }
}


const showHistoryModal = ref(false)
const patientHistoryData = ref(null)
const isHistoryLoading = ref(false)

const viewPatientHistory = async (patientId) => {
    showHistoryModal.value = true
    isHistoryLoading.value = true
    patientHistoryData.value = null

    try {
        const response = await axios.get(`http://127.0.0.1:5000/api/doctor/patient/${patientId}/history`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        patientHistoryData.value = response.data
    } catch (error) {
        console.error("Failed to fetch history:", error)
        alert("Failed to load patient history or permission denied.")
        showHistoryModal.value = false
    } finally {
        isHistoryLoading.value = false
    }
}
const closeHistoryModal = () => {
    showHistoryModal.value = false
}


onMounted(() => {
    fetchDashboard()
    fetchLeaves()
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
                <button :class="{ active: activeTab === 'leaves'}" @click="activeTab = 'leaves'">
                    Time off & Leaves
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
                                    <div class="action-buttons">
                                        <button @click="viewPatientHistory(appt.patient_id)" class="btn-secondary">History</button>
                                        
                                        <button v-if="appt.date === todayFormatted" @click="startConsultation(appt.id)" class="btn-primary">Consult</button>
                                        <button v-else class="btn-disabled" disabled>Upcoming</button>
                                    </div>
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

            <div v-if="activeTab === 'leaves'" class="tab-content">
                <div class="schedule-header">
                    <h3>Manage Time off</h3>
                    <p class="subtitle">Select dates you will be unavailable. The booking engine will automatically block these days.</p>
                </div>
                <div class="Leave-management-container">
                    <!-- Form to add leave -->
                    <form @submit.prevent="submitLeave" class="leave-form">
                        <div class="form-group">
                            <label>Select date for Time off</label>
                            <div class="Leave-input-group">
                                <input type="date" v-model="newLeaveDate" :min="todayFormatted" required>
                                <button type="submit" class="btn-primary" :disabled="isSubmitingLeave">
                                    {{ isSubmitingLeave ? 'Booking Date...' : 'Block Date' }}
                                </button>
                            </div>
                        </div>
                    </form>

                    <!-- List of upcoming leaves -->
                     <div class="upcoming-leaves">
                        <h4>Your Scheduled Time Off</h4>
                        <ul v-if="leaves.length > 0" class="leave-list">
                            <li v-for="leave in leaves" :key="leave.id" class="leave-item">
                                📅 {{ leave.date }}
                                <span class="status-badge completed">Blocked</span>
                            </li>
                        </ul>
                        <div v-else class="empty-state">
                            <p>You have no upcoming time off scheduled.</p>
                        </div>
                     </div>
                </div>
            </div>

            <div v-if="showConsultModal" class="modal-overlay">
                <div class="modal-content">
                    <h3>Patient Consultation</h3>
                    <form @submit.prevent="submitConsultation">

                        <div class="form-group">
                            <label>Diagnosis *</label>
                            <input type="text" v-model="consultForm.diagnosis" required placeholder="e.g., Viral Fever">
                        </div>
                        <div class="form-group">
                            <label>Prescription *</label>
                            <textarea v-model="consultForm.prescription" required placeholder="e.g., Paracetamol 500mg, 1x a day" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label>Additional Notes</label>
                            <textarea v-model="consultForm.notes" required placeholder="e.g., Drink plenty of fluids and rest." rows="2"></textarea>
                        </div>
                        <div class="modal-action">
                            <button type="button" @click="closeConsultModal" class="btn-cancel">Cancel</button>
                            <button type="submit" class="btn-primary" :disabled="isSubmitting">
                                {{ isSubmitting ? 'Saving...' : 'Complete Consultaiton' }}  
                            </button>
                        </div> 

                    </form>
                </div>
            </div>
        </div>
        <!-- Patient History Modal -->
         <div v-if="showHistoryModal" class="modal-overlay">
            <div class="modal-content history-modal">
                <div class="modal-header">
                    <h3>Patient Medical Records</h3>
                    <button @click="closeHistoryModal" class="close-btn">&times;</button>
                </div>

                <div v-if="isHistoryLoading" class="loading-state">Fetching records...</div>

                <div v-else-if="patientHistoryData">
                    <div class="patient-profile-bar">
                        <p><strong>Name:</strong> {{ patientHistoryData.patient_name }}</p>
                        <p><strong>Age:</strong> {{ patientHistoryData.patient_age }}</p>
                        <p><strong>Blood:</strong> {{ patientHistoryData.patient_blood_group || 'N/A' }}</p>
                    </div>

                    <div v-if="patientHistoryData.history.length > 0" class="history-list">
                        <div v-for="(record, index) in patientHistoryData.history" :key="index" class="history-card">
                            <div class="record-header">
                                <span class="record-date">{{ record.date }}</span>
                                <span class="record-doc">Treated by: {{ record.consulting_doctor }}</span>
                            </div>
                            <p><strong>Diagnosis:</strong> {{ record.diagnosis }}</p>
                            <p><strong>Prescription:</strong> {{ record.prescription }}</p>
                            <p v-if="record.notes"><strong>Notes:</strong> {{ record.notes }}</p>                           
                        </div>
                    </div>
                    <div v-else class="empty-state">
                        <p>No past medical history found for this patient.</p>
                    </div>
                </div>
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
.btn-disabled { background-color: #bdc3c7; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: not-allowed; }

/* Modal CSS */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background: white; padding: 2.5rem; border-radius: 12px; width: 90%; max-width: 500px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
.modal-content h3 { margin-top: 0; color: #2c3e50; border-bottom: 2px solid #f1f2f6; padding-bottom: 1rem; margin-bottom: 1.5rem; }
.form-group { margin-bottom: 1.5rem; display: flex; flex-direction: column; gap: 0.5rem; }
.form-group label { font-weight: bold; color: #34495e; font-size: 0.9rem; }
.form-group input, .form-group textarea { padding: 0.75rem; border: 1px solid #ddd; border-radius: 6px; font-family: inherit; font-size: 1rem; }
.form-group input:focus, .form-group textarea:focus { outline: none; border-color: #3498db; box-shadow: 0 0 0 2px rgba(52,152,219,0.2); }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 2rem; }
.btn-cancel { background: #f1f2f6; color: #7f8c8d; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; font-weight: bold; transition: 0.2s; }
.btn-cancel:hover { background: #e2e6ea; color: #2c3e50; }

/* History Modal CSS */
.action-buttons { display: flex; gap: 10px; }
.btn-secondary { background: #95a5a6; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; }
.btn-secondary:hover { background: #7f8c8d; }
.history-modal { max-width: 700px; width: 95%; max-height: 80vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f1f2f6; padding-bottom: 1rem; margin-bottom: 1.5rem; }
.modal-header h3 { margin: 0; color: #2c3e50; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #e74c3c; }
.patient-profile-bar { display: flex; gap: 2rem; background: #e8f4f8; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; color: #2980b9; }
.patient-profile-bar p { margin: 0; font-weight: bold; }
.history-list { display: flex; flex-direction: column; gap: 1rem; }
.history-card { border: 1px solid #ddd; padding: 1rem; border-radius: 8px; background: #fdfdfd; }
.record-header { display: flex; justify-content: space-between; border-bottom: 1px dashed #ccc; padding-bottom: 0.5rem; margin-bottom: 0.5rem; color: #7f8c8d; font-size: 0.9rem; }
.record-date { font-weight: bold; color: #34495e; }

/* Leave Management CSS */
.leave-management-container { display: flex; flex-direction: column; gap: 2rem; }
.leave-form { background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border: 1px solid #eee; }
.leave-input-group { display: flex; gap: 1rem; align-items: center; margin-top: 0.5rem; }
.upcoming-leaves h4 { color: #2c3e50; border-bottom: 2px solid #f1f2f6; padding-bottom: 0.5rem; }
.leave-list { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
.leave-item { background: white; border: 1px solid #ddd; padding: 1rem; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; font-weight: bold; color: #34495e; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
</style>