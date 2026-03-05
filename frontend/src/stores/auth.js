import { defineStore } from "pinia";
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () =>{
    // STATE (The Vault's Content)\
    // When the app starts , check if the token is already exist in the browser's hard drive.
    const token = ref(localStorage.getItem('token') || null)
    const user = ref(JSON.parse(localStorage.getItem('user')) || null)
    const role = ref(localStorage.getItem('role') || null)

    // --- Action (how we change the vault)
    const saveLogin = (newToken, newUser, newRole) => {
        // 1. Save to Pinia
        token.value = newToken
        user.value = newUser
        role.value = newRole

        // 2. Save to local storage.
        localStorage.setItem('token', newToken)
        localStorage.setItem('user', JSON.stringify(newUser))
        localStorage.setItem('role', newRole)
        }

    const logout = () => {
        // 1. Clear the Pinia.
        token.value = null
        user.value = null
        role.value = null

        // 2. clear the local storage.
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('role')
    }

    // we must return these, so that the rest of the app can use them.
    return { token, user, role, saveLogin, logout}
})