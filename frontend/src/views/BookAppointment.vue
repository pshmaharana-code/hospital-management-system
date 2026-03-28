<script setup>
import { ref, onMounted, computed} from 'vue'
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

// ------WIZARD STATE------
// This tracks which step of booking step we are on (1, 2 or 3)
const currentStep = ref(1)

const allDoctors = ref([])
const departments = ref([])
const availableSlots = ref([])
const availableDates = ref([])

// ------USER SELECTION-----
const selectedDepartment = ref('')
const selectedDoctor = ref(null)
const selectedDate = ref(null)
const selectedSlot = ref(null)

const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// --- STEP 1 & 2: FETCH DOCTORS & EXTRACT DEPARTMENTS ---
const fetchDoctorsAndDepartments = async () => {
    try{
        const response = await axios.get('http://127.0.0.1:5000/api/doctors')
        allDoctors.value = response.data

        // Extract unique department name from the doctors list
        const rawDepartments = allDoctors.value.map(doc => doc.department)
        departments.value = [...new Set(rawDepartments)]
    } catch (error) {
        console.error("Failed to load data:", error)
        errorMessage.value = "Could not load hospital departments."
    }
}

// User click a department (Move to step 2)
const chooseDepartment = (dept) => {
    selectedDepartment.value = dept
    currentStep.value = 2
}

// Computed property to only show doctors in the chosen department
const filteredDoctors = computed(() => {
    return allDoctors.value.filter(doc => doc.department === selectedDepartment.value)
})

// User clicks a doctor (Move to step 3)
const chooseDoctor = (doc) => {
    selectedDoctor.value = doc
    generateCalender()
    currentStep.value = 3
}

// -----Step 3 generate 30-Day Calender-----
const generateCalender = () => {
    const dates = []
    const today = new Date()

    for (let i = 0; i < 30; i++) {
        const nextDay = new Date(today)
        nextDay.setDate(today.getDate() + i)

        // Force exact local YYYY-MM-DD (No UTC shifting!)
        const year = nextDay.getFullYear()
        const month = String(nextDay.getMonth() + 1).padStart(2, '0')
        const day = String(nextDay.getDate()).padStart(2, '0')
        const dateString = `${year}-${month}-${day}`

        const displayString = nextDay.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })

        dates.push({date: dateString, display: displayString})
    }
    availableDates.value = dates
}


