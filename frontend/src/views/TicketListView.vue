<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import type { TicketListItem, TeamMember } from '../types'

const router = useRouter()

const tickets = ref<TicketListItem[]>([])
const teamMembers = ref<TeamMember[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(true)

// Filters
const statusFilter = ref('')
const categoryFilter = ref('')
const assigneeFilter = ref('')
const searchQuery = ref('')

async function loadTickets() {
  loading.value = true
  try {
    const params: Record<string, string | number> = {
      page: page.value,
      page_size: pageSize,
      sort_by: 'created_at',
      sort_order: 'desc',
    }
    if (statusFilter.value) params.status = statusFilter.value
    if (categoryFilter.value) params.category = categoryFilter.value
    if (assigneeFilter.value) params.assignee_id = assigneeFilter.value
    if (searchQuery.value) params.search = searchQuery.value

    const res = await api.getTickets(params)
    tickets.value = res.tickets
    total.value = res.total
  } finally {
    loading.value = false
  }
}

let pollInterval: number | undefined

onMounted(async () => {
  const [_, members] = await Promise.all([loadTickets(), api.getTeamMembers()])
  teamMembers.value = members
  // Auto-refresh ticket list every 30 seconds to pick up new inbound emails
  pollInterval = window.setInterval(() => { loadTickets() }, 30000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

watch([statusFilter, categoryFilter, assigneeFilter], () => {
  page.value = 1
  loadTickets()
})

let searchTimeout: number
function onSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    page.value = 1
    loadTickets()
  }, 300)
}

function totalPages() {
  return Math.ceil(total.value / pageSize)
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const hours = Math.floor(diff / 3600000)
  if (hours < 1) return 'just now'
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return `${Math.floor(days / 30)}mo ago`
}

function formatCategory(cat: string | null): string {
  if (!cat) return ''
  return cat.replace(/_/g, ' ')
}

function langFlag(lang: string): string {
  const flags: Record<string, string> = { de: 'DE', fr: 'FR', en: 'EN', nl: 'NL', it: 'IT' }
  return flags[lang] || lang.toUpperCase()
}

function confidenceColor(conf: number | null): string {
  if (!conf) return '#c4b5fd'
  if (conf >= 0.7) return '#065f46'
  if (conf >= 0.4) return '#b45309'
  return '#b91c1c'
}
</script>

<template>
  <div class="ticket-list-page">
    <header class="page-header">
      <div>
        <h1>Tickets</h1>
        <p class="subtitle">{{ total }} total tickets</p>
      </div>
    </header>

    <!-- Filters -->
    <div class="filters">
      <div class="search-wrapper">
        <svg class="search-icon" width="16" height="16" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/></svg>
        <input
          type="text"
          v-model="searchQuery"
          @input="onSearch"
          placeholder="Search tickets..."
          class="search-input"
        />
      </div>
      <select v-model="statusFilter">
        <option value="">All Status</option>
        <option value="open">Open</option>
        <option value="in_progress">In Progress</option>
        <option value="waiting">Waiting</option>
        <option value="resolved">Resolved</option>
        <option value="closed">Closed</option>
      </select>
      <select v-model="categoryFilter">
        <option value="">All Categories</option>
        <option value="refund_request">Refund Request</option>
        <option value="subscription_cancellation">Subscription Cancellation</option>
        <option value="flashcard_issues">Flashcard Issues</option>
        <option value="technical_errors">Technical Errors</option>
        <option value="account_issues">Account Issues</option>
        <option value="content_upload">Content Upload</option>
        <option value="quiz_issues">Quiz Issues</option>
        <option value="podcast_issues">Podcast Issues</option>
        <option value="garbage">Garbage / Spam</option>
        <option value="misunderstanding">Misunderstanding</option>
        <option value="other">Other</option>
      </select>
      <select v-model="assigneeFilter">
        <option value="">All Assignees</option>
        <option value="0">Unassigned</option>
        <option v-for="m in teamMembers" :key="m.id" :value="m.id">{{ m.name }}</option>
      </select>
    </div>

    <!-- Table -->
    <div class="card table-card">
      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <span>Loading tickets...</span>
      </div>
      <table v-else>
        <thead>
          <tr>
            <th>ID</th>
            <th>Subject</th>
            <th>Lang</th>
            <th>Category</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Assignee</th>
            <th>AI</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="ticket in tickets"
            :key="ticket.id"
            @click="router.push(`/tickets/${ticket.id}`)"
            class="ticket-row"
          >
            <td class="id-cell">#{{ ticket.id }}</td>
            <td class="subject-cell">
              <div class="subject-text">
                {{ ticket.subject }}
                <span v-if="ticket.source === 'email'" class="source-tag">
                  <svg width="10" height="10" viewBox="0 0 20 20" fill="currentColor"><path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/><path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/></svg>
                </span>
              </div>
              <div class="sender-info">{{ ticket.sender_email }}</div>
            </td>
            <td><span class="lang-badge">{{ langFlag(ticket.language) }}</span></td>
            <td><span class="category-text">{{ formatCategory(ticket.ai_category) }}</span></td>
            <td><span :class="'badge badge-' + ticket.status">{{ ticket.status.replace('_', ' ') }}</span></td>
            <td><span :class="'badge badge-' + ticket.priority">{{ ticket.priority }}</span></td>
            <td>
              <span v-if="ticket.assignee" class="assignee-name">{{ ticket.assignee.name }}</span>
              <span v-else class="unassigned">Unassigned</span>
            </td>
            <td>
              <span
                v-if="ticket.ai_confidence"
                class="confidence"
                :style="{ color: confidenceColor(ticket.ai_confidence) }"
              >
                {{ (ticket.ai_confidence * 100).toFixed(0) }}%
              </span>
            </td>
            <td class="time-cell">{{ timeAgo(ticket.created_at) }}</td>
          </tr>
          <tr v-if="tickets.length === 0">
            <td colspan="9" class="empty">
              <svg width="40" height="40" viewBox="0 0 20 20" fill="currentColor" style="color: #c4b5fd; margin-bottom: 8px;"><path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/><path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/></svg>
              <div>No tickets found</div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="totalPages() > 1">
      <button class="btn btn-sm" :disabled="page <= 1" @click="page--; loadTickets()">
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
        Previous
      </button>
      <span class="page-info">Page {{ page }} of {{ totalPages() }}</span>
      <button class="btn btn-sm" :disabled="page >= totalPages()" @click="page++; loadTickets()">
        Next
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/></svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.ticket-list-page {
  padding: 32px;
  animation: fadeIn 0.3s ease;
  overflow-x: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 26px;
  font-weight: 700;
  color: #1e1b3a;
  margin-bottom: 4px;
}

.subtitle { color: #8b8a9e; font-size: 14px; }

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.search-wrapper {
  flex: 1;
  min-width: 200px;
  position: relative;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #a5a3b8;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 9px 12px 9px 36px;
  border: 1px solid #e2e0f0;
  border-radius: 10px;
  font-size: 13px;
  background: #fff;
  transition: all 0.2s ease;
  outline: none;
  color: #334155;
}

.search-input:focus {
  border-color: #6c5ce7;
  box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.12);
}

.search-input::placeholder {
  color: #b0adc4;
}

.filters select {
  min-width: 140px;
  padding: 9px 12px;
  border-radius: 10px;
}

.table-card {
  padding: 0;
  overflow-x: auto;
  overflow-y: hidden;
  border-radius: 14px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 60px;
  color: #8b8a9e;
  font-size: 14px;
}

.loading-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid #ede9fe;
  border-top-color: #6c5ce7;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  text-align: left;
  padding: 14px 16px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: #8b8a9e;
  border-bottom: 1px solid #ebe8f7;
  background: #faf9ff;
  font-weight: 600;
}

