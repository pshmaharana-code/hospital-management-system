<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import axios from 'axios';


// 1. open the vault
const authStore = useAuthStore()
const router = useRouter()

// 3. Create a reactive variable to hold the appointments once they arrive from Flask
const appointments = ref([])

const fetchDashboardData = async () => {
    try {
        // We must pin the VIP Badge (token) to the header of our request
        const response = await axios.get('http://127.0.0.1:5000/api/patient/dashboard',{
            headers: {
                Authorization: `Bearer ${authStore.token}`
            }
        })
        // Look at the Flask code: you named the list "upcomming_appointments"
        appointments.value = response.data.upcomming_appointments

        console.log('Appointments fetched successfully', appointments.value)
    } catch (error) {
        console.log('Failed to fetch dashboard data:', error)
        if (error.response && error.response.status == 401) {
            alert("Your session expaired. Please log in again.")
            handleLogout()
        }
    }
}

const cancelAppointment = async (id) => {
    // Confirm with the user first so they don't click it by accident
    if (!confirm("Are you sure you want to cancel this appointment?")) return;
    try {
        // Send the POST request to our new Flask route with the VIP badge
        await axios.post(`http://127.0.0.1:5000/api/patient/appointment/cancel/${id}`, {}, {
            headers: { Authorization: `Bearer ${authStore.token}`}
        });
        alert("Appointmetn canceled successfully!");

        // MAGIC VUE TRICK: Instead of refreshing the page, we just filter the cancelled 
        // appointment out of our local array. Vue instantly removes it from the screen!
        appointments.value = appointments.value.filter(appt => appt.id !== id);
    } catch (error) {
        console.error("Failed to cancel appointment", error);
        alert("Could not cancel the appointmetn. Please try again.");
    }
}

// 5. onMounted runs exactly ONE time, the millisecond the page loads
onMounted(() => {
    fetchDashboardData()
})


const handleLogout = () => {
    authStore.logout()  // this instantly implies the vault
    router.push('/login')   // change the channel back to the login page.
}
</script>

<template>
    <div class="dashboard-container">
        <div class="dashboard-header">
            <h2>Patient Dashboard</h2>
            <div class="header-buttons">
                <router-link to="/patient-profile" class="btn-secondary">
                    Profile Settings
                </router-link>
                <router-link to="/patient-history" class="btn-secondary">
                    View History
                </router-link>
                <router-link to="/book-appointment" class="btn-primary">
                    + Book New Appointment
                </router-link>
            </div>
        </div>

        <div class="welcome-card" v-if="authStore.user">
            <h3>Welcome back, {{  authStore.user.username }}!</h3>
            <p>Your Role: {{ authStore.user.role }}</p>
            <button @click="handleLogout" class="logout-btn">Logout</button>
        </div>

        <div class="appointments-section">
            <h3>Your Upcoming Appointments</h3>

            <div v-if="appointments.length > 0" class="table-responsive">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Doctor</th>
                            <th>Department</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="appt in appointments" :key="appt.id">
                            <td>{{ appt.date }}</td>
                            <td>{{ appt.time }}</td>
                            <td>Dr. {{ appt.doctor_name }}</td>
                            <td>{{ appt.department }}</td>
                            <td>
                                <button @click="cancelAppointment(appt.id)" class="cancel-btn">Cancel</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div v-else class="empty-class">
                <p>You have no upcoming appointments</p>
            </div>


        </div>
    </div>
</template>

<style scoped>
.dashboard-container {
    max-width: 600px;
    margin: 3rem auto;
    text-align: center;
    font-family: Arial, sans-serif;
}

.welcome-card {
    background: #e8f4f8;
    padding: 2rem;
    border-radius: 8px;
    border: 1px solid #bce8f1;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.logout-btn {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}
.logout-btn:hover {
  background-color: #c0392b;
}
.appointments-section {
    margin-top: 3rem;
    text-align: left;
}
.table-responsive {
    overflow-x: auto;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.data-table th, .data-table td {
  padding: 1rem;
  border-bottom: 1px solid #eee;
  text-align: left;
}
.data-table th {
  background-color: #2c3e50;
  color: white;
  font-weight: bold;
}
.data-table tr:hover {
  background-color: #f8f9fa;
}
.empty-state {
  padding: 2rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  text-align: center;
  color: #666;
}
.cancel-btn {
  padding: 0.4rem 0.8rem;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}
.cancel-btn:hover {
  background-color: #c0392b;
}
/* --- Header & Button Styles --- */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.dashboard-header h2 {
  margin: 0;
}

.btn-primary {
  background-color: #3498db;
  color: white;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  text-decoration: none;
  font-weight: bold;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background-color: #2980b9;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.btn-secondary {
  background: #95a5a6;
  color: white; 
  padding: 0.6rem 1.2rem; 
  border-radius: 6px; 
  text-decoration: none; 
  font-weight: bold; 
}
/* --- Header & Button Styles --- */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap; /* Allows title and buttons to stack if screen is narrow */
  gap: 1rem;
}

.dashboard-header h2 {
  margin: 0;
}

/* NEW: Neatly spaces out the buttons without overlapping */
.header-buttons {
  display: flex;
  gap: 15px; 
  flex-wrap: wrap; 
  align-items: center;
}
</style>

