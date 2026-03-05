<script setup>
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app-container">
    <header>
      <h1>Hospital Management System</h1>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
header {
  background-color: #2c3e50;
  color: white;
  padding: 1rem;
  text-align: center;
}
</style>