// User clicks a date (Moves to Step 4)
const chooseDate = async (dateObj) => {
    selectedDate.value = dateObj
    isLoading.value = true
    errorMessage.value = ''
    availableSlots.value = []
    
    try {
        const response = await axios.get(`http://127.0.0.1:5000/api/patient/doctor/${selectedDoctor.value.id}/slots?date=${dateObj.date}`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        availableSlots.value = response.data
        currentStep.value = 4
    } catch (error) {
        console.error("Failed to fetch slots:", error)
        errorMessage.value = "Could not load availability for this date."
    } finally {
        isLoading.value = false
    }
}

// User clicks a time slot (Moves to Step 5)
const chooseSlot = (time) => {
    selectedSlot.value = time
    currentStep.value = 5
}

// --- STEP 5: CONFIRM AND BOOK ---
const confirmBooking = async () => {
    isLoading.value = true
    errorMessage.value = ''
    
    const payload = {
        doctor_id: selectedDoctor.value.id,
        date: selectedDate.value.date,
        time: selectedSlot.value
    }

    try {
        await axios.post('http://127.0.0.1:5000/api/patient/appointment', payload, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        successMessage.value = "Appointment Successfully Booked!"
        setTimeout(() => {
            router.push('/patient-dashboard')
        }, 3000)
    } catch (error) {
        console.error("Booking failed:", error)
        errorMessage.value = "Failed to book appointment. The slot might have just been taken."
    } finally {
        isLoading.value = false
    }
}

const goBack = () => {
    if (currentStep.value > 1) {
        currentStep.value--
        errorMessage.value = ''
    } else {
        router.push('/patient-dashboard')
    }
}

onMounted(() => {
    fetchDoctorsAndDepartments()
})
</script>

<template>
    <div class="booking-container">
        
        <div class="header">
            <h2>Book an Appointment</h2>
            <button @click="goBack" class="btn-back">&larr; Back</button>
        </div>

        <div class="progress-bar">
            <div :class="['step', { active: currentStep >= 1 }]">1. Dept</div>
            <div :class="['step', { active: currentStep >= 2 }]">2. Doctor</div>
            <div :class="['step', { active: currentStep >= 3 }]">3. Date</div>
            <div :class="['step', { active: currentStep >= 4 }]">4. Time</div>
            <div :class="['step', { active: currentStep >= 5 }]">5. Confirm</div>
        </div>

        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
        <div v-if="successMessage" class="success-message">
            <h3>🎉 {{ successMessage }}</h3>
            <p>Redirecting you to your dashboard...</p>
        </div>

        <div v-if="currentStep === 1 && !successMessage" class="step-content">
            <h3>Choose a Department</h3>
            <div class="grid-container">
                <div v-for="dept in departments" :key="dept" class="card dept-card" @click="chooseDepartment(dept)">
                    <h4>{{ dept }}</h4>
                    <button class="btn-select">View Doctors</button>
                </div>
            </div>
            <p v-if="departments.length === 0">No departments currently available.</p>
        </div>

        <div v-if="currentStep === 2 && !successMessage" class="step-content">
            <h3>Doctors in {{ selectedDepartment }}</h3>
            <div class="grid-container">
                <div v-for="doc in filteredDoctors" :key="doc.id" class="card doc-card" @click="chooseDoctor(doc)">
                    <h4>{{ doc.name }}</h4>
                    <p class="experience">{{ doc.experience ? doc.experience + ' years exp.' : 'Specialist' }}</p>
                    <button class="btn-select">Select</button>
                </div>
            </div>
        </div>

        <div v-if="currentStep === 3 && !successMessage" class="step-content">
            <h3>Select a Date for {{ selectedDoctor.name }}</h3>
            <div class="calendar-grid">
                <div v-for="date in availableDates" :key="date.date" 
                     class="card date-card" 
                     @click="chooseDate(date)">
                    {{ date.display }}
                </div>
            </div>
        </div>

        <div v-if="currentStep === 4 && !successMessage" class="step-content">
            <h3>Available Slots on {{ selectedDate.display }}</h3>
            <div v-if="isLoading" class="loading">Searching master schedule...</div>
            
            <div v-else-if="availableSlots.length > 0" class="slot-grid">
                <div v-for="time in availableSlots" :key="time" 
                     class="card slot-card" 
                     @click="chooseSlot(time)">
                    {{ time }}
                </div>
            </div>
            
            <div v-else class="empty-state">
                <p>No available slots on this date. The doctor may be off or fully booked.</p>
            </div>
        </div>

        <div v-if="currentStep === 5 && !successMessage" class="step-content confirmation">
            <h3>Confirm Your Appointment</h3>
            <div class="summary-box">
                <p><strong>Department:</strong> {{ selectedDepartment }}</p>
                <p><strong>Doctor:</strong> {{ selectedDoctor.name }}</p>
                <p><strong>Date:</strong> {{ selectedDate.display }}</p>
                <p><strong>Time:</strong> {{ selectedSlot }}</p>
            </div>
            <button @click="confirmBooking" class="btn-primary" :disabled="isLoading">
                {{ isLoading ? 'Booking...' : 'Confirm & Book Appointment' }}
            </button>
        </div>

    </div>
</template>

<style scoped>
/* Keeping the exact same elegant styling from before, just slightly optimized for the 5th step */
.booking-container { max-width: 900px; margin: 2rem auto; padding: 2rem; background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); font-family: Arial, sans-serif; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 2px solid #f1f2f6; padding-bottom: 1rem; }
.header h2 { margin: 0; color: #2c3e50; }
.btn-back { background: none; border: none; color: #7f8c8d; cursor: pointer; font-size: 1rem; font-weight: bold; }
.btn-back:hover { color: #34495e; }

/* Progress Bar */
.progress-bar { display: flex; justify-content: space-between; gap: 5px; margin-bottom: 3rem; background: #f1f2f6; border-radius: 30px; padding: 0.5rem; overflow-x: auto;}
.step { flex: 1; text-align: center; padding: 0.5rem; border-radius: 20px; color: #a4b0be; font-weight: bold; font-size: 0.85rem; transition: 0.3s; white-space: nowrap; }
.step.active { background: #3498db; color: white; }

/* Grids & Cards */
.step-content h3 { color: #2c3e50; margin-bottom: 1.5rem; text-align: center; }
.grid-container, .calendar-grid, .slot-grid { display: grid; gap: 1rem; }
.grid-container { grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }
.calendar-grid { grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
.slot-grid { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); }

.card { padding: 1.5rem; border: 2px solid #f1f2f6; border-radius: 8px; text-align: center; cursor: pointer; transition: 0.2s; background: white; }
.card:hover { border-color: #3498db; transform: translateY(-3px); box-shadow: 0 4px 10px rgba(52, 152, 219, 0.15); }

.doc-card h4, .dept-card h4 { margin: 0 0 0.5rem 0; color: #2c3e50; }
.experience { color: #7f8c8d; font-size: 0.9rem; margin-bottom: 1rem; }
.btn-select { background: #f1f2f6; border: none; padding: 0.5rem 1rem; border-radius: 4px; font-weight: bold; color: #34495e; cursor: pointer; width: 100%; transition: 0.2s; }
.card:hover .btn-select { background: #3498db; color: white; }

.date-card, .slot-card { font-weight: bold; color: #2c3e50; padding: 1rem; }
.date-card:hover, .slot-card:hover { background: #3498db; color: white; }

/* Confirmation */
.summary-box { background: #f8f9fa; border: 1px solid #e9ecef; border-left: 5px solid #2ecc71; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; font-size: 1.1rem; }
.summary-box p { margin: 0.5rem 0; }
.btn-primary { background: #2ecc71; color: white; border: none; padding: 1rem 2rem; font-size: 1.1rem; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; transition: 0.2s; }
.btn-primary:hover:not(:disabled) { background: #27ae60; }
.btn-primary:disabled { background: #95a5a6; cursor: not-allowed; }

/* Messages */
.error-message { background: #ffeaa7; color: #d63031; padding: 1rem; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 1rem; }
.success-message { text-align: center; padding: 3rem; background: #e8f8f5; color: #27ae60; border-radius: 12px; margin-top: 2rem; }
.empty-state, .loading { text-align: center; padding: 3rem; color: #7f8c8d; font-style: italic; background: #f8f9fa; border-radius: 8px; }
</style>