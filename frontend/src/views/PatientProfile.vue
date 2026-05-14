<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import ImageCropperModal from '@/components/ImageCropperModal.vue'

const authStore = useAuthStore()

const activeTab = ref('personal')

// --- PERSONAL PROFILE STATE ---
const profile = ref({ 
    name: '', contact: '', username: '', age: null,
    address: '', profile_picture: null, gender: '', blood_group: ''
})
const isProfileLoading = ref(true)
const updateMessage = ref('')
const isSuccess = ref(true)

// --- MEDIA UPLOAD STATE ---
const fileInput = ref(null)
const isUploading = ref(false)
const uploadError = ref('')
const showCropModal = ref(false)
const imageTimestamp = ref(Date.now())
const imageSource = ref(null)

// --- FAMILY MEMBER STATE ---
const familyMembers = ref([])
const isFamilyLoading = ref(true)
const showAddModal = ref(false)
const isSubmitting = ref(false)
const newMember = ref({ name: '', relation: '', gender: '', date_of_birth: '' })
const modalError = ref('')
const modalSuccess = ref('')

// --- API METHODS ---
const fetchProfile = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/patient/profile', { 
            headers: { Authorization: `Bearer ${authStore.token}` } 
        })
        profile.value = response.data
    } catch (error) {
        console.error(error)
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
        console.error(error)
    } finally { 
        isFamilyLoading.value = false 
    }
}

const updateProfile = async () => {
    updateMessage.value = "Saving..."
    isSuccess.value = true
    try {
        await axios.put('http://127.0.0.1:5000/api/patient/profile', profile.value, { 
            headers: { Authorization: `Bearer ${authStore.token}` } 
        })
        
        // Update global store so the username changes everywhere
        if (authStore.user) authStore.user.username = profile.value.username
        
        updateMessage.value = "Profile updated successfully."
        setTimeout(() => updateMessage.value = '', 3000)
    } catch (error) {
        isSuccess.value = false
        updateMessage.value = "Failed to update profile. Username might be taken."
    }
}

// --- GLOBAL CROPPER LOGIC ---
const triggerFileInput = () => { fileInput.value.click() }

const onFileSelect = (event) => {
    const file = event.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (e) => {
        imageSource.value = e.target.result 
        showCropModal.value = true
    }
    reader.readAsDataURL(file)
    event.target.value = '' // reset input
}

const handleCroppedImage = async (blob) => {
    isUploading.value = true
    uploadError.value = ''
    const formData = new FormData()
    formData.append('file', blob, 'profile_pic.jpg')
    
    try {
        const response = await axios.post('http://127.0.0.1:5000/api/patient/profile/picture', formData, {
            headers: { 
                Authorization: `Bearer ${authStore.token}`,
                'Content-Type': 'multipart/form-data' 
            }
        })
        
        // 1. Update Local Component State
        profile.value.profile_picture = response.data.picture_url
        
        // 2. CRITICAL: Update Global Pinia Store so Top-Nav updates instantly!
        if(authStore.user) {
            authStore.user.profile_picture = response.data.picture_url
        }
        
        // 3. Force image refresh
        imageTimestamp.value = Date.now()
        showCropModal.value = false
        
        updateMessage.value = "Profile picture updated globally!"
        setTimeout(() => updateMessage.value = '', 3000)
    } catch (error) {
        uploadError.value = error.response?.data?.msg || "Failed to upload picture."
    } finally {
        isUploading.value = false
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
            showAddModal.value = false; 
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
    fetchProfile()
    fetchFamilyMembers() 
})
</script>

