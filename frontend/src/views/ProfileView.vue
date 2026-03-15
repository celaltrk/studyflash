<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api'
import type { UserProfile } from '../types'

const profile = ref<UserProfile | null>(null)
const loading = ref(true)
const saving = ref(false)
const successMsg = ref('')

const editForm = ref({
  display_name: '',
  department: '',
  phone: '',
  bio: '',
})

async function loadProfile() {
  loading.value = true
  try {
    const p = await api.getMyProfile()
    profile.value = p
    editForm.value = {
      display_name: p.display_name,
      department: p.department || '',
      phone: p.phone || '',
      bio: p.bio || '',
    }
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  if (!profile.value) return
  saving.value = true
  successMsg.value = ''
  try {
    const data: Record<string, any> = {}
    if (editForm.value.display_name !== profile.value.display_name) data.display_name = editForm.value.display_name
    if ((editForm.value.department || null) !== profile.value.department) data.department = editForm.value.department || null
    if ((editForm.value.phone || null) !== profile.value.phone) data.phone = editForm.value.phone || null
    if ((editForm.value.bio || null) !== profile.value.bio) data.bio = editForm.value.bio || null

    if (Object.keys(data).length > 0) {
      profile.value = await api.updateUser(profile.value.id, data)
      // Update local storage user name if changed
      if (data.display_name) {
        const user = api.getUser()
        if (user) {
          user.name = data.display_name
          localStorage.setItem('user', JSON.stringify(user))
        }
      }
    }
    successMsg.value = 'Profile updated successfully'
    setTimeout(() => successMsg.value = '', 3000)
  } catch (e: any) {
    alert('Failed to save: ' + e.message)
  } finally {
    saving.value = false
  }
}

function roleColor(role: string): string {
  const colors: Record<string, string> = {
    admin: '#dc2626',
    support: '#2563eb',
    billing: '#059669',
    engineering: '#d97706',
  }
  return colors[role] || '#6b7280'
}

function initials(name: string): string {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
}

onMounted(loadProfile)
</script>

<template>
  <div class="profile-page">
    <header class="page-header">
      <h1>My Profile</h1>
      <p class="subtitle">View and update your account settings</p>
    </header>

    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <span>Loading profile...</span>
    </div>

    <template v-else-if="profile">
      <div class="profile-layout">
        <!-- Profile card -->
        <div class="profile-card">
          <div class="profile-card-header">
            <div class="avatar-large" :style="{ background: `linear-gradient(135deg, ${roleColor(profile.role)}dd, ${roleColor(profile.role)})` }">
              {{ initials(profile.display_name) }}
            </div>
            <h2>{{ profile.display_name }}</h2>
            <p class="profile-email">{{ profile.email }}</p>
            <span class="role-badge" :style="{ background: roleColor(profile.role) + '12', color: roleColor(profile.role), borderColor: roleColor(profile.role) + '30' }">
              {{ profile.role }}
            </span>
          </div>
          <div class="profile-stats">
            <div class="profile-stat">
              <div class="profile-stat-value">{{ profile.open_ticket_count }}</div>
              <div class="profile-stat-label">Open Tickets</div>
            </div>
            <div class="profile-stat">
              <div class="profile-stat-value">{{ profile.max_open_tickets }}</div>
              <div class="profile-stat-label">Max Capacity</div>
            </div>
          </div>
          <div v-if="profile.department" class="profile-detail">
            <span class="detail-label">
              <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4z" clip-rule="evenodd"/></svg>
              Department
            </span>
            <span class="detail-value">{{ profile.department }}</span>
          </div>
          <div v-if="profile.phone" class="profile-detail">
            <span class="detail-label">
              <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z"/></svg>
              Phone
            </span>
            <span class="detail-value">{{ profile.phone }}</span>
          </div>
        </div>

        <!-- Edit form -->
        <div class="edit-card">
          <h2>Edit Profile</h2>
          <div v-if="successMsg" class="success-msg">
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
            {{ successMsg }}
          </div>
          <form @submit.prevent="saveProfile">
            <div class="form-group">
              <label>Display Name</label>
              <input v-model="editForm.display_name" required />
            </div>
            <div class="form-group">
              <label>Department</label>
              <input v-model="editForm.department" placeholder="e.g. Customer Support" />
            </div>
            <div class="form-group">
              <label>Phone</label>
              <input v-model="editForm.phone" placeholder="e.g. +41 79 123 4567" />
            </div>
            <div class="form-group">
              <label>Bio</label>
              <textarea v-model="editForm.bio" rows="3" placeholder="Tell your team a bit about yourself..."></textarea>
            </div>
            <div class="form-group readonly-info">
              <label>Role</label>
              <p>{{ profile.role }} <span class="hint">(Contact an admin to change your role)</span></p>
            </div>
            <button type="submit" class="btn btn-primary save-btn" :disabled="saving">
              <svg v-if="saving" class="spinner" width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" stroke-dasharray="28" stroke-dashoffset="8" stroke-linecap="round"/></svg>
              {{ saving ? 'Saving...' : 'Save Changes' }}
            </button>
          </form>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.profile-page {
  padding: 32px;
  max-width: 900px;
  animation: fadeIn 0.3s ease;
}

.page-header {
  margin-bottom: 28px;
}

.page-header h1 {
  font-size: 26px;
  font-weight: 700;
  color: #1e1b3a;
  margin-bottom: 4px;
}

.subtitle {
  color: #8b8a9e;
  font-size: 14px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 80px;
  color: #8b8a9e;
  font-size: 14px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #ede9fe;
  border-top-color: #6c5ce7;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.profile-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 24px;
  align-items: start;
}

/* Profile card */
.profile-card {
  background: #fff;
  border: 1px solid #ebe8f7;
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 1px 3px rgba(108, 92, 231, 0.04);
}

.profile-card-header {
  text-align: center;
  margin-bottom: 24px;
}

.avatar-large {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 26px;
  margin: 0 auto 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.profile-card-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1e1b3a;
  margin-bottom: 4px;
}

.profile-email {
  font-size: 13px;
  color: #8b8a9e;
  margin-bottom: 12px;
}

.role-badge {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
  border: 1px solid;
}

.profile-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 20px 0;
  border-top: 1px solid #f3f1fa;
  border-bottom: 1px solid #f3f1fa;
  margin-bottom: 20px;
}

