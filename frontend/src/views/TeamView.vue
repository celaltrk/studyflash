<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import type { UserProfile } from '../types'

const users = ref<UserProfile[]>([])
const loading = ref(true)
const currentUser = api.getUser()
const isAdmin = computed(() => currentUser?.is_admin || currentUser?.role === 'admin')

// Filters
const roleFilter = ref('')
const showInactive = ref(false)

// Create user modal
const showCreateModal = ref(false)
const creating = ref(false)
const createForm = ref({
  email: '',
  password: '',
  display_name: '',
  role: 'support' as 'admin' | 'support' | 'billing' | 'engineering',
  department: '',
  phone: '',
  bio: '',
  max_open_tickets: 20,
})

// Edit user modal
const showEditModal = ref(false)
const editing = ref(false)
const editingUser = ref<UserProfile | null>(null)
const editForm = ref({
  display_name: '',
  role: 'support' as 'admin' | 'support' | 'billing' | 'engineering',
  department: '',
  phone: '',
  bio: '',
  is_active: true,
  max_open_tickets: 20,
})

const filteredUsers = computed(() => {
  let result = users.value
  if (roleFilter.value) {
    result = result.filter(u => u.role === roleFilter.value)
  }
  if (!showInactive.value) {
    result = result.filter(u => u.is_active)
  }
  return result
})

const roleCounts = computed(() => {
  const counts: Record<string, number> = {}
  for (const u of users.value) {
    if (u.is_active) {
      counts[u.role] = (counts[u.role] || 0) + 1
    }
  }
  return counts
})

async function loadUsers() {
  loading.value = true
  try {
    users.value = await api.getUsers({ active_only: !showInactive.value })
  } finally {
    loading.value = false
  }
}

async function createUser() {
  creating.value = true
  try {
    const data: Record<string, any> = { ...createForm.value }
    if (!data.department) delete data.department
    if (!data.phone) delete data.phone
    if (!data.bio) delete data.bio
    await api.createUser(data)
    showCreateModal.value = false
    createForm.value = { email: '', password: '', display_name: '', role: 'support', department: '', phone: '', bio: '', max_open_tickets: 20 }
    await loadUsers()
  } catch (e: any) {
    alert('Failed to create user: ' + e.message)
  } finally {
    creating.value = false
  }
}

function openEditModal(user: UserProfile) {
  editingUser.value = user
  editForm.value = {
    display_name: user.display_name,
    role: user.role,
    department: user.department || '',
    phone: user.phone || '',
    bio: user.bio || '',
    is_active: user.is_active,
    max_open_tickets: user.max_open_tickets,
  }
  showEditModal.value = true
}

