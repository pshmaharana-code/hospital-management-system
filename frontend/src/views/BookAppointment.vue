<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

// --- WIZARD STATE ---
const currentStep = ref(1)
const allDoctors = ref([])
const departments = ref([])
const availableSlots = ref([])
const availableDates = ref([])

// --- PATIENT SELECTION DATA ---
const mainPatientName = ref('')
const familyMembers = ref([])

// --- USER SELECTIONS ---
const selectedFamilyMemberId = ref(null)
const selectedPatientName = ref('')
const selectedDepartment = ref('')
const selectedDoctor = ref(null)
const selectedDate = ref(null)
const selectedSlot = ref(null)

const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// STEP 1: FETCH PATIENT & FAMILY PROFILES
const fetchPatientData = async () => {
    try {
        const profileRes = await axios.get('http://127.0.0.1:5000/api/patient/profile', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        mainPatientName.value = profileRes.data.name

        const familyRes = await axios.get('http://127.0.0.1:5000/api/patient/family', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        familyMembers.value = familyRes.data
    } catch (error) {
        console.error("Failed to load patient profiles:", error)
    }
}

const choosePatient = (isSelf, member = null) => {
    if (isSelf) {
        selectedFamilyMemberId.value = null
        selectedPatientName.value = mainPatientName.value || 'Myself'
    } else {
        selectedFamilyMemberId.value = member.id
        selectedPatientName.value = member.name
    }
    currentStep.value = 2
}

// STEP 2: FETCH DOCTORS & EXTRACT DEPARTMENTS
const fetchDoctorsAndDepartments = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/doctors')
        allDoctors.value = response.data
        const rawDepartments = allDoctors.value.map(doc => doc.department)
        departments.value = [...new Set(rawDepartments)]
    } catch (error) {
        errorMessage.value = "Could not load hospital departments."
    }
}

const chooseDepartment = (dept) => {
    selectedDepartment.value = dept
    currentStep.value = 3
}

// STEP 3: FILTER & CHOOSE DOCTOR
const filteredDoctors = computed(() => {
    return allDoctors.value.filter(doc => doc.department === selectedDepartment.value)
})

const chooseDoctor = (doc) => {
    selectedDoctor.value = doc
    generateCalendar()
    currentStep.value = 4
}

// STEP 4: GENERATE 30-DAY CALENDAR
const generateCalendar = () => {
    const dates = []
    const today = new Date()
    for (let i = 0; i < 30; i++) {
        const nextDay = new Date(today)
        nextDay.setDate(today.getDate() + i)
        const year = nextDay.getFullYear()
        const month = String(nextDay.getMonth() + 1).padStart(2, '0')
        const day = String(nextDay.getDate()).padStart(2, '0')
        const dateString = `${year}-${month}-${day}`
        const displayString = nextDay.toLocaleDateString('en-US', {
            weekday: 'short', month: 'short', day: 'numeric' 
        })
        dates.push({ date: dateString, display: displayString })
    }
    availableDates.value = dates
}

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
        currentStep.value = 5
    } catch (error) {
        errorMessage.value = "Could not load availability for this date."
    } finally {
        isLoading.value = false
    }
}

// STEP 5: CHOOSE SLOT
const chooseSlot = (time) => {
    selectedSlot.value = time
    currentStep.value = 6
}

