<script setup>
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import axios from 'axios';

// --- CHART.JS IMPORTS ---
import { Chart as ChartJS, ArcElement, Tooltip, Legend, Title } from 'chart.js'
import { Pie, Doughnut } from 'vue-chartjs'

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, Title)

const authStore = useAuthStore()
const router = useRouter()

const activeTab = ref('overview')

// --- OVERVIEW STATE ---
const stats = ref({
    total_doctors: 0,
    total_patients: 0,
    total_appointments: 0,
    recent_activity: [],
    charts: null // Holds the raw chart data from Flask
})
const isLoading = ref(true)
const errorMessage = ref('')

// --- DEPARTMENT & STAFF/PATIENT STATE ---
const departments = ref([])
const newDepartment = ref({ name: '', description: '' })
const isAddingDept = ref(false)
const deptMessage = ref(''); const deptError = ref('')

const newDoctor = ref({ name: '', email: '', username: '', password: '', department_id: '', experience: '' })
const isRegistering = ref(false)
const registerMessage = ref(''); const registerError = ref('')

const systemUsers = ref({ doctors: [], patients: [] })

// --- CHART DATA FORMATTING (COMPUTED PROPS) ---
// These automatically format the Flask data into the exact structure Chart.js demands
const departmentChartData = computed(() => {
    if (!stats.value.charts) return null;
    return {
        labels: stats.value.charts.departments.labels,
        datasets: [{
            data: stats.value.charts.departments.data,
            backgroundColor: ['#3498db', '#2ecc71', '#9b59b6', '#f1c40f', '#e67e22', '#e74c3c'],
            borderWidth: 1
        }]
    }
})

const appointmentChartData = computed(() => {
    if (!stats.value.charts) return null;
    return {
        labels: stats.value.charts.appointments.labels,
        datasets: [{
            data: stats.value.charts.appointments.data,
            backgroundColor: ['#3498db', '#2ecc71', '#e74c3c'], // Blue (Booked), Green (Completed), Red (Cancelled)
            borderWidth: 1
        }]
    }
})

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { position: 'bottom' }
    }
}

// --- FETCH FUNCTIONS ---
const fetchDashboard = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/admin/dashboard', { headers: { Authorization: `Bearer ${authStore.token}` } })
        stats.value = response.data
    } catch (error) {
        errorMessage.value = "Could not load hospital analytics."
    } finally {
        isLoading.value = false
    }
}

const fetchDepartments = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/admin/departments', { headers: { Authorization: `Bearer ${authStore.token}` } })
        departments.value = response.data
    } catch (error) {}
}

const fetchSystemUsers = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/admin/system-users', { headers: { Authorization: `Bearer ${authStore.token}` } })
        systemUsers.value = response.data
    } catch (error) {}
}

// --- CRUD & ACTION FUNCTIONS ---
const addDepartment = async () => {
    isAddingDept.value = true; deptMessage.value = ''; deptError.value = ''
    try {
        const response = await axios.post('http://127.0.0.1:5000/api/admin/departments', newDepartment.value, { headers: { Authorization: `Bearer ${authStore.token}` } })
        deptMessage.value = response.data.msg
        newDepartment.value = { name: '', description: '' }
        fetchDepartments()
    } catch (error) { deptError.value = error.response?.data?.msg || "Failed to add department." } 
    finally { isAddingDept.value = false }
}

const deleteDepartment = async (id) => {
    if (!confirm("Are you sure you want to delete this department?")) return;
    try {
        const response = await axios.delete(`http://127.0.0.1:5000/api/admin/departments/${id}`, { headers: { Authorization: `Bearer ${authStore.token}` } })
        alert(response.data.msg)
        fetchDepartments()
    } catch (error) { alert(error.response?.data?.msg || "Failed to delete department.") }
}

