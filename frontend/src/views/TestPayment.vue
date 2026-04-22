<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isProcessing = ref(false)
const paymentStatus = ref('')

const triggerPayment = async () => {
    isProcessing.value = true
    paymentStatus.value = "Creating Order on Server..."

    try {
        // STEP 1: Ask Flask to create a Razorpay Order
        const orderResponse = await axios.post('http://127.0.0.1:5000/api/payments/create-order', 
            { amount: 500 }, // Testing with ₹500
            { headers: { Authorization: `Bearer ${authStore.token}` } }
        )

        const { order_id, amount, key_id } = orderResponse.data

        // STEP 2: Configure the Razorpay Checkout Popup
        const options = {
            key: key_id, 
            amount: amount, 
            currency: "INR",
            name: "Hospital Management System",
            description: "Appointment Booking Fee",
            order_id: order_id,
            
            // STEP 3: What happens when payment is successful?
            handler: function (response) {
                console.log("Payment Success Data:", response)
                paymentStatus.value = `Payment Successful! ID: ${response.razorpay_payment_id}`
                // Next step will be sending this to Flask for verification!
            },
            prefill: {
                name: authStore.user?.username || "Patient",
            },
            theme: { color: "#3498db" }
        }

        // STEP 4: Open the Popup!
        paymentStatus.value = "Awaiting Payment..."
        const rzp = new window.Razorpay(options)
        
        // Handle user closing the popup
        rzp.on('payment.failed', function (response){
            paymentStatus.value = "Payment Failed or Cancelled."
        })
        
        rzp.open()

    } catch (error) {
        console.error(error)
        paymentStatus.value = "Failed to initiate payment gateway."
    } finally {
        isProcessing.value = false
    }
}
</script>

<template>
    <div style="padding: 2rem; text-align: center;">
        <h2>Checkout Simulation</h2>
        <p>Test the Razorpay Handshake</p>
        
        <button @click="triggerPayment" :disabled="isProcessing" style="padding: 1rem 2rem; background: #2c3e50; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 1.1rem; margin-top: 1rem;">
            {{ isProcessing ? 'Connecting to Razorpay...' : 'Pay ₹500 Now' }}
        </button>

        <p v-if="paymentStatus" style="margin-top: 2rem; font-weight: bold; color: #e74c3c;">
            Status: {{ paymentStatus }}
        </p>
    </div>
</template>