// STEP 6: CONFIRM AND PAY (RAZORPAY INTEGRATION)
const confirmAndPay = async () => {
    isLoading.value = true
    errorMessage.value = ''
    try {
        // 1. Ask Flask for the Razorpay Order
        const orderResponse = await axios.post('http://127.0.0.1:5000/api/payments/create-order', 
            { amount: selectedDoctor.value.consultation_fee },
            { headers: { Authorization: `Bearer ${authStore.token}` } }
        )
        const { order_id, amount, key_id } = orderResponse.data

        // 2. Configure the Popup
        const options = {
            key: key_id,
            amount: amount,
            currency: "INR",
            name: "ApexMedical Center",
            description: `Consultation with Dr. ${selectedDoctor.value.name}`,
            order_id: order_id,
            handler: async function (response) {
                try {
                    const payload = {
                        doctor_id: selectedDoctor.value.id,
                        date: selectedDate.value.date,
                        time: selectedSlot.value,
                        family_member_id: selectedFamilyMemberId.value,
                        payment_id: response.razorpay_payment_id 
                    }
                    const dbResponse = await axios.post('http://127.0.0.1:5000/api/patient/appointment', payload, {
                        headers: { Authorization: `Bearer ${authStore.token}` }
                    })
                    successMessage.value = dbResponse.data.msg || "Appointment Successfully Booked!"
                    setTimeout(() => { router.push('/patient-dashboard') }, 3000)
                } catch (saveError) {
                    errorMessage.value = "Payment succeeded, but failed to save appointment. Please contact support."
                } finally {
                    isLoading.value = false
                }
            },
            prefill: { name: authStore.user?.username || "Patient" },
            theme: { color: "#0f766e" } // Updated to Apex Teal
        }

        // 3. Open the Popup
        const rzp = new window.Razorpay(options)
        rzp.on('payment.failed', function () {
            errorMessage.value = "Payment Failed or Cancelled. Appointment not booked."
            isLoading.value = false
        })
        rzp.open()
    } catch (error) {
        console.error(error)
        errorMessage.value = "Failed to connect to payment gateway."
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
    fetchPatientData()
    fetchDoctorsAndDepartments()
})
</script>