const registerDoctor = async () => {
    isRegistering.value = true; registerMessage.value = ''; registerError.value = ''
    try {
        const response = await axios.post('http://127.0.0.1:5000/api/admin/doctors', newDoctor.value, { headers: { Authorization: `Bearer ${authStore.token}` } })
        registerMessage.value = response.data.msg
        newDoctor.value = { name: '', email: '', username: '', password: '', department_id: '', experience: '' }
        fetchDashboard(); fetchDepartments(); fetchSystemUsers();
    } catch (error) { registerError.value = error.response?.data?.msg || "Failed to register the doctor." } 
    finally { isRegistering.value = false }
}

const toggleUserStatus = async (userId, currentStatus) => {
    const action = currentStatus === 'active' ? 'blacklist' : 'reactivate';
    if (!confirm(`Are you sure you want to ${action} this user?`)) return;
    try {
        const response = await axios.patch(`http://127.0.0.1:5000/api/admin/users/${userId}/toggle-status`, {}, { headers: { Authorization: `Bearer ${authStore.token}` } })
        alert(response.data.msg)
        fetchSystemUsers()
    } catch (error) { alert(error.response?.data?.msg || "Failed to update user status.") }
}

const handleLogout = () => {
    authStore.logout(); router.push('/login')
}

onMounted(() => {
    fetchDashboard(); fetchDepartments(); fetchSystemUsers();
})
</script>

