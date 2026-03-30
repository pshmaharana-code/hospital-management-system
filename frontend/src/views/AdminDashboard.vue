<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import axios from 'axios';

const authStore = useAuthStore()
const router = useRouter()

const activeTab = ref('overview')

// --- OVERVIEW STATE ---
const stats = ref({
    total_doctors: 0,
    total_patients: 0,
    total_appointments: 0,
    recent_activity: []
})
const isLoading = ref(true)
const errorMessage = ref('')

// --- DEPARTMENT STATE (NEW) ---
const departments = ref([])
const newDepartment = ref({ name: '', description: '' })
const isAddingDept = ref(false)
const deptMessage = ref('')
const deptError = ref('')

// --- STAFF STATE (UPDATED) ---
const newDoctor = ref({
    name: '',
    username: '', 
    password: '',
    department_id: '', // <-- Now expecting the integer ID!
    experience: ''
})
const isRegistering = ref(false)
const registerMessage = ref('')
const registerError = ref('')

// --- FETCH FUNCTIONS ---
const fetchDashboard = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/admin/dashboard', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        stats.value = response.data
    } catch (error) {
        console.error("Failed to load admin dashboard:", error)
        errorMessage.value = "Could not load hospital analytics."
    } finally {
        isLoading.value = false
    }
}

const fetchDepartments = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/admin/departments', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        departments.value = response.data
    } catch (error) {
        console.error("Failed to load departments:", error)
    }
}