td {
  padding: 14px 16px;
  border-bottom: 1px solid #f3f1fa;
  font-size: 13px;
}

.ticket-row {
  cursor: pointer;
  transition: all 0.15s ease;
}

.ticket-row:hover {
  background: #f8f7ff;
}

.ticket-row:active {
  background: #f1f0f9;
}

.id-cell {
  color: #8b8a9e;
  font-size: 12px;
  white-space: nowrap;
  font-weight: 500;
}

.subject-cell {
  max-width: 280px;
}

.subject-text {
  font-weight: 600;
  color: #1e1b3a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 280px;
}

.sender-info {
  font-size: 11px;
  color: #a5a3b8;
  margin-top: 2px;
}

.source-tag {
  display: inline-flex;
  align-items: center;
  color: #1d4ed8;
  margin-left: 6px;
  vertical-align: middle;
}

.lang-badge {
  background: #ede9fe;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  color: #6c5ce7;
  letter-spacing: 0.5px;
}

.category-text {
  font-size: 12px;
  color: #4a4568;
  text-transform: capitalize;
}

.assignee-name {
  font-size: 12px;
  color: #334155;
  font-weight: 500;
}

.unassigned {
  font-size: 12px;
  color: #c4b5fd;
  font-style: italic;
}

.confidence {
  font-weight: 700;
  font-size: 12px;
}

.time-cell {
  color: #8b8a9e;
  font-size: 12px;
  white-space: nowrap;
}

.empty {
  text-align: center;
  color: #8b8a9e;
  padding: 60px 20px !important;
  font-size: 14px;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
}

.page-info {
  font-size: 13px;
  color: #4a4568;
  font-weight: 500;
}
</style>
