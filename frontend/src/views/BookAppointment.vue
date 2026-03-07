<script setup>
import { ref, onMounted} from 'vue'
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

// ------WIZARD STATE------
// This tracks which step of booking step we are on (1, 2 or 3)
const currentStep = ref(1)

// -----DATA STORAGE-------
const departments = ref([])
// We will use these later for step 2 and 3!
const selectedDepartment = ref(null)
const doctors = ref([])
const selectedDoctor = ref(null)
const availableDays = ref([])

// ----API Calls----

const fetchDepartments = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/departments', {
            headers: {Authorization: `Bearer ${authStore.token}`}
        })
        departments.value = response.data
    } catch (error) {
        console.error("Failed to fetch departments:", error)
        alert("Could not load departments")
    }
}

// When a user clicks a department card, we save their choice and move to Step 2!
const selectDepartment = (dept) => {
    selectedDepartment.value = dept
    currentStep.value = 2
    fetchDoctors(dept.id)  // Grab the doctors for this specific department
}

const fetchDoctors = async (deptId) => {
    try {
        const response = await axios.get(`http://127.0.0.1:5000/api/departments/${deptId}/doctors`, {
            headers: {Authorization: `Bearer ${authStore.token}`}
        })
        doctors.value = response.data
    } catch (error) {
        console.error("Failed to fetch doctors:", error)
        alert("Could not load doctors.")
    }
}

const selectDoctor = (doc) => {
    selectedDoctor.value = doc
    currentStep.value = 3
    fetchSlots(doc.id)
}

const fetchSlots = async (docId) => {
    try {
        const response = await axios.get(`http://127.0.0.1:5000/api/doctors/${docId}/slots`, {
            headers: {Authorization: `Bearer ${authStore.token}`}
        })
        availableDays.value = response.data
    } catch (error) {
        console.error("Failed to fetch slots:", error)
        alert("Could not load time slots.")
    }
}

// This will hold our final POST request to save the appointment!
const confirmBooking = async (date,time) => {
    // ask the user if they are abolutely sure or not
    if (!confirm(`Confirm booking with Dr. ${selectedDoctor.value.name} on ${date} at ${time}?`)) {
    return; // If they click cancel, stop here.
  }
  try {
    // 2. Send the data to our new Flask route
    await axios.post('http://127.0.0.1:5000/api/patient/appointment/book', {
        doctor_id: selectedDoctor.value.id,
        date: date,
        time: time
    }, {
        headers: {Authorization: `Bearer ${authStore.token}`}
    });
    // 3. Success! Alert them and teleport back to the Dashboard
    alert("Appointment booked successfully")
    router.push('/patient-dashboard')
  } catch (error) {
    console.error("Booking failed:", error);
    alert("Failed to book the appointment. Someone else might have just grabbed that slot!");
  }
}


onMounted(() => {
    fetchDepartments()
})
</script>

<template>
    <div class="booking-container">
        <h2>Book an Appointment</h2>

        <div class="progress-bar">
            <span :class="{ active: currentStep >= 1}">1. Department</span> &rarr;
            <span :class="{ active: currentStep >= 2}">2. Doctor</span> &rarr;
            <span :class="{ active: currentStep >= 3}">3. Time</span>
        </div>

        <div v-if="currentStep === 1" class="wizard-step">
            <h3>Select Department</h3>

            <div class="grid-container">
                <div
                    v-for="dept  in departments"
                    :key="dept.id"
                    class="card"
                    @click="selectDepartment(dept)"
                >
                    <h4>{{ dept.name }}</h4>
                    <p v-if="dept.description">{{ dept.description }}</p>
                </div>
            </div>
        </div>

        <div v-if="currentStep === 2" class="wizard-step">
            <h3>Select a Doctor ({{ selectedDepartment?.name }})</h3>
            
            <button @click="currentStep = 1" class="back-btn">&larr;Back to Departments</button>

            <div v-if="doctors.length === 0" class="empty-state" style="margin-top: 1rem;">
                <p>There are currently no active doctors available in this department.</p>
            </div>

            <div v-else class="grid-container">
                <div
                    v-for="doc in doctors"
                    :key="doc.id"
                    class="card"
                    @click="selectDoctor(doc)"
                >
                    <h4>Dr. {{ doc.name }}</h4>
                    <p>{{ doc.qualification }}</p>
                    <p v-if="doc.experience">Experience: {{ doc.experience }}</p>
                </div>
            </div>
        </div>

        <div v-if="currentStep === 3" class="wizard-step">
            <h3>Select a time for Dr. {{ selectedDoctor?.name }}</h3>
            <button @click="currentStep = 2" class="back-btn">&larr; Back to Doctors</button>

            <div class="calander-container">
                <div v-for="day in availableDays" :key="day.date" class="day-column">
                    <h4 class="day-name">{{ day.day_name }}</h4>
                    <p class="day-date">{{ day.display_date }}</p>

                    <div v-if="availableDays.length === 0" class="no-slot">
                        No slots available
                    </div>

                    <div v-else class="slot-list">
                        <button
                            v-for="slot in day.slots"
                            :key="slot.time"
                            :class="['slot-btn', slot.status === 'Booked' ? 'booked' : 'available']"
                            :disabled="slot.status === 'Booked'"
                            @click="confirmBooking(day.date, slot.time)"
                        >
                            {{ slot.time }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>


<style scoped>
.booking-container { max-width: 800px; margin: 2rem auto; padding: 1rem; }
.progress-bar { display: flex; justify-content: space-between; margin-bottom: 2rem; color: #888; font-weight: bold; }
.progress-bar .active { color: #2c3e50; border-bottom: 2px solid #3498db; }
.wizard-step { background: #f9f9f9; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem; }

/* The clickable cards */
.card {
  background: white; border: 1px solid #ddd; padding: 1.5rem;
  border-radius: 8px; cursor: pointer; transition: all 0.2s; text-align: center;
}
.card:hover { transform: translateY(-3px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-color: #3498db; }
.card h4 { margin: 0 0 0.5rem 0; color: #2c3e50; }
.card p { margin: 0; font-size: 0.9rem; color: #666; }
.back-btn { margin-top: 1rem; padding: 0.5rem 1rem; cursor: pointer; }

/* --- Calendar & Slots CSS --- */
.calendar-container { 
  display: flex; 
  gap: 1rem; 
  margin-top: 1.5rem; 
  overflow-x: auto; /* Lets the user scroll horizontally through the 7 days */
  padding-bottom: 1rem; 
}
.day-column { 
  min-width: 150px; 
  background: white; 
  padding: 1rem; 
  border-radius: 8px; 
  border: 1px solid #ddd; 
  text-align: center; 
}
.day-name { margin: 0; color: #2c3e50; font-size: 1.1rem; }
.day-date { margin: 0 0 1rem 0; font-size: 0.85rem; color: #666; }
.slots-list { display: flex; flex-direction: column; gap: 0.5rem; }

/* The Slot Buttons */
.slot-btn { 
  padding: 0.5rem; 
  border: none; 
  border-radius: 4px; 
  font-weight: bold; 
  cursor: pointer; 
  transition: 0.2s; 
}
.slot-btn.available { 
  background-color: #e8f8ec; 
  color: #27ae60; 
  border: 1px solid #bce8c5; 
}
.slot-btn.available:hover { 
  background-color: #27ae60; 
  color: white; 
}
.slot-btn.booked { 
  background-color: #fce4e4; 
  color: #c0392b; 
  cursor: not-allowed; 
  opacity: 0.6; 
}
.no-slots { font-size: 0.9rem; color: #999; font-style: italic; }
</style>