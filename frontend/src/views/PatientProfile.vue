<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// State to hold the profile data
const profile = ref({
  name: '',
  contact: '',
  username: '',
  age: null,
  gender: '',
  blood_group: '',
  address: ''
})

const isLoading = ref(true)
const updateMessage = ref('')

// Fetch the exisiting profile data when the page loads.
const fetchProfile = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/patient/profile', {
            headers: {Authorization: `Bearer ${authStore.token}`}
        })
        profile.value = response.data
    } catch (error) {
        console.error("Failed to load profile:", error)
        alert("Could not load profile data.")
    } finally {
        isLoading.value = false
    }
}

// Send the updated data back to the server.
const updateProfile = async () => {
    updateMessage.value = "Saving..."
    try {
        await axios.put('http://127.0.0.1:5000/api/patient/profile', profile.value, {
            headers: {Authorization: `Bearer ${authStore.token}`}
        })
        // update the username in vue auth store incase they change it.
        if (authStore.user) {
            authStore.user.username = profile.value.username
        }

        updateMessage.value = "Profile updated successfully."
        setTimeout(() => updateMessage.value = '', 3000)
    } catch (error) {
        console.error("Failed to update profile:", error)
        updateMessage.value = "Failed to update profile. Username might be taken."
    }
}

onMounted(() => {
    fetchProfile()
})
</script>


<template>
  <div class="profile-container">
    <div class="header-section">
      <h2>Profile Settings</h2>
      <router-link to="/patient-dashboard" class="back-link">&larr; Back to Dashboard</router-link>
    </div>

    <div v-if="isLoading" class="loading-state">Loading profile...</div>

    <div v-else class="profile-card">
      <form @submit.prevent="updateProfile" class="profile-form">
        
        <div class="form-section">
          <h3>Account Information</h3>
          <div class="input-group">
            <label>Full Name</label>
            <input type="text" v-model="profile.name" required />
          </div>
          <div class="input-group">
            <label>Username (Login ID)</label>
            <input type="text" v-model="profile.username" required />
          </div>
          <div class="input-group">
            <label>Contact Number</label>
            <input type="text" v-model="profile.contact" required />
          </div>
        </div>

        <div class="form-section">
          <h3>Medical Profile</h3>
          <div class="row">
            <div class="input-group half-width">
              <label>Age</label>
              <input type="number" v-model="profile.age" placeholder="e.g. 28" />
            </div>
            <div class="input-group half-width">
              <label>Gender</label>
              <select v-model="profile.gender">
                <option value="">Select Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
          
          <div class="input-group">
            <label>Blood Group</label>
            <select v-model="profile.blood_group">
              <option value="">Select Blood Group</option>
              <option value="A+">A+</option>
              <option value="A-">A-</option>
              <option value="B+">B+</option>
              <option value="B-">B-</option>
              <option value="O+">O+</option>
              <option value="O-">O-</option>
              <option value="AB+">AB+</option>
              <option value="AB-">AB-</option>
            </select>
          </div>
          
          <div class="input-group">
            <label>Address</label>
            <textarea v-model="profile.address" rows="3" placeholder="Enter full address"></textarea>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-save">Save Changes</button>
          <span v-if="updateMessage" :class="['message', updateMessage.includes('success') ? 'success' : 'error']">
            {{ updateMessage }}
          </span>
        </div>

      </form>
    </div>
  </div>
</template>

<style scoped>
.profile-container { max-width: 800px; margin: 2rem auto; padding: 1rem; }
.header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.back-link { color: #3498db; text-decoration: none; font-weight: bold; }
.back-link:hover { text-decoration: underline; }

.profile-card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.form-section { margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid #eee; }
.form-section h3 { margin-top: 0; color: #2c3e50; margin-bottom: 1rem; }

.input-group { margin-bottom: 1rem; display: flex; flex-direction: column; }
.row { display: flex; gap: 1rem; }
.half-width { flex: 1; }

label { font-weight: bold; margin-bottom: 0.5rem; color: #34495e; font-size: 0.9rem; }
input, select, textarea { padding: 0.75rem; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; }
input:focus, select:focus, textarea:focus { outline: none; border-color: #3498db; box-shadow: 0 0 0 2px rgba(52,152,219,0.2); }

.form-actions { display: flex; align-items: center; gap: 1rem; }
.btn-save { background-color: #2ecc71; color: white; padding: 0.75rem 2rem; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; transition: background 0.2s; font-size: 1rem; }
.btn-save:hover { background-color: #27ae60; }

.message { font-weight: bold; font-size: 0.9rem; }
.message.success { color: #2ecc71; }
.message.error { color: #e74c3c; }
.loading-state { text-align: center; padding: 3rem; color: #7f8c8d; font-style: italic; }
</style>