<template>
    <div class="clean-layout">
        
        <div class="dynamic-bg">
            <div class="orb orb-1"></div>
            <div class="orb orb-2"></div>
            <div class="orb orb-3"></div>
        </div>
        
        <aside class="side-nav">
            <div class="brand-header" @click="$router.push('/')">
                <div class="logo-mark">+</div>
                <span class="logo-text">ApexMedical</span>
            </div>
            <nav class="nav-links">
                <router-link to="/patient-dashboard" class="nav-btn btn-back">
                    &larr; Exit Booking
                </router-link>
            </nav>
        </aside>

        <main class="workspace">
            <header class="page-header">
                <div class="header-content">
                    <h1 class="sofi-title">Book Consultation</h1>
                    <p>Follow the steps to schedule a secure appointment.</p>
                </div>
                <button @click="goBack" class="btn-outline-back" :disabled="currentStep <= 1 || successMessage.length > 0">
                    &larr; Previous Step
                </button>
            </header>

            <div class="content-area">
                <div class="wizard-card glass-panel">
                    
                    <div class="stepper-wrapper">
                        <div v-for="stepNum in 6" :key="stepNum" class="stepper-item" :class="{ 'completed': currentStep > stepNum, 'active': currentStep === stepNum }">
                            <div class="step-counter">{{ currentStep > stepNum ? '✓' : stepNum }}</div>
                            <div class="step-name">
                                {{ ['Patient', 'Department', 'Doctor', 'Date', 'Time', 'Confirm'][stepNum - 1] }}
                            </div>
                        </div>
                    </div>

                    <div v-if="errorMessage" class="alert-msg alert-error">{{ errorMessage }}</div>
                    
                    <div v-if="successMessage" class="success-screen fade-in">
                        <div class="success-icon">🎉</div>
                        <h2>{{ successMessage }}</h2>
                        <p>Your payment was successful. Redirecting you to your dashboard...</p>
                    </div>

                    <div v-if="currentStep === 1 && !successMessage" class="step-content fade-in">
                        <h3 class="step-title">Who is this appointment for?</h3>
                        <div class="grid-container">
                            <div class="selection-card" @click="choosePatient(true)">
                                <div class="avatar-circle main-avatar">Me</div>
                                <h4>{{ mainPatientName || 'Myself' }}</h4>
                                <span class="badge badge-teal">Primary Account</span>
                            </div>
                            <div v-for="member in familyMembers" :key="member.id" class="selection-card" @click="choosePatient(false, member)">
                                <div class="avatar-circle family-avatar">{{ member.name.charAt(0).toUpperCase() }}</div>
                                <h4>{{ member.name }}</h4>
                                <span class="badge badge-indigo">{{ member.relation }}</span>
                            </div>
                        </div>
                        <p class="help-text mt-3 text-center">Need to book for someone else? <router-link to="/patient-profile">Add a Family Member</router-link></p>
                    </div>

                    <div v-if="currentStep === 2 && !successMessage" class="step-content fade-in">
                        <h3 class="step-title">Choose a Department</h3>
                        <div class="grid-container">
                            <div v-for="dept in departments" :key="dept" class="selection-card color-hover-card" @click="chooseDepartment(dept)">
                                <div class="icon-blob">
                                    <span class="icon-emoji">🏥</span>
                                </div>
                                <h4>{{ dept }}</h4>
                            </div>
                        </div>
                    </div>

                    <div v-if="currentStep === 3 && !successMessage" class="step-content fade-in">
                        <h3 class="step-title">Select a Specialist</h3>
                        <div class="grid-container">
                            <div v-for="doc in filteredDoctors" :key="doc.id" class="selection-card doc-card color-hover-card" @click="chooseDoctor(doc)">
                                <div class="doc-avatar"></div>
                                <h4>Dr. {{ doc.name }}</h4>
                                <p class="sub-text">{{ doc.experience }} Years Experience</p>
                                <div class="price-tag">₹{{ doc.consultation_fee }}</div>
                            </div>
                        </div>
                    </div>

                    <div v-if="currentStep === 4 && !successMessage" class="step-content fade-in">
                        <h3 class="step-title">Select a Date</h3>
                        <div class="calendar-grid">
                            <div v-for="date in availableDates" :key="date.date" class="selection-card date-card" @click="chooseDate(date)">
                                {{ date.display }}
                            </div>
                        </div>
                    </div>

                    <div v-if="currentStep === 5 && !successMessage" class="step-content fade-in">
                        <h3 class="step-title">Available Slots on {{ selectedDate.display }}</h3>
                        <div v-if="isLoading" class="loading-state"><div class="spinner"></div></div>
                        <div v-else-if="availableSlots.length > 0" class="slot-grid">
                            <div v-for="time in availableSlots" :key="time" class="selection-card time-card" @click="chooseSlot(time)">
                                {{ time }}
                            </div>
                        </div>
                        <div v-else class="empty-state">No available slots on this date. Doctor may be fully booked.</div>
                    </div>

                    <div v-if="currentStep === 6 && !successMessage" class="step-content fade-in">
                        <h3 class="step-title">Confirm Appointment Details</h3>
                        <div class="summary-box glass-panel-inner">
                            <div class="summary-row">
                                <span class="label">Patient:</span>
                                <span class="value">{{ selectedPatientName }}</span>
                            </div>
                            <div class="summary-row">
                                <span class="label">Specialist:</span>
                                <span class="value">Dr. {{ selectedDoctor.name }}</span>
                            </div>
                            <div class="summary-row">
                                <span class="label">Date & Time:</span>
                                <span class="value">{{ selectedDate.display }} at {{ selectedSlot }}</span>
                            </div>
                            <div class="summary-row total-row">
                                <span class="label">Consultation Fee:</span>
                                <span class="value text-gradient">₹{{ selectedDoctor.consultation_fee }}</span>
                            </div>
                        </div>
                        <div class="action-footer">
                            <button @click="confirmAndPay" class="btn-primary-large" :disabled="isLoading">
                                {{ isLoading ? 'Processing...' : `Secure Slot & Pay ₹${selectedDoctor.consultation_fee}` }}
                            </button>
                        </div>
                    </div>

                </div>
            </div>
        </main>
    </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@700;800&display=swap');