async function saveEdit() {
  if (!editingUser.value) return
  editing.value = true
  try {
    const data: Record<string, any> = {}
    if (editForm.value.display_name !== editingUser.value.display_name) data.display_name = editForm.value.display_name
    if (editForm.value.role !== editingUser.value.role) data.role = editForm.value.role
    if ((editForm.value.department || null) !== editingUser.value.department) data.department = editForm.value.department || null
    if ((editForm.value.phone || null) !== editingUser.value.phone) data.phone = editForm.value.phone || null
    if ((editForm.value.bio || null) !== editingUser.value.bio) data.bio = editForm.value.bio || null
    if (editForm.value.is_active !== editingUser.value.is_active) data.is_active = editForm.value.is_active
    if (editForm.value.max_open_tickets !== editingUser.value.max_open_tickets) data.max_open_tickets = editForm.value.max_open_tickets

    if (Object.keys(data).length > 0) {
      await api.updateUser(editingUser.value.id, data)
    }
    showEditModal.value = false
    await loadUsers()
  } catch (e: any) {
    alert('Failed to update user: ' + e.message)
  } finally {
    editing.value = false
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

function roleIcon(role: string): string {
  const icons: Record<string, string> = {
    admin: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    support: 'M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7z',
    billing: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    engineering: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
  }
  return icons[role] || ''
}

function initials(name: string): string {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
}

onMounted(loadUsers)
</script>

<template>
  <div class="team-page">
    <header class="page-header">
      <div>
        <h1>Team Management</h1>
        <p class="subtitle">Manage users, roles, and ticket assignment capacity</p>
      </div>
      <button v-if="isAdmin" class="btn btn-primary" @click="showCreateModal = true">
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/></svg>
        Add User
      </button>
    </header>

    <!-- Role summary cards -->
    <div class="role-cards">
      <div
        v-for="role in ['support', 'billing', 'engineering', 'admin']"
        :key="role"
        class="role-card"
        :class="{ active: roleFilter === role }"
        @click="roleFilter = roleFilter === role ? '' : role"
      >
        <div class="role-icon" :style="{ background: roleColor(role) + '15', color: roleColor(role) }">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="roleIcon(role)"/></svg>
        </div>
        <div class="role-count" :style="{ color: roleColor(role) }">{{ roleCounts[role] || 0 }}</div>
        <div class="role-label">{{ role }}</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <label class="checkbox-label">
        <input type="checkbox" v-model="showInactive" @change="loadUsers" />
        <span class="checkbox-custom"></span>
        Show inactive users
      </label>
      <span class="result-count">{{ filteredUsers.length }} user{{ filteredUsers.length !== 1 ? 's' : '' }}</span>
    </div>

    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <span>Loading team...</span>
    </div>

    <div v-else class="user-grid">
      <div v-for="user in filteredUsers" :key="user.id" class="user-card" :class="{ inactive: !user.is_active }">
        <div class="user-card-header">
          <div class="avatar" :style="{ background: `linear-gradient(135deg, ${roleColor(user.role)}dd, ${roleColor(user.role)})` }">{{ initials(user.display_name) }}</div>
          <div class="user-card-info">
            <div class="user-card-name">{{ user.display_name }}</div>
            <div class="user-card-email">{{ user.email }}</div>
          </div>
          <button v-if="isAdmin" class="btn-icon" @click.stop="openEditModal(user)" title="Edit user">
            <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/></svg>
          </button>
        </div>
        <div class="user-card-body">
          <div class="user-card-meta">
            <span class="role-badge" :style="{ background: roleColor(user.role) + '12', color: roleColor(user.role), borderColor: roleColor(user.role) + '30' }">
              {{ user.role }}
            </span>
            <span v-if="user.department" class="department">{{ user.department }}</span>
            <span v-if="!user.is_active" class="badge badge-inactive">Inactive</span>
          </div>
          <div class="ticket-load">
            <div class="ticket-load-bar-wrapper">
              <div
                class="ticket-load-bar"
                :style="{ width: Math.min(100, (user.open_ticket_count / user.max_open_tickets) * 100) + '%' }"
                :class="{ warning: user.open_ticket_count >= user.max_open_tickets * 0.8, full: user.open_ticket_count >= user.max_open_tickets }"
              ></div>
            </div>
            <span class="ticket-load-label">{{ user.open_ticket_count }}/{{ user.max_open_tickets }} tickets</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Create User Modal -->
    <Teleport to="body">
      <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
        <div class="modal">
          <div class="modal-header">
            <h2>Create New User</h2>
            <button class="modal-close" @click="showCreateModal = false">
              <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
            </button>
          </div>
          <form @submit.prevent="createUser">
            <div class="form-group">
              <label>Display Name</label>
              <input v-model="createForm.display_name" required />
            </div>
            <div class="form-group">
              <label>Email</label>
              <input v-model="createForm.email" type="email" required />
            </div>
            <div class="form-group">
              <label>Password</label>
              <input v-model="createForm.password" type="password" required minlength="8" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Role</label>
                <select v-model="createForm.role">
                  <option value="support">Support</option>
                  <option value="billing">Billing</option>
                  <option value="engineering">Engineering</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div class="form-group">
                <label>Department</label>
                <input v-model="createForm.department" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Phone</label>
                <input v-model="createForm.phone" />
              </div>
              <div class="form-group">
                <label>Max Open Tickets</label>
                <input v-model.number="createForm.max_open_tickets" type="number" min="1" max="100" />
              </div>
            </div>
            <div class="form-group">
              <label>Bio</label>
              <textarea v-model="createForm.bio" rows="2"></textarea>
            </div>
            <div class="modal-actions">
              <button type="button" class="btn" @click="showCreateModal = false">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="creating">
                {{ creating ? 'Creating...' : 'Create User' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Edit User Modal -->
    <Teleport to="body">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
        <div class="modal">
          <div class="modal-header">
            <h2>Edit User</h2>
            <button class="modal-close" @click="showEditModal = false">
              <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
            </button>
          </div>
          <form @submit.prevent="saveEdit">
            <div class="form-group">
              <label>Display Name</label>
              <input v-model="editForm.display_name" required />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Role</label>
                <select v-model="editForm.role">
                  <option value="support">Support</option>
                  <option value="billing">Billing</option>
                  <option value="engineering">Engineering</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div class="form-group">
                <label>Department</label>
                <input v-model="editForm.department" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Phone</label>
                <input v-model="editForm.phone" />
              </div>
              <div class="form-group">
                <label>Max Open Tickets</label>
                <input v-model.number="editForm.max_open_tickets" type="number" min="1" max="100" />
              </div>
            </div>
            <div class="form-group">
              <label>Bio</label>
              <textarea v-model="editForm.bio" rows="2"></textarea>
            </div>
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="editForm.is_active" />
                <span class="checkbox-custom"></span>
                Active
              </label>
            </div>
            <div class="modal-actions">
              <button type="button" class="btn" @click="showEditModal = false">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="editing">
                {{ editing ? 'Saving...' : 'Save Changes' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.team-page {
  padding: 32px;
  max-width: 1100px;
  animation: fadeIn 0.3s ease;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
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

/* Role summary cards */
.role-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

.role-card {
  background: #fff;
  border: 1px solid #ebe8f7;
  border-radius: 14px;
  padding: 18px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(108, 92, 231, 0.04);
}

.role-card:hover {
  border-color: #c4b5fd;
  box-shadow: 0 4px 12px rgba(108, 92, 231, 0.1);
}

.role-card.active {
  border-color: #6c5ce7;
  background: #faf9ff;
  box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.12);
}

.role-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 10px;
}

.role-count {
  font-size: 28px;
  font-weight: 700;
}

.role-label {
  font-size: 12px;
  color: #8b8a9e;
  text-transform: capitalize;
  margin-top: 2px;
  font-weight: 500;
}

/* Filters */
.filters-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 8px 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #4a4568;
  cursor: pointer;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  accent-color: #6c5ce7;
  width: 16px;
  height: 16px;
}

.result-count {
  font-size: 13px;
  color: #8b8a9e;
  font-weight: 500;
}

/* User grid */
.user-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.user-card {
  background: #fff;
  border: 1px solid #ebe8f7;
  border-radius: 14px;
  padding: 18px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(108, 92, 231, 0.04);
}

.user-card:hover {
  box-shadow: 0 4px 16px rgba(108, 92, 231, 0.1);
  transform: translateY(-1px);
}

.user-card.inactive { opacity: 0.55; }

.user-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.avatar {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-card-info {
  flex: 1;
  min-width: 0;
}

.user-card-name {
  font-weight: 600;
  font-size: 14px;
  color: #1e1b3a;
}

.user-card-email {
  font-size: 12px;
  color: #8b8a9e;
  overflow: hidden;
  text-overflow: ellipsis;
}

.btn-icon {
  background: none;
  border: 1px solid #ebe8f7;
  border-radius: 8px;
  padding: 7px 8px;
  cursor: pointer;
  color: #8b8a9e;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
}

.btn-icon:hover {
  background: #f5f3ff;
  color: #6c5ce7;
  border-color: #c4b5fd;
}

.user-card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.role-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  text-transform: capitalize;
  border: 1px solid;
}

.badge-inactive {
  background: #f1f5f9;
  color: #94a3b8;
  border: 1px solid #e2e8f0;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 20px;
}

.department {
  font-size: 12px;
  color: #4a4568;
}

.ticket-load {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ticket-load-bar-wrapper {
  flex: 1;
  height: 6px;
  background: #f1f0f9;
  border-radius: 3px;
  overflow: hidden;
}

.ticket-load-bar {
  height: 100%;
  background: linear-gradient(90deg, #8b7ef5, #6c5ce7);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.ticket-load-bar.warning { background: linear-gradient(90deg, #fbbf24, #d97706); }
.ticket-load-bar.full { background: linear-gradient(90deg, #f87171, #dc2626); }

.ticket-load-label {
  font-size: 11px;
  color: #8b8a9e;
  white-space: nowrap;
  font-weight: 500;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(30, 27, 58, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.modal {
  background: #fff;
  border-radius: 20px;
  padding: 0;
  width: 500px;
  max-width: 92vw;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(30, 27, 58, 0.25);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px 0;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 700;
  color: #1e1b3a;
}

.modal-close {
  background: none;
  border: none;
  color: #8b8a9e;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.15s;
  display: flex;
}

.modal-close:hover {
  background: #f5f3ff;
  color: #6c5ce7;
}

.modal form {
  padding: 20px 28px 28px;
}

.form-group {
  margin-bottom: 16px;
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
.form-group select,
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

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: #6c5ce7;
  box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.12);
  background: #fff;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #ebe8f7;
}
</style>
