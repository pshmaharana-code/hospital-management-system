<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// --- IMPORT OUR REUSABLE ENGINE! ---
import ImageCropperModal from '@/components/ImageCropperModal.vue'

const authStore = useAuthStore()

// --- PROFILE STATE ---
const profile = ref({ name: '', contact: '', qualification: '', experience: null, bio: '', profile_picture: null, consultation_fee: 500 })
const isLoading = ref(true)
const updateMessage = ref('')

// --- MEDIA UPLOAD STATE ---
const fileInput = ref(null) 
const isUploading = ref(false)
const uploadError = ref('')
const showCropModal = ref(false)
const imageSource = ref(null)
const imageTimestamp = ref(Date.now()) // The Cache-Buster!

const fetchProfile = async () => {
    try {
        const response = await axios.get('http://127.0.0.1:5000/api/doctor/profile', { 
            headers: { Authorization: `Bearer ${authStore.token}` } 
        })
        profile.value = response.data
    } catch (error) { 
        console.error(error)
    } finally { 
        isLoading.value = false 
    }
}

const updateProfile = async () => {
    updateMessage.value = "Saving..."
    try {
        await axios.put('http://127.0.0.1:5000/api/doctor/profile', profile.value, { 
            headers: { Authorization: `Bearer ${authStore.token}` } 
        })
        updateMessage.value = "Profile updated successfully."
        setTimeout(() => updateMessage.value = '', 3000)
    } catch (error) {
        updateMessage.value = "Failed to update profile."
    }
}

// ==========================================
// THE CROPPER LOGIC
// ==========================================
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
    event.target.value = '' 
}

const handleCroppedImage = async (blob) => {
    isUploading.value = true
    uploadError.value = ''

    const formData = new FormData()
    formData.append('file', blob, 'profile_pic.jpg')

    try {
        const response = await axios.post('http://127.0.0.1:5000/api/doctor/profile/picture', formData, {
            headers: { Authorization: `Bearer ${authStore.token}`, 'Content-Type': 'multipart/form-data' }
        })
        
        // Save URL and bust cache
        profile.value.profile_picture = response.data.picture_url
        imageTimestamp.value = Date.now()
        
        showCropModal.value = false 
        updateMessage.value = "Profile picture updated!"
        setTimeout(() => updateMessage.value = '', 3000)
    } catch (error) {
        uploadError.value = error.response?.data?.msg || "Failed to upload picture."
    } finally {
        isUploading.value = false
    }
}

onMounted(() => { fetchProfile() })
</script>

