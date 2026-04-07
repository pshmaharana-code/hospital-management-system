<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// --- NAVIGATION STATE ---
const activeTab = ref('personal') // 'personal' or 'family'

// --- PERSONAL PROFILE STATE ---
const profile = ref({ name: '', contact: '', username: '', age: null, gender: '', blood_group: '', address: '' })
const isProfileLoading = ref(true)
const updateMessage = ref('')

// --- FAMILY MEMBER STATE ---
const familyMembers = ref([])
const isFamilyLoading = ref(true)
const showAddModal = ref(false)
const isSubmitting = ref(false)
const newMember = ref({ name: '', relation: '', gender: '', date_of_birth: '' })
const modalError = ref('')
const modalSuccess = ref('')

// ==========================================
// FETCH DATA FUNCTIONS
// ==========================================
const fetchProfile = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/patient/profile', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        profile.value = response.data
    } catch (error) {
        console.error("Failed to load personal profile:", error)
    } finally {
        isProfileLoading.value = false
    }
}

const fetchFamilyMembers = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/patient/family', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        familyMembers.value = response.data
    } catch (error) {
        console.error("Failed to fetch family members:", error)
    } finally {
        isFamilyLoading.value = false
    }
}

// ==========================================
// ACTION FUNCTIONS
// ==========================================
const updateProfile = async () => {
    updateMessage.value = "Saving..."
    try {
        await axios.put('http://127.0.0.1:5000/api/patient/profile', profile.value, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        if (authStore.user) {
            authStore.user.username = profile.value.username
        }
        updateMessage.value = "Profile updated successfully."
        setTimeout(() => updateMessage.value = '', 3000)
    } catch (error) {
        updateMessage.value = "Failed to update profile. Username might be taken."
    }
}

const handleAddMember = async () => {
    isSubmitting.value = true
    modalError.value = ''; modalSuccess.value = ''
    try {
        const response = await axios.post('http://127.0.0.1:5000/api/patient/family', newMember.value, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        })
        modalSuccess.value = response.data.msg
        await fetchFamilyMembers() 
        setTimeout(() => {
            showAddModal.value = false
            newMember.value = { name: '', relation: '', gender: '', date_of_birth: '' }
            modalSuccess.value = ''
        }, 1500)
    } catch (error) {
        modalError.value = error.response?.data?.msg || "Failed to add family member."
    } finally {
        isSubmitting.value = false
    }
}

onMounted(() => {
    // Load both datasets simultaneously when the page loads
    fetchProfile()
    fetchFamilyMembers()
})
</script>

<template>
  <div class="profile-container">
    
    <div class="header-section">
      <h2>Account Settings</h2>
      <router-link to="/patient-dashboard" class="back-link">&larr; Back to Dashboard</router-link>
    </div>

    <div class="layout-wrapper">
      
      <aside class="sidebar">
        <button :class="{ active: activeTab === 'personal' }" @click="activeTab = 'personal'">
          My Profile
        </button>
        <button :class="{ active: activeTab === 'family' }" @click="activeTab = 'family'">
          Manage Family Members
        </button>
      </aside>

      <main class="content-area">

        <div v-if="activeTab === 'personal'">
            <div v-if="isProfileLoading" class="loading-state">Loading personal profile...</div>
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
                      <option value="A+">A+</option><option value="A-">A-</option>
                      <option value="B+">B+</option><option value="B-">B-</option>
                      <option value="O+">O+</option><option value="O-">O-</option>
                      <option value="AB+">AB+</option><option value="AB-">AB-</option>
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

        <div v-if="activeTab === 'family'">
            <div class="section-header">
                <h3>Family Members</h3>
                <button @click="showAddModal = true" class="btn-add">+ Add New Member</button>
            </div>

            <div v-if="isFamilyLoading" class="loading-state">Loading family profiles...</div>
            
            <div v-else-if="familyMembers.length === 0" class="empty-state">
                <p>No family members added yet. Add a family member to easily book appointments for them.</p>
            </div>

            <div v-else class="family-grid">
                <div v-for="member in familyMembers" :key="member.id" class="member-card">
                    <div class="member-avatar">{{ member.name.charAt(0).toUpperCase() }}</div>
                    <div class="member-info">
                        <h4>{{ member.name }}</h4>
                        <p class="relation-badge">{{ member.relation }}</p>
                        <p class="details">{{ member.gender }} • Born: {{ member.date_of_birth }}</p>
                    </div>
                </div>
            </div>
        </div>

      </main>
    </div>

    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
        <div class="modal-content">
            <button class="close-btn" @click="showAddModal = false">&times;</button>
            <h3>Add New Family Member</h3>
            <p class="modal-subtitle">Register a family member to book appointments on their behalf.</p>
            
            <div v-if="modalSuccess" class="success-msg">{{ modalSuccess }}</div>
            <div v-if="modalError" class="error-msg">{{ modalError }}</div>

            <form @submit.prevent="handleAddMember" class="modal-form">
                <div class="form-group">
                    <label>Full Name</label>
                    <input type="text" v-model="newMember.name" required placeholder="e.g. Jane Doe">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Relation</label>
                        <select v-model="newMember.relation" required>
                            <option value="" disabled>Select relation...</option>
                            <option value="Spouse">Spouse</option>
                            <option value="Child">Child</option>
                            <option value="Parent">Parent</option>
                            <option value="Sibling">Sibling</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Gender</label>
                        <select v-model="newMember.gender" required>
                            <option value="" disabled>Select gender...</option>
                            <option value="Male">Male</option>
                            <option value="Female">Female</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>Date of Birth</label>
                    <input type="date" v-model="newMember.date_of_birth" required>
                </div>
                <button type="submit" class="btn-primary" :disabled="isSubmitting">
                    {{ isSubmitting ? 'Adding...' : 'Save Family Member' }}
                </button>
            </form>
        </div>
    </div>

  </div>