.profile-stat {
  text-align: center;
}

.profile-stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #1e1b3a;
}

.profile-stat-label {
  font-size: 11px;
  color: #8b8a9e;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  font-weight: 500;
  margin-top: 2px;
}

.profile-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  font-size: 13px;
  border-bottom: 1px solid #f8f7ff;
}

.profile-detail:last-child {
  border-bottom: none;
}

.detail-label {
  color: #8b8a9e;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.detail-value {
  color: #1e1b3a;
  font-weight: 500;
}

/* Edit form */
.edit-card {
  background: #fff;
  border: 1px solid #ebe8f7;
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 1px 3px rgba(108, 92, 231, 0.04);
}

.edit-card h2 {
  font-size: 18px;
  font-weight: 700;
  color: #1e1b3a;
  margin-bottom: 24px;
}

.success-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #d1fae5;
  color: #065f46;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  margin-bottom: 18px;
  font-weight: 500;
  border: 1px solid #a7f3d0;
}

.form-group {
  margin-bottom: 18px;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #4a4568;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1.5px solid #e2e0f0;
  border-radius: 10px;
  font-size: 13px;
  outline: none;
  transition: all 0.2s ease;
  box-sizing: border-box;
  background: #faf9ff;
  color: #1e1b3a;
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: #b0adc4;
}

.form-group input:focus,
.form-group textarea:focus {
  border-color: #6c5ce7;
  box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.12);
  background: #fff;
}

.readonly-info p {
  font-size: 13px;
  color: #1e1b3a;
  text-transform: capitalize;
  font-weight: 500;
}

.hint {
  color: #a5a3b8;
  font-size: 11px;
  text-transform: none;
  font-weight: 400;
}

.save-btn {
  padding: 10px 24px;
  font-size: 14px;
}

.spinner {
  animation: spin 0.8s linear infinite;
}
</style>
