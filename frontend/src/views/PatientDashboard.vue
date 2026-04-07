<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { jsPDF } from 'jspdf';

const authStore = useAuthStore()
const router = useRouter()

const activeTab = ref('upcoming') // 'upcoming' or 'history'
const patientData = ref(null)
const historyData = ref([])
const isLoading = ref(true)
const errorMessage = ref('')

const fetchDashboard = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/patient/dashboard', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        patientData.value = response.data
    } catch (error) {
        console.error("Failed to load dashboard:", error)
        errorMessage.value = "Could not load dashboard data."
    } finally {
        isLoading.value = false
    }
}

const fetchHistory = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/patient/history', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        historyData.value = response.data
    } catch (error) {
        console.error("Failed to load history:", error)
    }
}

// Switch tabs and load data if needed
const switchTab = (tab) => {
    activeTab.value = tab
    if (tab === 'history' && historyData.value.length === 0) {
        fetchHistory()
    }
}

const goToBooking = () => {
    router.push('/book-appointment')
}

// Cancel an appointment
const cancelAppointment = async (appointmentId) => {
    if (!confirm("Are you sure you want to cancel this appointment?")) return;
    
    try {
        // NOTE: Verify this URL matches your existing Flask backend route for cancelling!
        await axios.post(`http://127.0.0.1:5000/api/patient/appointment/${appointmentId}/cancel`, {}, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        
        // Refresh the dashboard to remove it from the list
        fetchDashboard()
        
        // If they have the history tab open, refresh that too so it shows as "Cancelled"
        if (activeTab.value === 'history') {
            fetchHistory()
        }
    } catch (error) {
        console.error("Failed to cancel appointment:", error)
        alert("Failed to cancel appointment. Please try again.")
    }
}

const handleLogout = () => {
    authStore.logout()
    router.push('/login')
}

// We will build the actual PDF generation logic next!
// The Frontend PDF Generator
const downloadPrescription = (record) => {
    // 1. Initialize a new blank PDF document
    const doc = new jsPDF();

    // 2. Hospital Letterhead (Centered)
    doc.setFontSize(22);
    doc.setTextColor(41, 128, 185); // Professional Blue
    doc.text("HMS GENERAL HOSPITAL", 105, 20, null, null, "center");

    doc.setFontSize(12);
    doc.setTextColor(127, 140, 141); // Grey
    doc.text("Official Medical Prescription", 105, 28, null, null, "center");

    // Divider Line
    doc.setLineWidth(0.5);
    doc.setDrawColor(236, 240, 241);
    doc.line(20, 35, 190, 35);

    // 3. Patient & Date Info
    doc.setFontSize(11);
    doc.setTextColor(44, 62, 80); // Dark Blue/Grey
    doc.text(`Date: ${record.date} at ${record.time}`, 20, 45);
    doc.text(`Patient Name: ${patientData.value.patient_name}`, 20, 52);

    // 4. Doctor Info
    doc.text(`Consulting Doctor: Dr. ${record.doctor_name}`, 20, 65);
    doc.text(`Department: ${record.department}`, 20, 72);

    // Divider Line
    doc.line(20, 80, 190, 80);

    // 5. Medical Details
    doc.setFontSize(14);
    doc.setTextColor(41, 128, 185);
    doc.text("Diagnosis & Treatment", 20, 95);

    doc.setFontSize(12);
    doc.setTextColor(0, 0, 0); // Black for readable text
    
    // Diagnosis
    doc.setFont("helvetica", "bold");
    doc.text("Diagnosis:", 20, 105);
    doc.setFont("helvetica", "normal");
    doc.text(record.diagnosis, 45, 105);

    // Prescription (Wrapped nicely in case it's a long paragraph)
    doc.setFont("helvetica", "bold");
    doc.text("Prescription:", 20, 115);
    doc.setFont("helvetica", "normal");
    const splitPrescription = doc.splitTextToSize(record.prescription, 140);
    doc.text(splitPrescription, 50, 115);

    // Calculate where to put Notes based on how long the prescription was
    let nextY = 115 + (splitPrescription.length * 7);

    // Notes
    if (record.notes) {
        doc.setFont("helvetica", "bold");
        doc.text("Notes:", 20, nextY);
        doc.setFont("helvetica", "normal");
        const splitNotes = doc.splitTextToSize(record.notes, 150);
        doc.text(splitNotes, 36, nextY);
    }

    // 6. Footer
    doc.setFontSize(9);
    doc.setTextColor(149, 165, 166);
    doc.text("This is a digitally generated document. No physical signature is required.", 105, 280, null, null, "center");

    // 7. Trigger the Download!
    // Clean up the date string to make a safe filename
    const safeDate = record.date.replace(/, /g, '_').replace(/ /g, '_');
    doc.save(`Prescription_${safeDate}.pdf`);
}

onMounted(() => {
    fetchDashboard()
})
</script>

<template>
    <div class="dashboard-container">
        
        <div class="dashboard-header">
            <h2>Patient Portal</h2>

            <div class="header-actions">
                <router-link to="/patient-profile" class="btn-profile">
                    Manage Profile
                </router-link>
                <button @click="handleLogout" class="logout-btn">Logout</button>
            </div>

        </div>

        <div v-if="isLoading" class="loading-state">Loading your dashboard...</div>
        <div v-else-if="errorMessage" class="error-message">{{ errorMessage }}</div>

        <div v-else>
            <div class="info-card">
                <div class="card-text">
                    <h3>Welcome, {{ patientData.patient_name }}</h3>
                    <p>Manage your appointments and medical history from your personal portal.</p>
                </div>
                <button @click="goToBooking" class="btn-primary pulse-btn">+ Book New Appointment</button>
            </div>

            <!-- Tabs Navigation -->
            <div class="tabs">
                <button :class="{ active: activeTab === 'upcoming' }" @click="switchTab('upcoming')">
                    Upcoming Appointments
                </button>
                <button :class="{ active: activeTab === 'history' }" @click="switchTab('history')">
                    My Medical History
                </button>
            </div>

            <!-- Tab 1: Upcoming Appointments -->
            <div v-if="activeTab === 'upcoming'" class="tab-content">
                <div v-if="patientData.upcoming_appointments.length > 0" class="table-responsive">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Time</th>
                                <th>Doctor</th>
                                <th>Department</th>
                                <th>Action</th> <!-- Added back -->
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="appt in patientData.upcoming_appointments" :key="appt.id">
                                <td><strong>{{ appt.date }}</strong></td>
                                <td>{{ appt.time }}</td>
                                <td>Dr. {{ appt.doctor_name }}</td>
                                <td>{{ appt.department }}</td>
                                <td>
                                    <!-- The missing button! -->
                                    <button @click="cancelAppointment(appt.id)" class="btn-cancel-sm">Cancel</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div v-else class="empty-state">
                    <p>You have no upcoming appointments.</p>
                    <button @click="goToBooking" class="btn-secondary">Book One Now</button>
                </div>
            </div>

            <!-- Tab 2: Medical History (The New Section!) -->
            <div v-if="activeTab === 'history'" class="tab-content">
                <div v-if="historyData.length > 0" class="history-grid">
                    <div v-for="record in historyData" :key="record.id" class="history-card">
                        
                        <div class="record-header">
                            <div>
                                <span class="record-date">{{ record.date }}</span>
                                <span class="record-time">{{ record.time }}</span>
                            </div>
                            <span :class="['status-badge', record.status.toLowerCase()]">{{ record.status }}</span>
                        </div>

                        <div class="record-body">
                            <p class="doc-name"><strong>Dr. {{ record.doctor_name }}</strong> ({{ record.department }})</p>
                            
                            <div v-if="record.status === 'Completed'" class="medical-details">
                                <p><strong>Diagnosis:</strong> {{ record.diagnosis }}</p>
                                <p><strong>Prescription:</strong> {{ record.prescription }}</p>
                                <p v-if="record.notes"><strong>Notes:</strong> {{ record.notes }}</p>
                            </div>
                            <div v-else class="cancelled-text">
                                <p>This appointment was cancelled.</p>
                            </div>
                        </div>

                        <!-- The Brilliant Download Button! -->
                        <div class="record-footer" v-if="record.status === 'Completed'">
                            <button @click="downloadPrescription(record)" class="btn-download">
                                📄 Download Prescription
                            </button>
                        </div>

                    </div>
                </div>
                <div v-else class="empty-state">
                    <p>No past medical history found.</p>
                </div>
            </div>

        </div>
    </div>
</template>

<style scoped>
/* Keeping your existing styles and adding a few for the new History Cards! */
.dashboard-container { max-width: 1000px; margin: 2rem auto; padding: 1rem; font-family: Arial, sans-serif; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
.info-card { display: flex; justify-content: space-between; align-items: center; background: #e8f4f8; padding: 2rem; border-radius: 8px; border-left: 5px solid #3498db; margin-bottom: 2rem; }
.info-card h3 { margin-top: 0; color: #2980b9; }

.tabs { display: flex; gap: 10px; margin-bottom: 1rem; border-bottom: 2px solid #eee; }
.tabs button { padding: 10px 20px; border: none; background: none; font-size: 1rem; font-weight: bold; color: #7f8c8d; cursor: pointer; border-bottom: 3px solid transparent; transition: 0.2s; }
.tabs button:hover { color: #3498db; }
.tabs button.active { color: #3498db; border-bottom-color: #3498db; }
.tab-content { background: white; padding: 2rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }

/* History Cards */
.history-grid { display: grid; gap: 1.5rem; }
.history-card { border: 1px solid #e0e6ed; border-radius: 8px; overflow: hidden; background: #fff; transition: box-shadow 0.2s; }
.history-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.record-header { display: flex; justify-content: space-between; align-items: center; background: #f8f9fa; padding: 1rem 1.5rem; border-bottom: 1px solid #e0e6ed; }
.record-date { font-weight: bold; color: #2c3e50; margin-right: 1rem; }
.record-time { color: #7f8c8d; font-size: 0.9rem; }
.status-badge { padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
.status-badge.completed { background: #e8f8f5; color: #27ae60; }
.status-badge.cancelled { background: #fdedec; color: #e74c3c; }

.record-body { padding: 1.5rem; }
.doc-name { margin-top: 0; font-size: 1.1rem; color: #34495e; border-bottom: 1px dashed #eee; padding-bottom: 0.5rem; margin-bottom: 1rem; }
.medical-details p { margin: 0.5rem 0; color: #2c3e50; line-height: 1.5; }
.cancelled-text { color: #95a5a6; font-style: italic; }

.record-footer { background: #fdfdfd; padding: 1rem 1.5rem; border-top: 1px solid #eee; text-align: right; }
.btn-download { background: #fff; border: 2px solid #3498db; color: #3498db; padding: 0.5rem 1rem; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s; display: flex; align-items: center; gap: 0.5rem; margin-left: auto; }
.btn-download:hover { background: #3498db; color: white; }

.btn-cancel-sm {
    background-color: #ffeaa7; /* Soft yellow/orange warning color */
    color: #d35400;
    padding: 0.4rem 0.8rem;
    border: 1px solid #e67e22;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: bold;
    transition: 0.2s;
}
.btn-cancel-sm:hover {
    background-color: #e74c3c;
    color: white;
    border-color: #e74c3c;
}

/* General Buttons */
.btn-primary { background-color: #3498db; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
.btn-primary:hover { background-color: #2980b9; }
.btn-secondary { background-color: #95a5a6; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; }
.logout-btn { background-color: #e74c3c; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
.empty-state { text-align: center; padding: 3rem; color: #7f8c8d; font-style: italic; background: #f8f9fa; border-radius: 8px; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 1rem; border-bottom: 1px solid #eee; text-align: left; }

/* Update the header to align items correctly */
.dashboard-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 2rem; 
}

/* Group the buttons together */
.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

/* Style for the new profile button */
.btn-profile {
  background-color: #f8f9fa;
  color: #2c3e50;
  border: 1px solid #ccc;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-weight: bold;
  text-decoration: none;
  transition: 0.2s;
}

.btn-profile:hover {
  background-color: #e2e6ea;
}

/* Ensure your logout button still looks good */
.logout-btn { 
  background-color: #e74c3c; 
  color: white; 
  padding: 0.5rem 1rem; 
  border: none; 
  border-radius: 4px; 
  cursor: pointer; 
  font-weight: bold; 
}
</style>