// --- CRUD FUNCTIONS ---
const addDepartment = async () => {
    isAddingDept.value = true
    deptMessage.value = ''
    deptError.value = ''
    try {
        const response = await axios.post('http://127.0.0.1:5000/api/admin/departments', newDepartment.value, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        deptMessage.value = response.data.msg
        newDepartment.value = { name: '', description: '' }
        fetchDepartments() // Instantly refresh the list
    } catch (error) {
        deptError.value = error.response?.data?.msg || "Failed to add department."
    } finally {
        isAddingDept.value = false
    }
}

const deleteDepartment = async (id) => {
    if (!confirm("Are you sure you want to delete this department?")) return;
    try {
        const response = await axios.delete(`http://127.0.0.1:5000/api/admin/departments/${id}`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        alert(response.data.msg)
        fetchDepartments() // Instantly refresh the list
    } catch (error) {
        alert(error.response?.data?.msg || "Failed to delete department.")
    }
}

const registerDoctor = async () => {
    isRegistering.value = true
    registerMessage.value = ''
    registerError.value = ''
    try {
        const response = await axios.post('http://127.0.0.1:5000/api/admin/doctors', newDoctor.value, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        registerMessage.value = response.data.msg
        newDoctor.value = { name: '', username: '', password: '', department_id: '', experience: '' }
        fetchDashboard() // Refresh stats
        fetchDepartments() // Refresh department doctor counts
    } catch (error) {
        registerError.value = error.response?.data?.msg || "Failed to register the doctor."
    } finally {
        isRegistering.value = false
    }
}

const handleLogout = () => {
    authStore.logout()
    router.push('/login')
}

onMounted(() => {
    fetchDashboard()
    fetchDepartments() // Fetch departments on load!
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
        </div>

        <div v-if="activeTab === 'overview'" class="tab-content">
            <div v-if="isLoading" class="loading-state">Aggregating hospital data...</div>
            <div v-else-if="errorMessage" class="error-message">{{ errorMessage }}</div>
            <div v-else>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Patients</h3>
                        <p class="stat-number">{{ stats.total_patients }}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Total Doctors</h3>
                        <p class="stat-number">{{ stats.total_doctors }}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Total Appointments</h3>
                        <p class="stat-number">{{ stats.total_appointments }}</p>
                    </div>
                </div>

                <div class="recent-activity">
                    <h3>Live Hospital Feed (Recent Appointments)</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Appt ID</th>
                                <th>Date</th>
                                <th>Doctor</th>
                                <th>Patient</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="appt in stats.recent_activity" :key="appt.id">
                                <td><strong>#{{ appt.id }}</strong></td>
                                <td>{{ appt.date }}</td>
                                <td>Dr. {{ appt.doctor }}</td>
                                <td>{{ appt.patient }}</td>
                                <td><span :class="['status-badge', appt.status.toLowerCase()]">{{ appt.status }}</span></td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="stats.recent_activity.length === 0" class="empty-state">
                        <p>No recent activity found in the system.</p>
                    </div>
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
                        <div class="form-group">
                            <label>Department Name</label>
                            <input type="text" v-model="newDepartment.name" placeholder="e.g. Cardiology" required>
                        </div>
                        <div class="form-group">
                            <label>Description (Optional)</label>
                            <textarea v-model="newDepartment.description" rows="3" placeholder="Brief overview of the department..."></textarea>
                        </div>
                        <button type="submit" class="btn-primary" :disabled="isAddingDept">
                            {{ isAddingDept ? 'Adding...' : 'Create Department' }}
                        </button>
                    </form>
                </div>

                <div class="list-section">
                    <h3>Current Departments</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Doctors</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="dept in departments" :key="dept.id">
                                <td><strong>{{ dept.name }}</strong></td>
                                <td>{{ dept.doctor_count }}</td>
                                <td>
                                    <button @click="deleteDepartment(dept.id)" class="btn-delete" :disabled="dept.doctor_count > 0">
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <p v-if="departments.length === 0" class="empty-state" style="padding: 1rem;">No departments configured.</p>
                </div>
            </div>
        </div>

        <div v-if="activeTab === 'staff'" class="tab-content">
            <div class="staff-management-container">
                <h3>Register New Doctor</h3>
                <p class="subtitle">Enter the physician's credentials to provision their hospital account.</p>

                <div v-if="registerMessage" class="success-message">{{ registerMessage }}</div>
                <div v-if="registerError" class="error-message">{{ registerError }}</div>

                <form @submit.prevent="registerDoctor" class="admin-form">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Full Name</label>
                            <input type="text" v-model="newDoctor.name" placeholder="e.g. Gregory House" required>
                        </div>
                        <div class="form-group">
                            <label>Department</label>
                            <select v-model="newDoctor.department_id" required>
                                <option value="" disabled>Select a Department...</option>
                                <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                                    {{ dept.name }}
                                </option>
                            </select>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>System Username</label>
                            <input type="text" v-model="newDoctor.username" placeholder="e.g. dr_house" required>
                        </div>
                        <div class="form-group">
                            <label>Temporary Password</label>
                            <input type="password" v-model="newDoctor.password" required>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Years of Experience (Optional)</label>
                            <input type="number" v-model="newDoctor.experience" min="0" placeholder="e.g. 10">
                        </div>
                    </div>

                    <button type="submit" class="btn-primary" :disabled="isRegistering">
                        {{ isRegistering ? 'Provisioning Account...' : 'Register Doctor' }}
                    </button>
                </form>
            </div>
        </div>

    </div>
</template>

<style scoped>
/* Core Layout */
.dashboard-container { max-width: 1100px; margin: 2rem auto; padding: 1rem; font-family: Arial, sans-serif; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 3px solid #2c3e50; padding-bottom: 1rem; }
.dashboard-header h2 { color: #2c3e50; margin: 0; }
.logout-btn { background-color: #e74c3c; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }

/* Tabs */
.tabs { display: flex; gap: 10px; margin-bottom: 1rem; border-bottom: 2px solid #eee; }
.tabs button { padding: 10px 20px; border: none; background: none; font-size: 1rem; font-weight: bold; color: #7f8c8d; cursor: pointer; border-bottom: 3px solid transparent; transition: 0.2s; }
.tabs button.active { color: #8e44ad; border-bottom-color: #8e44ad; }
.tab-content { background: white; padding: 2rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }

/* Analytics Cards & Table */
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 3rem; }
.stat-card { background: #f8f9fa; padding: 2rem; border-radius: 8px; text-align: center; border-top: 4px solid #8e44ad; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.stat-card h3 { margin: 0 0 1rem 0; color: #7f8c8d; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px; }
.stat-number { font-size: 3rem; font-weight: bold; color: #2c3e50; margin: 0; }

.recent-activity h3 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 0.5rem; margin-bottom: 1.5rem; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 1rem; border-bottom: 1px solid #eee; text-align: left; }
.data-table th { background: #f8f9fa; color: #2c3e50; }

.status-badge { padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
.status-badge.booked { background: #e8f4f8; color: #3498db; }
.status-badge.completed { background: #e8f8f5; color: #27ae60; }
.status-badge.cancelled { background: #fdedec; color: #e74c3c; }

/* Form Elements */
.staff-management-container h3, .form-section h3, .list-section h3 { color: #2c3e50; margin-bottom: 0.5rem; }
.subtitle { color: #7f8c8d; margin-bottom: 2rem; font-size: 0.95rem; }
.admin-form { display: flex; flex-direction: column; gap: 1.5rem; background: #f8f9fa; padding: 2rem; border-radius: 8px; border: 1px solid #eee; }
.form-row { display: flex; gap: 1.5rem; }
.form-row .form-group { flex: 1; }
.form-group { display: flex; flex-direction: column; gap: 0.5rem; }
.form-group label { font-weight: bold; color: #34495e; font-size: 0.9rem; }
.form-group input, .form-group select, .form-group textarea { padding: 0.8rem; border: 1px solid #ccc; border-radius: 4px; font-size: 1rem; transition: 0.2s; font-family: Arial, sans-serif; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { border-color: #8e44ad; outline: none; box-shadow: 0 0 0 2px rgba(142, 68, 173, 0.2); }

/* Buttons */
.btn-primary { background: #8e44ad; color: white; border: none; padding: 1rem; font-size: 1.1rem; font-weight: bold; border-radius: 8px; cursor: pointer; transition: 0.2s; margin-top: 1rem; }
.btn-primary:hover:not(:disabled) { background: #732d91; }
.btn-primary:disabled { background: #bdc3c7; cursor: not-allowed; }

.btn-delete { background: #e74c3c; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn-delete:hover:not(:disabled) { background: #c0392b; }
.btn-delete:disabled { background: #fab1a0; cursor: not-allowed; }

/* Layouts & States */
.split-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
@media (max-width: 768px) { .split-layout, .form-row { flex-direction: column; grid-template-columns: 1fr; gap: 1.5rem; } }

.error-message { background: #ffeaa7; color: #d63031; padding: 1rem; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 1rem; }
.success-message { background: #e8f8f5; color: #27ae60; padding: 1rem; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 1.5rem; border: 1px solid #2ecc71; }
.empty-state, .loading-state { text-align: center; padding: 3rem; color: #7f8c8d; font-style: italic; background: #f8f9fa; border-radius: 8px; }
</style>