<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await api.login(email.value, password.value)
    router.push('/')
  } catch (e: any) {
    error.value = 'Invalid email or password'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <img src="/studyflash.png" alt="Studyflash" class="logo-icon" />
        <h1>Studyflash Support</h1>
        <p>Sign in to your account</p>
      </div>
      <form @submit.prevent="handleLogin">
        <div class="field">
          <label>Email</label>
          <input type="email" v-model="email" placeholder="you@studyflash.ch" required />
        </div>
        <div class="field">
          <label>Password</label>
          <input type="password" v-model="password" placeholder="Password" required />
        </div>
        <div v-if="error" class="error">
          <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
          {{ error }}
        </div>
        <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
          <svg v-if="loading" class="spinner" width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" stroke-dasharray="28" stroke-dashoffset="8" stroke-linecap="round"/></svg>
          {{ loading ? 'Signing in...' : 'Sign in' }}
        </button>
      </form>
    </div>
    <div class="login-footer">Studyflash Support Portal</div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e1b3a 0%, #2d2755 40%, #3b2d70 70%, #6c5ce7 100%);
  position: relative;
  overflow: hidden;
}

.login-page::before {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(108, 92, 231, 0.15) 0%, transparent 70%);
  top: -200px;
  right: -200px;
}

.login-page::after {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(139, 126, 245, 0.1) 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
}

.login-card {
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 44px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(108, 92, 231, 0.1);
  position: relative;
  z-index: 1;
  animation: fadeIn 0.4s ease;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  object-fit: cover;
  margin-bottom: 20px;
}

.login-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: #1e1b3a;
  margin-bottom: 6px;
}

.login-header p {
  font-size: 14px;
  color: #8b8a9e;
}

.field {
  margin-bottom: 18px;
}

.field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #4a4568;
  margin-bottom: 6px;
}

.field input {
  width: 100%;
  padding: 12px 14px;
  border: 1.5px solid #e2e0f0;
  border-radius: 10px;
  font-size: 14px;
  box-sizing: border-box;
  transition: all 0.2s ease;
  background: #faf9ff;
  color: #1e1b3a;
}

.field input::placeholder {
  color: #b0adc4;
}

.field input:focus {
  outline: none;
  border-color: #6c5ce7;
  box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.12);
  background: #fff;
}

.error {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #dc2626;
  font-size: 13px;
  margin-bottom: 16px;
  padding: 10px 14px;
  background: #fef2f2;
  border-radius: 10px;
  border: 1px solid #fecaca;
  font-weight: 500;
}

.login-btn {
  width: 100%;
  padding: 12px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px;
}

.spinner {
  animation: spin 0.8s linear infinite;
}

.login-footer {
  position: relative;
  z-index: 1;
  margin-top: 32px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
  font-weight: 500;
}
</style>