<template>
  <div class="profile-container">
    
    <div class="header-section">
      <h2>Professional Settings</h2>
      <router-link to="/doctor-dashboard" class="back-link">&larr; Back to Dashboard</router-link>
    </div>

    <div v-if="isLoading" class="loading-state">Loading your professional profile...</div>
    
    <div v-else class="profile-card">
        
        <div class="avatar-section">
            <div class="avatar-wrapper">
                <img v-if="profile.profile_picture" :src="'http://127.0.0.1:5000' + profile.profile_picture + '?t=' + imageTimestamp" alt="Profile" class="profile-img">
                <div v-else class="avatar-placeholder">{{ profile.name ? profile.name.charAt(0).toUpperCase() : 'Dr.' }}</div>
            </div>
            
            <div class="avatar-actions">
                <input type="file" ref="fileInput" @change="onFileSelect" accept="image/png, image/jpeg, image/webp" style="display: none;">
                <button type="button" class="btn-upload" @click="triggerFileInput">Change Picture</button>
            </div>
        </div>
        <hr class="divider">

        <form @submit.prevent="updateProfile" class="profile-form">
            <div class="form-section">
                <h3>Public Directory Details</h3>
                <p class="help-text">This information will be visible to patients when they are booking an appointment.</p>
                
                <div class="row">
                    <div class="input-group half-width">
                        <label>Display Name</label>
                        <input type="text" v-model="profile.name" required />
                    </div>
                    <div class="input-group half-width">
                        <label>Contact Number</label>
                        <input type="text" v-model="profile.contact" />
                    </div>
                </div>

                <div class="row">
                    <div class="input-group half-width">
                        <label>Qualifications (Degrees)</label>
                        <input type="text" v-model="profile.qualification" placeholder="e.g., MBBS, MD" />
                    </div>
                    <div class="input-group half-width">
                        <label>Years of Experience</label>
                        <input type="number" v-model="profile.experience" placeholder="e.g., 10" />
                    </div>
                </div>

                <div class="input-group">
                    <label>Professional Bio</label>
                    <textarea v-model="profile.bio" rows="4" placeholder="Briefly describe your specialties and background..."></textarea>
                </div>

                <hr class="divider" style="margin: 2rem 0;">

                <h3>Consultation Settings</h3>
                <p class="help-text">Set the price patients will be charged via Razorpay when booking your slots.</p>
                <div class="row">
                    <div class="input-group half-width">
                        <label>Consultation Fee (₹)</label>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 1.2rem; font-weight: bold; color: #7f8c8d;">₹</span>
                            <input 
                                type="number" 
                                v-model="profile.consultation_fee" 
                                min="0" 
                                step="50" 
                                required 
                                style="flex: 1;"
                            />
                        </div>
                    </div>
                </div>
            </div>

            <div class="form-actions">
                <button type="submit" class="btn-save">Save Public Profile</button>
                <span v-if="updateMessage" :class="['message', updateMessage.includes('success') ? 'success' : 'error']">
                    {{ updateMessage }}
                </span>
            </div>
        </form>
    </div>

    <ImageCropperModal 
        :show="showCropModal"
        :imageSource="imageSource"
        :isUploading="isUploading"
        @close="showCropModal = false"
        @crop="handleCroppedImage"
    />

  </div>
</template>

<style scoped>
.profile-container { max-width: 800px; margin: 2rem auto; padding: 1rem; font-family: Arial, sans-serif;}
.header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 2px solid #eee; padding-bottom: 1rem; }
.header-section h2 { margin: 0; color: #2c3e50; }
.back-link { color: #3498db; text-decoration: none; font-weight: bold; }

.profile-card { background: white; padding: 2.5rem; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #eee;}

/* AVATAR STYLES */
.avatar-section { display: flex; align-items: center; gap: 2rem; margin-bottom: 1rem; }
.avatar-wrapper { width: 120px; height: 120px; border-radius: 50%; overflow: hidden; background: #fdfdfd; border: 4px solid #2c3e50; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 4px 10px rgba(0,0,0,0.1);}
.profile-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder { font-size: 3rem; font-weight: bold; color: #2c3e50; }
.btn-upload { background: #f8f9fa; border: 1px solid #ccc; padding: 0.6rem 1.2rem; border-radius: 6px; font-weight: bold; color: #2c3e50; cursor: pointer; transition: 0.2s; }
.btn-upload:hover { background: #e2e6ea; border-color: #b1b7ba; }
.divider { border: 0; height: 1px; background: #eee; margin: 2rem 0; }

/* Form Styles */
.form-section h3 { margin-top: 0; color: #2c3e50; margin-bottom: 0.5rem; }
.help-text { color: #7f8c8d; font-size: 0.9rem; margin-bottom: 1.5rem; }
.input-group { margin-bottom: 1.5rem; display: flex; flex-direction: column; }
.row { display: flex; gap: 1.5rem; }
.half-width { flex: 1; }
label { font-weight: bold; margin-bottom: 0.5rem; color: #34495e; font-size: 0.9rem; }
input, textarea { padding: 0.8rem; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; font-family: inherit;}
input:focus, textarea:focus { outline: none; border-color: #3498db; }
.form-actions { display: flex; align-items: center; gap: 1rem; margin-top: 2rem; border-top: 1px solid #eee; padding-top: 1.5rem;}
.btn-save { background-color: #2c3e50; color: white; padding: 0.8rem 2rem; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 1rem; transition: 0.2s;}
.btn-save:hover { background-color: #34495e; }
.message { font-weight: bold; font-size: 0.9rem; }
.message.success { color: #2ecc71; }
.message.error { color: #e74c3c; }
.loading-state { text-align: center; padding: 3rem; color: #7f8c8d; font-style: italic; }
</style>