</template>

<style scoped>
/* Core Layout */
.profile-container { max-width: 1000px; margin: 2rem auto; padding: 1rem; font-family: Arial, sans-serif;}
.header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 2px solid #eee; padding-bottom: 1rem; }
.header-section h2 { margin: 0; color: #2c3e50; }
.back-link { color: #3498db; text-decoration: none; font-weight: bold; }
.back-link:hover { text-decoration: underline; }

/* Split Layout (Sidebar + Main Content) */
.layout-wrapper { display: flex; gap: 2rem; align-items: flex-start; }
.sidebar { width: 250px; display: flex; flex-direction: column; gap: 0.5rem; background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
.sidebar button { padding: 1rem; text-align: left; background: none; border: none; border-radius: 6px; font-size: 1rem; font-weight: bold; color: #7f8c8d; cursor: pointer; transition: 0.2s; }
.sidebar button:hover { background: #f8f9fa; color: #2c3e50; }
.sidebar button.active { background: #e8f4f8; color: #3498db; border-left: 4px solid #3498db; }
.content-area { flex: 1; }

/* Personal Profile Form Styles */
.profile-card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee;}
.form-section { margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid #eee; }
.form-section h3 { margin-top: 0; color: #2c3e50; margin-bottom: 1rem; }
.input-group { margin-bottom: 1rem; display: flex; flex-direction: column; }
.row { display: flex; gap: 1rem; }
.half-width { flex: 1; }
label { font-weight: bold; margin-bottom: 0.5rem; color: #34495e; font-size: 0.9rem; }
input, select, textarea { padding: 0.75rem; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; }
input:focus, select:focus, textarea:focus { outline: none; border-color: #3498db; }
.form-actions { display: flex; align-items: center; gap: 1rem; }
.btn-save { background-color: #2ecc71; color: white; padding: 0.75rem 2rem; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 1rem; }
.btn-save:hover { background-color: #27ae60; }
.message { font-weight: bold; font-size: 0.9rem; }
.message.success { color: #2ecc71; }
.message.error { color: #e74c3c; }

/* Family Members Styles */
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #eee; }
.section-header h3 { color: #34495e; margin: 0; }
.btn-add { background: #1abc9c; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; font-weight: bold; cursor: pointer; }
.family-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
.member-card { display: flex; align-items: center; background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #eee; }
.member-avatar { width: 50px; height: 50px; border-radius: 50%; background: #3498db; color: white; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: bold; margin-right: 1.2rem; }
.member-info h4 { margin: 0 0 0.3rem 0; color: #2c3e50; }
.relation-badge { display: inline-block; background: #e8f4f8; color: #2980b9; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; font-weight: bold; margin: 0 0 0.5rem 0; }
.details { margin: 0; color: #7f8c8d; font-size: 0.85rem; }
.empty-state { background: white; padding: 3rem; text-align: center; border-radius: 8px; color: #7f8c8d; border: 1px dashed #ccc; }
.loading-state { text-align: center; padding: 3rem; color: #7f8c8d; font-style: italic; }

/* Modal Styles */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: white; padding: 2.5rem; border-radius: 12px; width: 100%; max-width: 450px; position: relative; }
.close-btn { position: absolute; top: 1rem; right: 1.5rem; background: none; border: none; font-size: 1.5rem; color: #95a5a6; cursor: pointer; }
.modal-form { display: flex; flex-direction: column; gap: 1rem; }
.btn-primary { margin-top: 1rem; background: #2c3e50; color: white; border: none; padding: 1rem; border-radius: 6px; font-weight: bold; cursor: pointer; }
.error-msg { background: #fdedec; color: #e74c3c; padding: 0.8rem; border-radius: 6px; margin-bottom: 1rem; }
.success-msg { background: #e8f8f5; color: #27ae60; padding: 0.8rem; border-radius: 6px; margin-bottom: 1rem; }
</style> 