<template>
    <div class="dashboard-container">
        
        <div class="dashboard-header">
            <h2>Admin Command Center</h2>
            <button @click="handleLogout" class="logout-btn">Logout</button>
        </div>

        <div class="tabs">
            <button :class="{ active: activeTab === 'overview' }" @click="activeTab = 'overview'">System Overview</button>
            <button :class="{ active: activeTab === 'departments' }" @click="activeTab = 'departments'">Manage Departments</button>
            <button :class="{ active: activeTab === 'staff' }" @click="activeTab = 'staff'">Manage Staff</button>
            <button :class="{ active: activeTab === 'patients' }" @click="activeTab = 'patients'">Manage Patients</button>
        </div>

        <div v-if="activeTab === 'overview'" class="tab-content">
            <div v-if="isLoading" class="loading-state">Aggregating hospital data...</div>
            <div v-else-if="errorMessage" class="error-message">{{ errorMessage }}</div>
            <div v-else>
                
                <div class="stats-grid">
                    <div class="stat-card"><h3>Total Patients</h3><p class="stat-number">{{ stats.total_patients }}</p></div>
                    <div class="stat-card"><h3>Total Doctors</h3><p class="stat-number">{{ stats.total_doctors }}</p></div>
                    <div class="stat-card"><h3>Total Appointments</h3><p class="stat-number">{{ stats.total_appointments }}</p></div>
                </div>

                <div class="charts-grid" v-if="stats.charts">
                    <div class="chart-card">
                        <h3>Staff Distribution by Department</h3>
                        <div class="chart-wrapper">
                            <Pie v-if="departmentChartData" :data="departmentChartData" :options="chartOptions" />
                        </div>
                    </div>
                    
                    <div class="chart-card">
                        <h3>Appointment Health (Status)</h3>
                        <div class="chart-wrapper">
                            <Doughnut v-if="appointmentChartData" :data="appointmentChartData" :options="chartOptions" />
                        </div>
                    </div>
                </div>

                <div class="recent-activity">
                    <h3>Live Hospital Feed (Recent Appointments)</h3>
                    <table class="data-table">
                        <thead><tr><th>Appt ID</th><th>Date</th><th>Doctor</th><th>Patient</th><th>Status</th></tr></thead>
                        <tbody>
                            <tr v-for="appt in stats.recent_activity" :key="appt.id">
                                <td><strong>#{{ appt.id }}</strong></td><td>{{ appt.date }}</td><td>Dr. {{ appt.doctor }}</td><td>{{ appt.patient }}</td>
                                <td><span :class="['status-badge', appt.status.toLowerCase()]">{{ appt.status }}</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div v-if="activeTab === 'departments'" class="tab-content">
            <div class="split-layout">
                <div class="form-section">
                    <h3>Add New Department</h3>
                    <div v-if="deptMessage" class="success-message">{{ deptMessage }}</div>
                    <div v-if="deptError" class="error-message">{{ deptError }}</div>
                    <form @submit.prevent="addDepartment" class="admin-form">
                        <div class="form-group"><label>Department Name</label><input type="text" v-model="newDepartment.name" required></div>
                        <div class="form-group"><label>Description (Optional)</label><textarea v-model="newDepartment.description" rows="3"></textarea></div>
                        <button type="submit" class="btn-primary" :disabled="isAddingDept">Create Department</button>
                    </form>
                </div>
                <div class="list-section">
                    <h3>Current Departments</h3>
                    <table class="data-table">
                        <thead><tr><th>Name</th><th>Doctors</th><th>Action</th></tr></thead>
                        <tbody>
                            <tr v-for="dept in departments" :key="dept.id">
                                <td><strong>{{ dept.name }}</strong></td><td>{{ dept.doctor_count }}</td>
                                <td><button @click="deleteDepartment(dept.id)" class="btn-delete" :disabled="dept.doctor_count > 0">Delete</button></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div v-if="activeTab === 'staff'" class="tab-content">
            <div class="staff-management-container">
                <h3>Register New Doctor</h3>
                <div v-if="registerMessage" class="success-message">{{ registerMessage }}</div>
                <div v-if="registerError" class="error-message">{{ registerError }}</div>

                <form @submit.prevent="registerDoctor" class="admin-form" style="margin-bottom: 3rem;">
                    <div class="form-row">
                        <div class="form-group"><label>Full Name</label><input type="text" v-model="newDoctor.name" required></div>
                        <div class="form-group">
                            <label>Department</label>
                            <select v-model="newDoctor.department_id" required>
                                <option value="" disabled>Select a Department...</option>
                                <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group"><label>Email Address</label><input type="email" v-model="newDoctor.email" required></div>
                        <div class="form-group"><label>System Username</label><input type="text" v-model="newDoctor.username" required></div>
                        <div class="form-group"><label>Temporary Password</label><input type="password" v-model="newDoctor.password" required></div>
                    </div>
                    <button type="submit" class="btn-primary" :disabled="isRegistering">Register Doctor</button>
                </form>

                <hr class="divider">
                <h3>Staff Directory & Access Control</h3>
                <table class="data-table">
                    <thead><tr><th>Doctor Name</th><th>Department</th><th>Email</th><th>System Status</th><th>Action</th></tr></thead>
                    <tbody>
                        <tr v-for="doc in systemUsers.doctors" :key="doc.id">
                            <td><strong>Dr. {{ doc.name }}</strong></td><td>{{ doc.department }}</td><td>{{ doc.email }}</td>
                            <td><span :class="['system-status', doc.status]">{{ doc.status.toUpperCase() }}</span></td>
                            <td>
                                <button @click="toggleUserStatus(doc.user_id, doc.status)" :class="doc.status === 'active' ? 'btn-warning' : 'btn-success'">
                                    {{ doc.status === 'active' ? 'Suspend Access' : 'Reactivate' }}
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div v-if="activeTab === 'patients'" class="tab-content">
            <div class="list-section">
                <h3>Patient Database</h3>
                <p class="subtitle">Monitor registered patients and manage system access.</p>
                <table class="data-table">
                    <thead><tr><th>Patient Name</th><th>Contact</th><th>Email Address</th><th>System Status</th><th>Action</th></tr></thead>
                    <tbody>
                        <tr v-for="pat in systemUsers.patients" :key="pat.id">
                            <td><strong>{{ pat.name }}</strong></td><td>{{ pat.contact }}</td><td>{{ pat.email }}</td>
                            <td><span :class="['system-status', pat.status]">{{ pat.status.toUpperCase() }}</span></td>
                            <td>
                                <button @click="toggleUserStatus(pat.user_id, pat.status)" :class="pat.status === 'active' ? 'btn-warning' : 'btn-success'">
                                    {{ pat.status === 'active' ? 'Suspend Access' : 'Reactivate' }}
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div v-if="systemUsers.patients.length === 0" class="empty-state">No patients registered in the system.</div>
            </div>
        </div>

    </div>
