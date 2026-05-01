<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { jsPDF } from 'jspdf';

const authStore = useAuthStore()
const router = useRouter()

const activeTab = ref('upcoming') 
const patientData = ref(null)
const historyData = ref([])
const isLoading = ref(true)
const errorMessage = ref('')

// --- API LOGIC (Preserved and Secure) ---
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

const switchTab = (tab) => {
    activeTab.value = tab
    if (tab === 'history' && historyData.value.length === 0) {
        fetchHistory()
    }
}

const goToBooking = () => { router.push('/book-appointment') }

const cancelAppointment = async (appointmentId) => {
    if (!confirm("Are you sure you want to cancel this appointment?")) return;
    try {
        await axios.post(`http://127.0.0.1:5000/api/patient/appointment/${appointmentId}/cancel`, {}, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        fetchDashboard()
        if (activeTab.value === 'history') fetchHistory()
    } catch (error) {
        console.error("Failed to cancel:", error)
        alert("Failed to cancel appointment. Please try again.")
    }
}

const handleLogout = () => {
    authStore.logout()
    router.push('/login')
}

// --- PDF GENERATOR (Updated to Clean Aesthetic) ---
const downloadPrescription = (record) => {
    const doc = new jsPDF();
    doc.setFontSize(22);
    doc.setTextColor(15, 118, 110); 
    doc.text("APEX MEDICAL CENTER", 105, 20, null, null, "center");
    doc.setFontSize(12);
    doc.setTextColor(100, 116, 139); 
    doc.text("Official Medical Prescription", 105, 28, null, null, "center");
    doc.setLineWidth(0.5);
    doc.setDrawColor(226, 232, 240);
    doc.line(20, 35, 190, 35);
    
    doc.setFontSize(11);
    doc.setTextColor(30, 41, 59); 
    doc.text(`Date: ${record.date} at ${record.time}`, 20, 45);
    doc.text(`Patient Name: ${patientData.value?.patient_name || 'Patient'}`, 20, 52);
    doc.text(`Consulting Doctor: Dr. ${record.doctor_name}`, 20, 65);
    doc.text(`Department: ${record.department}`, 20, 72);
    doc.line(20, 80, 190, 80);
    
    doc.setFontSize(14);
    doc.setTextColor(15, 118, 110);
    doc.text("Diagnosis & Treatment", 20, 95);
    doc.setFontSize(11);
    doc.setTextColor(30, 41, 59); 
    
    doc.setFont("helvetica", "bold"); doc.text("Diagnosis:", 20, 105);
    doc.setFont("helvetica", "normal"); doc.text(record.diagnosis, 45, 105);
    
    doc.setFont("helvetica", "bold"); doc.text("Prescription:", 20, 115);
    doc.setFont("helvetica", "normal");
    const splitPrescription = doc.splitTextToSize(record.prescription, 140);
    doc.text(splitPrescription, 50, 115);
    
    let nextY = 115 + (splitPrescription.length * 7);
    if (record.notes) {
        doc.setFont("helvetica", "bold"); doc.text("Notes:", 20, nextY);
        doc.setFont("helvetica", "normal");
        const splitNotes = doc.splitTextToSize(record.notes, 150);
        doc.text(splitNotes, 36, nextY);
    }
    
    doc.setFontSize(9);
    doc.setTextColor(148, 163, 184);
    doc.text("This is a digitally generated document. No signature required.", 105, 280, null, null, "center");
    
    const safeDate = record.date.replace(/, /g, '_').replace(/ /g,'_');
    doc.save(`ApexMedical_Prescription_${safeDate}.pdf`);
}

onMounted(() => { fetchDashboard() })
</script>

<template>
    <div class="clean-layout">
        
        <!-- SIDE NAVIGATION (Solid White Base) -->
        <aside class="side-nav">
            <div class="brand-header" @click="$router.push('/')">
                <div class="logo-mark">+</div>
                <span class="logo-text">ApexMedical</span>
            </div>

            <nav class="nav-links">
                <button :class="['nav-btn', { active: activeTab === 'upcoming' }]" @click="switchTab('upcoming')">
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
                    Dashboard
                </button>
                <button :class="['nav-btn', { active: activeTab === 'history' }]" @click="switchTab('history')">
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                    Medical History
                </button>
                <router-link to="/patient-profile" class="nav-btn">
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    Manage Profile
                </router-link>
            </nav>

            <div class="sidebar-bottom">
                <div class="premium-upgrade">
                    <h5>Apex Plus</h5>
                    <p>Unlock priority support and telehealth.</p>
                    <button class="btn-text">Upgrade Now &rarr;</button>
                </div>
            </div>
        </aside>

        <!-- MAIN WORKSPACE (Light Grey Base) -->
        <main class="workspace">
            
            <!-- TOP NAVIGATION (Solid White) -->
            <header class="top-nav">
                <div class="search-bar">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    <input type="text" placeholder="Search for appointments, doctors, reports..." />
                </div>
                
                <div class="top-actions">
                    <button class="icon-btn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                        <span class="notification-dot"></span>
                    </button>
                    <div class="user-profile">
                        <div class="avatar-placeholder">PM</div>
                        <span class="user-name">PIYUSH MAHARANA</span>
                    </div>
                </div>
            </header>

            <div v-if="isLoading" class="content-area loading-state">
                <div class="spinner"></div><p>Establishing secure connection...</p>
            </div>

            <div v-else class="content-area">
                
                <!-- GREETING & QUICK STATS -->
                <section class="top-widgets">
                    <div class="greeting-card">
                        <h1>Good morning, PIYUSH! 👋</h1>
                        <p>Manage your appointments and access your medical records securely.</p>
                    </div>
                    
                    <!-- Solid White Stat Cards -->
                    <div class="stat-card">
                        <div class="stat-icon bg-teal-light">
                            <svg viewBox="0 0 24 24" fill="none" stroke="#0f766e" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                        </div>
                        <div class="stat-info">
                            <h3>{{ patientData?.upcoming_appointments?.length || 0 }}</h3>
                            <p>Upcoming</p>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon bg-emerald-light">
                            <svg viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                        </div>
                        <div class="stat-info">
                            <h3>{{ historyData?.length || 0 }}</h3>
                            <p>Records</p>
                        </div>
                    </div>

                    <button @click="goToBooking" class="btn-primary">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                        Book Consultation
                    </button>
                </section>

                <!-- TAB 1: UPCOMING APPOINTMENTS -->
                <section v-if="activeTab === 'upcoming'" class="data-section fade-in">
                    <div class="section-header">
                        <h2>Upcoming Appointments</h2>
                        <button class="btn-link">View All &rarr;</button>
                    </div>
                    
                    <!-- Solid White Table Card -->
                    <div class="table-card">
                        <table class="clean-table" v-if="patientData?.upcoming_appointments?.length > 0">
                            <thead>
                                <tr>
                                    <th>Date & Time</th>
                                    <th>Doctor</th>
                                    <th>Department</th>
                                    <th>Status</th>
                                    <th class="text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="appt in patientData.upcoming_appointments" :key="appt.id">
                                    <td>
                                        <div class="datetime"><strong>{{ appt.date }}</strong><span>{{ appt.time }}</span></div>
                                    </td>
                                    <td>
                                        <div class="doc-profile">
                                            <div class="doc-avatar"></div>
                                            <div class="doc-name"><strong>Dr. {{ appt.doctor_name }}</strong><span>Specialist</span></div>
                                        </div>
                                    </td>
                                    <td>{{ appt.department }}</td>
                                    <!-- Use Emerald green for confirmed, not ruby -->
                                    <td><span class="status-pill status-confirmed"><span class="dot"></span> Confirmed</span></td>
                                    <td class="text-right actions-cell">
                                        <button class="btn-outline">Reschedule</button>
                                        <button @click="cancelAppointment(appt.id)" class="btn-outline-danger">Cancel</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <div v-else class="empty-state">No upcoming appointments.</div>
                    </div>
                </section>

                <!-- TAB 2: MEDICAL HISTORY -->
                <section v-if="activeTab === 'history'" class="data-section fade-in">
                    <div class="section-header">
                        <h2>Medical History</h2>
                    </div>
                    
                    <div class="history-grid" v-if="historyData?.length > 0">
                        <div v-for="record in historyData" :key="record.id" class="history-card">
                            <div class="card-head">
                                <span class="date">{{ record.date }}</span>
                                <span :class="['status-pill', record.status === 'Completed' ? 'status-confirmed' : 'status-cancelled']">
                                    <span class="dot"></span> {{ record.status }}
                                </span>
                            </div>
                            <div class="card-body">
                                <h4>Dr. {{ record.doctor_name }} <span class="dept">({{ record.department }})</span></h4>
                                <div class="diag-info" v-if="record.status === 'Completed'">
                                    <p><strong>Diagnosis:</strong> {{ record.diagnosis }}</p>
                                    <p class="truncate"><strong>Rx:</strong> {{ record.prescription }}</p>
                                </div>
                            </div>
                            <div class="card-foot" v-if="record.status === 'Completed'">
                                <button @click="downloadPrescription(record)" class="btn-outline w-100">Download Report</button>
                            </div>
                        </div>
                    </div>
                    <div v-else class="table-card empty-state">No medical history found.</div>
                </section>

                <!-- HEALTH SUMMARY (New wide elevated card with 4-Block layout) -->
                <section class="health-summary-section mt-2 fade-in">
                    <div class="summary-card-elevated">
                        
                        <div class="summary-left">
                            <h2>feel better, <br/>PIYUSH MAHARANA</h2>
                            <p>Your health at a glance.</p>
                        </div>
                        
                        <div class="summary-middle">
                            <!-- Heart Rate (Updated Icon) -->
                            <div class="summary-data-block">
                                <div class="icon-head icon-head-red">❤️</div>
                                <span class="label">Heart Rate</span>
                                <span class="value">72 <small>bpm</small></span>
                                <span class="status-green">🟢 Normal</span>
                            </div>

                            <!-- Blood Pressure (Updated Icon) -->
                            <div class="summary-data-block">
                                <div class="icon-head icon-head-blue">💧</div>
                                <span class="label">Blood Pressure</span>
                                <span class="value">120/80 <small>mmHg</small></span>
                                <span class="status-green">🟢 Normal</span>
                            </div>

                            <!-- NEW: Last Checkup -->
                            <div class="summary-data-block">
                                <div class="icon-head icon-head-purple">📅</div>
                                <span class="label">Last Checkup</span>
                                <span class="value">12 Mar 2026</span>
                                <span class="type-text">General Checkup</span>
                            </div>

                            <!-- NEW: Next Appointment -->
                            <div class="summary-data-block">
                                <div class="icon-head icon-head-indigo">🕒</div>
                                <span class="label">Next Appointment</span>
                                <span class="value">24 Apr 2026</span>
                                <span class="type-text">10:30 AM</span>
                            </div>
                        </div>

                        <div class="summary-right">
                            <img src="@/assets/health-heart.png" alt="Health Summary Graphic" style="width: 120px; height: auto;" />
                        </div>
                    </div>
                </section>

            </div>
        </main>
    </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* --- BASE --- */
.clean-layout {
    font-family: 'Plus Jakarta Sans', sans-serif;
    display: flex;
    height: 100vh;
    background-color: #ffffff; 
    color: #1e293b;
    overflow: hidden;
}

/* --- SIDE NAV --- */
.side-nav {
    width: 230px; /* Slimmed down to give main content more room */
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    padding: 1.5rem 1.2rem;
    z-index: 20;
}
.brand-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 2.5rem; cursor: pointer; }
.logo-mark { background: #0f766e; color: white; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 8px; font-weight: 800; }
.logo-text { font-size: 1.15rem; font-weight: 800; color: #0f172a; }

.nav-links { display: flex; flex-direction: column; gap: 0.4rem; flex: 1; }
.nav-btn { display: flex; align-items: center; gap: 0.8rem; padding: 0.8rem 1rem; border-radius: 10px; border: none; background: transparent; color: #64748b; font-weight: 600; font-size: 0.9rem; cursor: pointer; text-decoration: none; transition: all 0.2s; }
.nav-btn:hover { background: #f8fafc; color: #0f766e; }
.nav-btn.active { background: #f0fdfa; color: #0f766e; }
.nav-icon { width: 18px; height: 18px; }

.premium-upgrade { background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid #e2e8f0; }
.premium-upgrade h5 { color: #0f766e; margin: 0 0 0.3rem 0; font-size: 0.9rem; }
.premium-upgrade p { font-size: 0.75rem; color: #64748b; margin: 0 0 0.8rem 0; line-height: 1.4; }
.btn-text { background: none; border: none; color: #0f172a; font-weight: 700; font-size: 0.8rem; cursor: pointer; padding: 0; }

/* --- WORKSPACE & TOP NAV --- */
.workspace { 
    flex: 1; 
    display: flex; 
    flex-direction: column; 
    overflow: hidden; 
    background-color: #f1f5f9; 
}

.top-nav { height: 70px; background: #ffffff; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; padding: 0 2rem; }
.search-bar { display: flex; align-items: center; gap: 0.6rem; background: #f8fafc; padding: 0.5rem 1rem; border-radius: 8px; width: 350px; border: 1px solid #e2e8f0; }
.search-bar svg { width: 16px; height: 16px; color: #94a3b8; }
.search-bar input { border: none; background: transparent; outline: none; width: 100%; font-family: inherit; font-size: 0.85rem; color: #1e293b; }

.top-actions { display: flex; align-items: center; gap: 1.2rem; }
.icon-btn { background: none; border: none; position: relative; cursor: pointer; color: #64748b; }
.icon-btn svg { width: 20px; height: 20px; }
.notification-dot { position: absolute; top: 0; right: 2px; width: 8px; height: 8px; background: #ef4444; border-radius: 50%; border: 2px solid white; }

.user-profile { display: flex; align-items: center; gap: 0.8rem; cursor: pointer; padding-left: 1.2rem; border-left: 1px solid #e2e8f0; }
.avatar-placeholder { width: 32px; height: 32px; background: #e0e7ff; color: #4f46e5; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.8rem; }
.user-name { font-weight: 600; font-size: 0.85rem; color: #1e293b; }

/* --- CONTENT AREA --- */
.content-area { padding: 1.5rem 2rem; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 1.5rem; }

/* TOP WIDGETS */
.top-widgets { display: grid; grid-template-columns: 2.5fr 1fr 1fr 1.2fr; gap: 1.2rem; align-items: stretch; }
.greeting-card { display: flex; flex-direction: column; justify-content: center; }
/* Reduced font size so names don't wrap */
.greeting-card h1 { font-size: 1.5rem; font-weight: 800; margin: 0 0 0.3rem 0; letter-spacing: -0.5px; line-height: 1.2; }
.greeting-card p { color: #64748b; margin: 0; font-size: 0.9rem; line-height: 1.4; }

.stat-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1rem; display: flex; align-items: center; gap: 0.8rem; box-shadow: 0 2px 10px rgba(0,0,0,0.02); }
.stat-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stat-icon svg { width: 20px; height: 20px; }
.bg-teal-light { background: #ccfbf1; }
.bg-emerald-light { background: #dcfce7; }
.stat-info h3 { margin: 0; font-size: 1.3rem; font-weight: 800; line-height: 1; }
.stat-info p { margin: 0.2rem 0 0 0; font-size: 0.75rem; color: #64748b; font-weight: 600; }

.btn-primary { background: #0f766e; color: white; border: none; border-radius: 14px; font-weight: 700; font-size: 0.9rem; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.4rem; transition: 0.2s; font-family: inherit; box-shadow: 0 4px 15px rgba(15, 118, 110, 0.2); }
.btn-primary:hover { background: #115e59; transform: translateY(-2px); }
.btn-primary svg { width: 20px; height: 20px; }

/* DATA SECTIONS & TABLES */
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; }
.section-header h2 { font-size: 1.05rem; font-weight: 700; margin: 0; color: #334155; }
.btn-link { background: none; border: none; color: #0f766e; font-weight: 600; font-size: 0.85rem; cursor: pointer; }

.table-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 0.5rem 1.5rem; box-shadow: 0 2px 10px rgba(0,0,0,0.02); overflow-x: auto; }
.clean-table { width: 100%; border-collapse: collapse; min-width: 600px; }
.clean-table th { text-align: left; padding: 1rem 0.5rem; font-size: 0.7rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #e2e8f0; }
.clean-table td { padding: 1rem 0.5rem; border-bottom: 1px solid #f8fafc; vertical-align: middle; }
.clean-table tr:last-child td { border-bottom: none; }

.datetime strong { display: block; font-weight: 700; color: #1e293b; font-size: 0.9rem; }
.datetime span { color: #64748b; font-size: 0.75rem; }

.doc-profile { display: flex; align-items: center; gap: 0.6rem; }
.doc-avatar { width: 28px; height: 28px; background: #e2e8f0; border-radius: 50%; }
.doc-name strong { display: block; font-weight: 700; font-size: 0.9rem; color: #1e293b; text-transform: capitalize; }
.doc-name span { font-size: 0.75rem; color: #64748b; }

.status-pill { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0.6rem; border-radius: 20px; font-size: 0.75rem; font-weight: 700; white-space: nowrap; }
.dot { width: 6px; height: 6px; border-radius: 50%; }
.status-confirmed { background: #f0fdf4; color: #15803d; }
.status-confirmed .dot { background: #22c55e; }
.status-cancelled { background: #fef2f2; color: #b91c1c; }
.status-cancelled .dot { background: #ef4444; }

.actions-cell { display: flex; gap: 0.5rem; justify-content: flex-end; }
.btn-outline, .btn-outline-danger { background: transparent; padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 600; font-size: 0.75rem; cursor: pointer; transition: 0.2s; white-space: nowrap; }
.btn-outline { border: 1px solid #e2e8f0; color: #475569; }
.btn-outline:hover { border-color: #0f766e; color: #0f766e; }
.btn-outline-danger { border: 1px solid #fecaca; color: #ef4444; }
.btn-outline-danger:hover { background: #fef2f2; }

/* HISTORY GRID */
.history-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.2rem; }
.history-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1.2rem; box-shadow: 0 2px 10px rgba(0,0,0,0.02); }
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; border-bottom: 1px solid #f8fafc; padding-bottom: 0.6rem; }
.card-head .date { font-weight: 700; color: #1e293b; font-size: 0.85rem; }
.card-body h4 { margin: 0 0 0.6rem 0; font-size: 0.95rem; color: #1e293b; }
.card-body .dept { color: #64748b; font-weight: 500; font-size: 0.8rem; }
.diag-info p { margin: 0 0 0.3rem 0; font-size: 0.8rem; color: #475569; }
.truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* HEALTH SUMMARY SECTION (Fluid Flexbox Update) */
.summary-card-elevated {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 4px 14px rgba(0,0,0,0.03); 
}

.summary-left { flex: 1; min-width: 140px; }
.summary-left h2 { font-size: 1.2rem; font-weight: 800; color: #1e293b; margin: 0 0 0.4rem 0; line-height: 1.2; letter-spacing: -0.5px; }
.summary-left p { color: #64748b; font-size: 0.8rem; margin: 0; line-height: 1.3; }

.summary-middle { 
    flex: 3; 
    display: flex; 
    justify-content: space-between; /* Spreads items evenly without squishing */
    align-items: center;
    gap: 1rem;
    padding: 0 1.5rem; 
    border-left: 1px solid #e2e8f0; 
    border-right: 1px solid #e2e8f0; 
}

.summary-data-block { display: flex; flex-direction: column; gap: 0.2rem; }
.icon-head { font-size: 1rem; margin-bottom: 0.3rem; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 6px; }
.icon-head-red { background: #fee2e2; }
.icon-head-blue { background: #d1e9f1; } 
.icon-head-purple { background: #ddd5f2; } 
.icon-head-indigo { background: #c7c6e6; } 

.summary-data-block .label { font-size: 0.75rem; font-weight: 600; color: #64748b; margin-bottom: 0.1rem; white-space: nowrap; }
.summary-data-block .value { font-size: 1.15rem; font-weight: 800; color: #1e293b; white-space: nowrap; }
.summary-data-block .value small { font-size: 0.75rem; font-weight: 600; color: #94a3b8; }
.status-green, .type-text { font-size: 0.75rem; font-weight: 600; white-space: nowrap; }
.status-green { color: #10b981; }
.type-text { color: #64748b; }

.summary-right { flex: 0.5; display: flex; justify-content: center; align-items: center; min-width: 80px; }
.summary-right img { width: 100%; max-width: 90px; height: auto; object-fit: contain; }

/* LOADING / ERROR STATES */
.loading-state, .error-alert { justify-content: center; align-items: center; text-align: center; }
.spinner { width: 32px; height: 32px; border: 3px solid #e2e8f0; border-top-color: #0f766e; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }
.empty-state { padding: 2rem; text-align: center; color: #64748b; font-size: 0.9rem; }
</style>