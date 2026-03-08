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
  {
    path: '/admin-dashboard',
    name: 'adminDashboard',
    component: () => import('../views/AdminDashboard.vue'),
    meta: { requiresAuth: true, requiredRole: 'admin' } // Admin Only
  }
]


const router = createRouter({
  history: createWebHistory(),
  routes
})


// --- 3. THE BOUNCER (Navigation Guard) ---
// This runs every single time the URL changes, before the new page loads
router.beforeEach((to, from) => {
  const authStore = useAuthStore() // look inside the vault

  // Check 1: are they logged in at all ?
  if (to.meta.requiresAuth && !authStore.token) {
    alert("Hold up! You must be logged in to view this page.")
    return '/'  // Kick them back to the Login page
  }
  
  // Check 2: are they the right kind of User ?
  if (to.meta.requiredRole && authStore.role != to.meta.requiredRole) {
    alert(`Access Denied! You are a ${authStore.role}, not a ${to.meta.requiredRole}.`)

    // Send them back to their own dashboard
    if (authStore.role == 'doctor') return '/doctor-dashboard'
    if (authStore.role == 'admin') return '/admin-dashboard'
    return '/'
  }

  // Check 3: check if they pass both the check, open the door.
  return true
})




export default router