<template>
    <div class="clean-layout">
        
        <aside class="side-nav">
            <div class="brand-header" @click="$router.push('/')">
                <div class="logo-mark">+</div>
                <span class="logo-text">ApexMedical</span>
            </div>

            <nav class="nav-links">
                <button :class="['nav-btn', { active: activeTab === 'personal' }]" @click="activeTab = 'personal'">
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"></circle><path d="M18 8h1a4 4 0 0 1 0 8h-1"></path><path d="M6 8H5a4 4 0 0 0 0 8h1"></path><line x1="6" y1="2" x2="6" y2="22"></line><line x1="18" y1="2" x2="18" y2="22"></line></svg>
                    My Profile
                </button>
                <button :class="['nav-btn', { active: activeTab === 'family' }]" @click="activeTab = 'family'">
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                    Family Members
                </button>
                
                <div class="nav-divider"></div>
                <router-link to="/patient-dashboard" class="nav-btn btn-back">
                    &larr; Back to Dashboard
                </router-link>
            </nav>
        </aside>

        <main class="workspace">
            <header class="page-header">
                <h1>Account Settings</h1>
                <p>Manage your personal information and family network.</p>
            </header>

            <div class="content-area">
                
                <div v-if="activeTab === 'personal'" class="fade-in">
                    <div v-if="isProfileLoading" class="loading-state">
                        <div class="spinner"></div><p>Loading profile...</p>
                    </div>
                    
                    <div v-else class="settings-card">
                        
                        <div class="avatar-section">
                            <div class="avatar-wrapper">
                                <img v-if="profile.profile_picture" 
                                     :src="`http://127.0.0.1:5000${profile.profile_picture}?t=${imageTimestamp}`" 
                                     alt="Profile" class="profile-img">
                                <div v-else class="avatar-placeholder">
                                    {{ profile.name ? profile.name.charAt(0).toUpperCase() : '?' }}
                                </div>
                            </div>
                            
                            <div class="avatar-actions">
                                <h3>Profile Picture</h3>
                                <p>Upload a high-res picture. PNG or JPG.</p>
                                <input type="file" ref="fileInput" @change="onFileSelect" accept="image/png, image/jpeg, image/webp" style="display: none;">
                                <button type="button" class="btn-outline" @click="triggerFileInput" :disabled="isUploading">
                                    {{ isUploading ? 'Uploading...' : 'Change Picture' }}
                                </button>
                                <span v-if="uploadError" class="text-error mt-1">{{ uploadError }}</span>
                            </div>
                        </div>

                        <hr class="divider">

                        <form @submit.prevent="updateProfile" class="profile-form">
                            
                            <div class="form-section">
                                <h3 class="section-title">Account Information</h3>
                                <div class="form-grid">
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
                                    <div class="input-group">
                                        <label>Email Address</label>
                                        <input type="email" value="account@example.com" disabled />
                                        <small>Email cannot be changed.</small>
                                    </div>
                                </div>
                            </div>

                            <div class="form-section mt-3">
                                <h3 class="section-title">Medical Profile</h3>
                                <div class="form-grid">
                                    <div class="input-group">
                                        <label>Age</label>
                                        <input type="number" v-model="profile.age" />
                                    </div>
                                    <div class="input-group">
                                        <label>Gender</label>
                                        <select v-model="profile.gender">
                                            <option value="">Select Gender</option>
                                            <option value="Male">Male</option>
                                            <option value="Female">Female</option>
                                            <option value="Other">Other</option>
                                        </select>
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
                                    <div class="input-group full-width">
                                        <label>Address</label>
                                        <textarea v-model="profile.address" rows="3"></textarea>
                                    </div>
                                </div>
                            </div>

                            <div class="form-actions">
                                <button type="submit" class="btn-primary">Save Changes</button>
                                <span v-if="updateMessage" :class="['alert-msg', isSuccess ? 'alert-success' : 'alert-error']">
                                    {{ updateMessage }}
                                </span>
                            </div>
                        </form>
                    </div>
                </div>

                <div v-if="activeTab === 'family'" class="fade-in">
                    <div class="family-header">
                        <div>
                            <h3 class="section-title">Family Network</h3>
                            <p class="sub-text">Manage dependents and connected family members.</p>
                        </div>
                        <button @click="showAddModal=true" class="btn-primary">+ Add Member</button>
                    </div>

                    <div v-if="isFamilyLoading" class="loading-state">
                        <div class="spinner"></div><p>Loading family profiles...</p>
                    </div>
                    
                    <div v-else-if="familyMembers.length === 0" class="empty-state settings-card">
                        <p>No family members added yet.</p>
                    </div>
                    
                    <div v-else class="family-grid">
                        <div v-for="member in familyMembers" :key="member.id" class="member-card">
                            <div class="member-avatar">{{ member.name.charAt(0).toUpperCase() }}</div>
                            <div class="member-info">
                                <h4>{{ member.name }}</h4>
                                <span class="relation-badge">{{ member.relation }}</span>
                                <p class="details">{{ member.gender }} &bull; Born: {{ member.date_of_birth }}</p>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </main>
        
        <ImageCropperModal
            :show="showCropModal"
            :imageSource="imageSource"
            :isUploading="isUploading"
            @close="showCropModal = false"
            @crop="handleCroppedImage"
        />

        <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
            <div class="modal-card fade-in">
                <button class="close-btn" @click="showAddModal = false">&times;</button>
                <h3>Add Family Member</h3>
                <p class="sub-text mb-2">Register a new dependent to your network.</p>
                
                <div v-if="modalSuccess" class="alert-msg alert-success mb-1">{{ modalSuccess }}</div>
                <div v-if="modalError" class="alert-msg alert-error mb-1">{{ modalError }}</div>

                <form @submit.prevent="handleAddMember" class="modal-form">
                    <div class="input-group">
                        <label>Full Name</label>
                        <input type="text" v-model="newMember.name" required> 
                    </div>
                    
                    <div class="form-row">
                        <div class="input-group">
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
                        <div class="input-group">
                            <label>Gender</label>
                            <select v-model="newMember.gender" required> 
                                <option value="" disabled>Select gender...</option>
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="input-group">
                        <label>Date of Birth</label>
                        <input type="date" v-model="newMember.date_of_birth" required> 
                    </div>
                    
                    <button type="submit" class="btn-primary w-100 mt-2" :disabled="isSubmitting">
                        {{ isSubmitting ? 'Adding...' : 'Save Family Member' }}
                    </button>
                </form>
            </div>
        </div>

    </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* --- BASE & LAYOUT --- */