/* --- BASE & LAYOUT --- */
.clean-layout { font-family: 'Plus Jakarta Sans', sans-serif; display: flex; height: 100vh; background-color: #f8fafc; color: #1e293b; overflow: hidden; position: relative; }

/* THE MAGIC: ANIMATED GRADIENT ORBS (Now covers the whole screen) */
.dynamic-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; overflow: hidden; z-index: 0; pointer-events: none; }
.orb { position: absolute; border-radius: 50%; filter: blur(100px); opacity: 0.4; animation: float 20s infinite alternate cubic-bezier(0.4, 0, 0.2, 1); }
.orb-1 { width: 600px; height: 600px; background: #14b8a6; top: -20%; left: -10%; }
.orb-2 { width: 700px; height: 700px; background: #8b5cf6; bottom: -20%; right: -5%; animation-delay: -5s; }
.orb-3 { width: 500px; height: 500px; background: #38bdf8; top: 30%; left: 40%; animation-delay: -10s; opacity: 0.25; }

@keyframes float {
    0% { transform: translate(0, 0) scale(1); }
    100% { transform: translate(50px, 50px) scale(1.1); }
}

/* SIDEBAR - Now frosted glass! */
.side-nav { width: 250px; background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.6); display: flex; flex-direction: column; padding: 1.5rem 1.2rem; z-index: 30; box-shadow: 4px 0 24px rgba(0,0,0,0.02); position: relative; }
.brand-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 2.5rem; cursor: pointer; }
.logo-mark { background: linear-gradient(135deg, #0f766e, #14b8a6); color: white; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 8px; font-weight: 800; box-shadow: 0 4px 10px rgba(15, 118, 110, 0.2); }
.logo-text { font-family: 'Outfit', sans-serif; font-size: 1.3rem; font-weight: 800; color: #0f172a; letter-spacing: -0.5px; }
.nav-links { display: flex; flex-direction: column; gap: 0.4rem; flex: 1; }
.nav-btn { display: flex; align-items: center; gap: 0.8rem; padding: 0.8rem 1rem; border-radius: 10px; border: none; background: transparent; color: #64748b; font-weight: 600; font-size: 0.9rem; cursor: pointer; text-decoration: none; transition: all 0.2s; text-align: left; }
.btn-back { color: #0f766e; background: linear-gradient(135deg, #f0fdfa, #ccfbf1); box-shadow: 0 2px 5px rgba(15, 118, 110, 0.05); }

/* --- DYNAMIC WORKSPACE - Now transparent so background shows through --- */
.workspace { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: transparent; position: relative; z-index: 10; }

.page-header { padding: 2.5rem 3rem 1rem; display: flex; justify-content: space-between; align-items: flex-end; position: relative; z-index: 20; }
.sofi-title { font-family: 'Outfit', sans-serif; font-size: 2.2rem; font-weight: 800; color: #0f172a; margin: 0 0 0.2rem 0; letter-spacing: -1px; }
.page-header p { color: #475569; margin: 0; font-size: 1rem; font-weight: 500; }

/* Top Right Button Logic */
.btn-outline-back { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); border: 2px solid #0f766e; color: #0f766e; padding: 0.6rem 1.2rem; border-radius: 10px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 4px 15px rgba(15, 118, 110, 0.1); }
.btn-outline-back:hover:not(:disabled) { background: #0f766e; color: #ffffff; transform: translateY(-2px); box-shadow: 0 8px 20px rgba(15, 118, 110, 0.2); }
.btn-outline-back:disabled { border: 2px solid rgba(148, 163, 184, 0.3); color: #94a3b8; background: rgba(255, 255, 255, 0.5); box-shadow: none; opacity: 0.6; cursor: not-allowed; transform: none; }

.content-area { padding: 0 3rem 3rem; overflow-y: auto; flex: 1; position: relative; z-index: 20; }

/* --- TRUE GLASSMORPHIC WIZARD CARD --- */
.glass-panel {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 24px;
    padding: 3rem 4rem;
    box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.15), inset 0 1px 0 rgba(255, 255, 255, 1);
    max-width: 950px;
    margin: 0 auto;
}

.step-title { font-family: 'Outfit', sans-serif; font-size: 1.6rem; font-weight: 800; color: #0f172a; margin-bottom: 2rem; text-align: center; letter-spacing: -0.5px; }

/* --- STEPPER --- */
.stepper-wrapper { display: flex; justify-content: space-between; margin-bottom: 3.5rem; position: relative; }
.stepper-wrapper::before { content: ''; position: absolute; top: 18px; left: 0; right: 0; height: 3px; background: rgba(0,0,0,0.05); z-index: 1; border-radius: 3px; }
.stepper-item { display: flex; flex-direction: column; align-items: center; z-index: 2; position: relative; background: transparent; padding: 0 10px; width: 80px; }
.step-counter { width: 38px; height: 38px; border-radius: 50%; background: #ffffff; color: #94a3b8; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.95rem; margin-bottom: 0.8rem; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); border: 2px solid #e2e8f0; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
.step-name { font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; transition: 0.3s; }

.stepper-item.active .step-counter { background: linear-gradient(135deg, #14b8a6, #0f766e); color: #ffffff; border-color: #0f766e; box-shadow: 0 0 0 6px rgba(20, 184, 166, 0.2); transform: scale(1.1); }
.stepper-item.active .step-name { color: #0f766e; font-weight: 800; }
.stepper-item.completed .step-counter { background: #10b981; color: white; border-color: #10b981; }

/* --- GRIDS & DYNAMIC SELECTION CARDS --- */
.grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1.5rem; }
.calendar-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 1.2rem; }
.slot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 1.2rem; }

.selection-card { 
    background: rgba(255, 255, 255, 0.9); 
    border: 1px solid rgba(255, 255, 255, 1); 
    border-radius: 16px; 
    padding: 1.5rem; 
    text-align: center; 
    cursor: pointer; 
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
    display: flex; 
    flex-direction: column; 
    align-items: center; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.03); 
    position: relative;
    overflow: hidden;
}

/* The Hover Physics */
.selection-card:hover { 
    background: #ffffff; 
    border-color: #14b8a6; 
    transform: translateY(-5px) scale(1.02); 
    box-shadow: 0 20px 40px rgba(15, 118, 110, 0.12); 
}
.selection-card h4 { margin: 0 0 0.5rem 0; font-size: 1.1rem; color: #1e293b; text-transform: capitalize; font-weight: 700; z-index: 2; }

/* Color Specific Hover Effects */
.color-hover-card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(135deg, rgba(20, 184, 166, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%); opacity: 0; transition: 0.3s; z-index: 0; pointer-events: none; }
.color-hover-card:hover::before { opacity: 1; }

.date-card, .time-card { padding: 1.2rem; font-weight: 700; color: #334155; font-size: 0.95rem; }
.date-card:hover, .time-card:hover { background: linear-gradient(135deg, #0f766e, #14b8a6); color: white; border-color: #14b8a6; }

/* CARD INNER ELEMENTS */
.avatar-circle { width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.3rem; margin-bottom: 1rem; color: white; box-shadow: 0 8px 16px rgba(0,0,0,0.1); z-index: 2; }
.main-avatar { background: linear-gradient(135deg, #0f766e, #14b8a6); }
.family-avatar { background: linear-gradient(135deg, #8b5cf6, #a78bfa); }
.doc-avatar { width: 72px; height: 72px; border-radius: 50%; background: linear-gradient(135deg, #e2e8f0, #cbd5e1); margin-bottom: 1.2rem; z-index: 2; border: 3px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }

.icon-blob { width: 60px; height: 60px; background: linear-gradient(135deg, #e0e7ff, #ede9fe); border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; transition: 0.4s; z-index: 2; }
.icon-emoji { font-size: 1.8rem; }
.selection-card:hover .icon-blob { border-radius: 50%; transform: scale(1.1) rotate(10deg); background: linear-gradient(135deg, #ccfbf1, #dbeafe); }

.badge { padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.75rem; font-weight: 800; margin-top: 0.5rem; z-index: 2; }
.badge-teal { background: #ccfbf1; color: #0f766e; }
.badge-indigo { background: #e0e7ff; color: #4338ca; }
.price-tag { background: #ffffff; color: #059669; padding: 0.4rem 1.2rem; border-radius: 8px; font-weight: 800; font-size: 0.95rem; margin-top: 1.2rem; border: 1px solid #a7f3d0; z-index: 2; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15); }

/* --- SUMMARY BOX (Inner Glass) --- */
.glass-panel-inner { background: rgba(255, 255, 255, 0.5); border: 1px solid rgba(255, 255, 255, 0.6); border-radius: 16px; padding: 2.5rem; margin-bottom: 2.5rem; max-width: 600px; margin-left: auto; margin-right: auto; box-shadow: inset 0 2px 20px rgba(255,255,255,0.5); }
.summary-row { display: flex; justify-content: space-between; padding: 1rem 0; border-bottom: 1px dashed #cbd5e1; }
.summary-row:last-child { border-bottom: none; }
.summary-row .label { color: #64748b; font-weight: 600; font-size: 1rem; }
.summary-row .value { color: #1e293b; font-weight: 800; font-size: 1.05rem; }
.total-row { margin-top: 1rem; padding-top: 1.5rem; border-top: 2px solid rgba(15, 118, 110, 0.2); border-bottom: none; }
.total-row .label { font-size: 1.15rem; color: #1e293b; }
.total-row .value { font-size: 1.5rem; }
.text-gradient { background: linear-gradient(135deg, #059669, #10b981); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* --- ACTIONS & UTILS --- */
.action-footer { display: flex; justify-content: center; }
.btn-primary-large { background: linear-gradient(135deg, #0f766e, #14b8a6); color: white; border: none; border-radius: 14px; font-weight: 700; font-size: 1.1rem; padding: 1.2rem 3rem; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); font-family: inherit; box-shadow: 0 10px 25px rgba(15, 118, 110, 0.3); width: 100%; max-width: 600px; position: relative; overflow: hidden; }
.btn-primary-large::after { content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.3), rgba(255,255,255,0)); transform: skewX(-20deg); transition: 0.5s; }
.btn-primary-large:hover:not(:disabled) { transform: translateY(-3px); box-shadow: 0 15px 35px rgba(15, 118, 110, 0.4); }
.btn-primary-large:hover:not(:disabled)::after { left: 150%; }
.btn-primary-large:disabled { opacity: 0.7; cursor: not-allowed; transform: none; box-shadow: none; }

.alert-error { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; padding: 1rem; border-radius: 12px; font-weight: 600; text-align: center; margin-bottom: 2rem; }

.success-screen { text-align: center; padding: 4rem 0; }
.success-icon { font-size: 5rem; margin-bottom: 1.5rem; animation: bounce 2s infinite; }
@keyframes bounce { 0%, 20%, 50%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-20px); } 60% { transform: translateY(-10px); } }
.success-screen h2 { color: #10b981; font-size: 2.2rem; font-weight: 800; margin-bottom: 0.8rem; letter-spacing: -0.5px; }

.loading-state, .empty-state { text-align: center; padding: 5rem; color: #64748b; }
.spinner { width: 40px; height: 40px; border: 4px solid #e2e8f0; border-top-color: #0f766e; border-radius: 50%; animation: spin 1s cubic-bezier(0.4, 0, 0.2, 1) infinite; margin: 0 auto 1.5rem; }
@keyframes spin { to { transform: rotate(360deg); } }
.fade-in { animation: fadeIn 0.5s cubic-bezier(0.4, 0, 0.2, 1); }
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px) scale(0.98); filter: blur(4px); } to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); } }
</style>