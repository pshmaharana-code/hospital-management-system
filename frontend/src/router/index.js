import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// This map points the root URL ('/') to our soon-to-be Login page
const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/LandingPage.vue')
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/Register.vue')
  },
  {
    path: '/patient-dashboard',
    name: 'PatientDashboard',
    component: () => import('../views/PatientDashboard.vue'),
    meta: { requiresAuth: true, requiredRole: 'patient'}  // Patient only
  },
  {
    path: '/patient-profile',
    name: 'patientProfile',
    component: () => import('../views/PatientProfile.vue'),
    meta: { requiresAuth: true, requiredRole: 'patient' }
  },
  {
    path: '/book-appointment',
    name: 'bookAppointment',
    component: () => import('../views/BookAppointment.vue'),
    meta: { requiresAuth: true, requiredRole: 'patient' } // Patient only
  },
  {
    path: '/patient-history',
    name: 'patientHistory',
    component: () => import('../views/PatientHistory.vue'),
    meta: { requiresAuth: true, requiredRole: 'patient' }
  },
  {
    path: '/doctor-dashboard',
    name: 'doctorDashboard',
    component: () => import('../views/DoctorDashboard.vue'),
    meta: { requiresAuth: true, requiredRole: 'doctor' } // Doctor Only
  },
  // --- NEW: DOCTOR PROFILE ROUTE ---
  {
    path: '/doctor-profile',
    name: 'doctorProfile',
    component: () => import('../views/DoctorProfile.vue'),
    meta: { requiresAuth: true, requiredRole: 'doctor' } // Doctor Only
  },
  {
    path: '/admin-dashboard',
    name: 'adminDashboard',
    component: () => import('../views/AdminDashboard.vue'),
    meta: { requiresAuth: true, requiredRole: 'admin' } // Admin Only
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// --- 3. THE BOUNCER (Navigation Guard) ---
router.beforeEach((to, from) => {
  const authStore = useAuthStore()

  // Check 1: Are they logged in at all?
  if (to.meta.requiresAuth && !authStore.token) {
    alert("Hold up! You must be logged in to view this page.")
    return '/login'  // <-- Send to login
  }
  
  // Check 2: Are they the right kind of User?
  if (to.meta.requiredRole && authStore.role !== to.meta.requiredRole) {
    alert(`Access Denied! You are a ${authStore.role}, not a ${to.meta.requiredRole}.`)

    // <-- Send everyone back to their proper home
    if (authStore.role === 'admin') return '/admin-dashboard'
    if (authStore.role === 'doctor') return '/doctor-dashboard'
    if (authStore.role === 'patient') return '/patient-dashboard'
    
    return '/login' // Failsafe
  }

  // Pass all checks, open the door
  return true
})

export default router