</template>

<style scoped>
/* Core Dashboard Styles */
.dashboard-container { max-width: 1100px; margin: 2rem auto; padding: 1rem; font-family: Arial, sans-serif; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 3px solid #2c3e50; padding-bottom: 1rem; }
.dashboard-header h2 { color: #2c3e50; margin: 0; }
.logout-btn { background-color: #e74c3c; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }

.tabs { display: flex; gap: 10px; margin-bottom: 1rem; border-bottom: 2px solid #eee; }
.tabs button { padding: 10px 20px; border: none; background: none; font-size: 1rem; font-weight: bold; color: #7f8c8d; cursor: pointer; border-bottom: 3px solid transparent; transition: 0.2s; }
.tabs button.active { color: #8e44ad; border-bottom-color: #8e44ad; }
.tab-content { background: white; padding: 2rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem; }
.stat-card { background: #f8f9fa; padding: 2rem; border-radius: 8px; text-align: center; border-top: 4px solid #8e44ad; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.stat-number { font-size: 3rem; font-weight: bold; color: #2c3e50; margin: 0; }

/* --- NEW: CHART STYLES --- */
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 3rem; }
.chart-card { background: #ffffff; padding: 1.5rem; border-radius: 8px; border: 1px solid #eee; box-shadow: 0 2px 4px rgba(0,0,0,0.02); text-align: center; }
.chart-card h3 { margin-top: 0; color: #2c3e50; font-size: 1.1rem; border-bottom: 2px solid #f8f9fa; padding-bottom: 0.5rem; margin-bottom: 1.5rem; }
.chart-wrapper { position: relative; height: 250px; width: 100%; display: flex; justify-content: center; }

/* Tables & Badges */
.data-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
.data-table th, .data-table td { padding: 1rem; border-bottom: 1px solid #eee; text-align: left; }
.data-table th { background: #f8f9fa; color: #2c3e50; }

.status-badge { padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
.status-badge.booked { background: #e8f4f8; color: #3498db; }
.status-badge.completed { background: #e8f8f5; color: #27ae60; }
.status-badge.cancelled { background: #fdedec; color: #e74c3c; }

.system-status { padding: 0.3rem 0.6rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
.system-status.active { background: #e8f8f5; color: #27ae60; border: 1px solid #27ae60; }
.system-status.blacklisted { background: #fdedec; color: #e74c3c; border: 1px solid #e74c3c; }

/* Forms & Buttons */
.admin-form { display: flex; flex-direction: column; gap: 1.5rem; background: #f8f9fa; padding: 2rem; border-radius: 8px; border: 1px solid #eee; }
.form-row { display: flex; gap: 1.5rem; }
.form-row .form-group { flex: 1; }
.form-group { display: flex; flex-direction: column; gap: 0.5rem; }
.form-group input, .form-group select, .form-group textarea { padding: 0.8rem; border: 1px solid #ccc; border-radius: 4px; }
.btn-primary { background: #8e44ad; color: white; border: none; padding: 1rem; border-radius: 8px; cursor: pointer; font-weight: bold;}
.btn-delete { background: #e74c3c; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer;}
.btn-warning { background: #e67e22; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-weight: bold;}
.btn-success { background: #27ae60; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-weight: bold;}
.divider { border: 0; height: 1px; background: #eee; margin: 2rem 0; }
.error-message { background: #fdedec; color: #e74c3c; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center; }
.success-message { background: #e8f8f5; color: #27ae60; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;}
.empty-state { text-align: center; padding: 3rem; color: #7f8c8d; font-style: italic; }
.split-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
</style>