.clean-layout { font-family: 'Plus Jakarta Sans', sans-serif; display: flex; height: 100vh; background-color: #ffffff; color: #1e293b; overflow: hidden; }

/* SIDE NAV */
.side-nav { width: 250px; background: #ffffff; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; padding: 1.5rem 1.2rem; z-index: 20; }
.brand-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 2.5rem; cursor: pointer; }
.logo-mark { background: #0f766e; color: white; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 8px; font-weight: 800; }
.logo-text { font-size: 1.15rem; font-weight: 800; color: #0f172a; }

.nav-links { display: flex; flex-direction: column; gap: 0.4rem; flex: 1; }
.nav-btn { display: flex; align-items: center; gap: 0.8rem; padding: 0.8rem 1rem; border-radius: 10px; border: none; background: transparent; color: #64748b; font-weight: 600; font-size: 0.9rem; cursor: pointer; text-decoration: none; transition: all 0.2s; text-align: left; }
.nav-btn:hover { background: #f8fafc; color: #0f766e; }
.nav-btn.active { background: #f0fdfa; color: #0f766e; }
.nav-icon { width: 18px; height: 18px; }
.nav-divider { height: 1px; background: #e2e8f0; margin: 1rem 0; }
.btn-back { color: #0f766e; }

/* WORKSPACE */
.workspace { flex: 1; display: flex; flex-direction: column; overflow: hidden; background-color: #f1f5f9; }
.page-header { padding: 2.5rem 3rem 1rem; }
.page-header h1 { font-size: 1.8rem; font-weight: 800; color: #1e293b; margin: 0 0 0.4rem 0; letter-spacing: -0.5px; }
.page-header p { color: #64748b; margin: 0; font-size: 0.95rem; }
.content-area { padding: 0 3rem 3rem; overflow-y: auto; flex: 1; }

/* --- CARDS & SECTIONS --- */
.settings-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 2.5rem; box-shadow: 0 4px 14px rgba(0,0,0,0.03); max-width: 900px; }
.section-title { font-size: 1.1rem; font-weight: 700; color: #1e293b; margin: 0 0 1.2rem 0; }
.sub-text { color: #64748b; font-size: 0.9rem; margin: 0; }
.divider { border: 0; height: 1px; background: #e2e8f0; margin: 2rem 0; }
.mt-3 { margin-top: 2.5rem; }

/* --- AVATAR SECTION --- */
.avatar-section { display: flex; align-items: center; gap: 2rem; }
.avatar-wrapper { width: 100px; height: 100px; border-radius: 50%; overflow: hidden; border: 4px solid #f0fdfa; box-shadow: 0 4px 15px rgba(15, 118, 110, 0.1); display: flex; align-items: center; justify-content: center; background: #f8fafc; flex-shrink: 0; }
.profile-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder { font-size: 2.5rem; font-weight: 800; color: #0f766e; }
.avatar-actions h3 { margin: 0 0 0.3rem 0; font-size: 1rem; color: #1e293b; }
.avatar-actions p { margin: 0 0 1rem 0; font-size: 0.85rem; color: #64748b; }

/* --- FORMS --- */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.input-group { display: flex; flex-direction: column; gap: 0.4rem; }
.full-width { grid-column: span 2; }
.input-group label { font-size: 0.85rem; font-weight: 600; color: #475569; }
.input-group input, .input-group select, .input-group textarea { padding: 0.8rem 1rem; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 0.95rem; color: #1e293b; transition: all 0.2s; background: #ffffff; }
.input-group input:focus, .input-group select:focus, .input-group textarea:focus { outline: none; border-color: #0f766e; box-shadow: 0 0 0 3px #ccfbf1; }
.input-group input:disabled { background: #f1f5f9; color: #94a3b8; cursor: not-allowed; }
.input-group small { color: #94a3b8; font-size: 0.75rem; }

/* --- BUTTONS & ALERTS --- */
.form-actions { display: flex; align-items: center; gap: 1.5rem; margin-top: 2rem; padding-top: 2rem; border-top: 1px solid #e2e8f0; }
.btn-primary { background: #0f766e; color: white; border: none; border-radius: 10px; font-weight: 700; font-size: 0.95rem; padding: 0.8rem 1.5rem; cursor: pointer; transition: 0.2s; font-family: inherit; box-shadow: 0 4px 15px rgba(15, 118, 110, 0.2); }
.btn-primary:hover:not(:disabled) { background: #115e59; transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.7; cursor: not-allowed; }
.btn-outline { background: transparent; border: 1px solid #cbd5e1; color: #475569; padding: 0.6rem 1.2rem; border-radius: 8px; font-weight: 600; font-size: 0.85rem; cursor: pointer; transition: 0.2s; }
.btn-outline:hover:not(:disabled) { border-color: #0f766e; color: #0f766e; }

.alert-msg { padding: 0.8rem 1.2rem; border-radius: 8px; font-weight: 600; font-size: 0.85rem; }
.alert-success { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.alert-error { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.text-error { color: #ef4444; font-size: 0.8rem; font-weight: 600; display: block; }

/* --- FAMILY SECTION --- */
.family-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; max-width: 900px; }
.family-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; max-width: 900px; }
.member-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.5rem; display: flex; align-items: center; gap: 1.2rem; box-shadow: 0 2px 10px rgba(0,0,0,0.02); }
.member-avatar { width: 50px; height: 50px; background: #f0fdfa; color: #0f766e; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 800; }
.member-info h4 { margin: 0 0 0.3rem 0; color: #1e293b; font-size: 1.05rem; }
.relation-badge { display: inline-block; background: #f1f5f9; color: #475569; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 700; margin-bottom: 0.5rem; }
.details { margin: 0; color: #64748b; font-size: 0.8rem; }

/* --- MODALS & UTILS --- */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { background: white; padding: 2.5rem; border-radius: 20px; width: 100%; max-width: 500px; position: relative; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
.close-btn { position: absolute; top: 1.5rem; right: 1.5rem; background: none; border: none; font-size: 1.8rem; color: #94a3b8; cursor: pointer; transition: 0.2s; line-height: 1; }
.close-btn:hover { color: #1e293b; }
.modal-form { display: flex; flex-direction: column; gap: 1.2rem; margin-top: 1.5rem; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.w-100 { width: 100%; }
.mt-2 { margin-top: 1rem; }
.mb-1 { margin-bottom: 1rem; }
.mb-2 { margin-bottom: 1.5rem; }

.loading-state, .empty-state { text-align: center; padding: 4rem; color: #64748b; }
.spinner { width: 36px; height: 36px; border: 3px solid #e2e8f0; border-top-color: #0f766e; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }
.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>