<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import type { Ticket, TeamMember } from '../types'

const route = useRoute()
const router = useRouter()
const ticketId = Number(route.params.id)

const ticket = ref<Ticket | null>(null)
const teamMembers = ref<TeamMember[]>([])
const loading = ref(true)
const replyText = ref('')
const sending = ref(false)
const aiLoading = ref<string | null>(null)
const autoAssigning = ref(false)
const showTranslated = ref(false)
const translating = ref(false)
const translatingReply = ref(false)
const replyTranslation = ref<string | null>(null)
const showReplyTranslation = ref(false)
const replyTextarea = ref<HTMLTextAreaElement | null>(null)

function autoResize() {
  const el = replyTextarea.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.max(el.scrollHeight, 100) + 'px'
}

async function loadTicket() {
  ticket.value = await api.getTicket(ticketId)
}

let pollInterval: number | undefined

onMounted(async () => {
  try {
    const [_, members] = await Promise.all([loadTicket(), api.getTeamMembers()])
    teamMembers.value = members
  } finally {
    loading.value = false
  }
  // Auto-refresh conversation every 15 seconds to pick up inbound emails
  pollInterval = window.setInterval(() => { loadTicket() }, 15000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

async function updateField(field: string, value: any) {
  if (!ticket.value) return
  await api.updateTicket(ticketId, { [field]: value })
  await loadTicket()
}

async function sendReply() {
  if (!replyText.value.trim()) return
  sending.value = true
  try {
    await api.addMessage(ticketId, replyText.value)
    replyText.value = ''
    await loadTicket()
  } finally {
    sending.value = false
  }
}

async function runAI(action: string) {
  aiLoading.value = action
  try {
    if (action === 'categorize') {
      await api.categorizeTicket(ticketId)
    } else if (action === 'draft') {
      const result = await api.draftResponse(ticketId)
      replyText.value = result.draft_response
    } else if (action === 'enrich') {
      await api.enrichTicket(ticketId)
    }
    await loadTicket()
  } finally {
    aiLoading.value = null
  }
}

watch(replyText, () => {
  replyTranslation.value = null
  showReplyTranslation.value = false
  setTimeout(autoResize, 0)
})

async function translateReply() {
  if (!replyText.value.trim()) return
  translatingReply.value = true
  try {
    const result = await api.translateText(replyText.value)
    if (result.translated_body) {
      replyTranslation.value = result.translated_body
      showReplyTranslation.value = true
    }
  } finally {
    translatingReply.value = false
  }
}

async function translateTicket() {
  translating.value = true
  try {
    await api.translateTicket(ticketId)
    await loadTicket()
    showTranslated.value = true
  } finally {
    translating.value = false
  }
}

const parsedSentry = computed(() => {
  if (!ticket.value?.sentry_issues) return null
  try { return JSON.parse(ticket.value.sentry_issues) } catch { return null }
})

const parsedUserMeta = computed(() => {
  if (!ticket.value?.user_metadata) return null
  try { return JSON.parse(ticket.value.user_metadata) } catch { return null }
})

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatCategory(cat: string | null): string {
  if (!cat) return 'Uncategorized'
  return cat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

async function autoAssign() {
  autoAssigning.value = true
  try {
    const result = await api.autoAssignTicket(ticketId)
    if (!result.assigned) {
      alert(result.message || 'Could not auto-assign')
    }
    await loadTicket()
  } catch (e: any) {
    alert('Auto-assign failed: ' + e.message)
  } finally {
    autoAssigning.value = false
  }
}

function langFlag(lang: string): string {
  const flags: Record<string, string> = { de: 'DE', fr: 'FR', en: 'EN', nl: 'NL', it: 'IT' }
  return flags[lang] || lang.toUpperCase()
}
</script>

<template>
  <div class="ticket-detail" v-if="!loading && ticket">
    <!-- Header -->
    <header class="detail-header">
      <button class="btn btn-sm back-btn" @click="router.push('/tickets')">
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd"/></svg>
        Back
      </button>
      <div class="header-info">
        <h1>
          <span class="ticket-id">#{{ ticket.id }}</span>
          {{ ticket.subject }}
        </h1>
        <div class="header-meta">
          <span :class="'badge badge-' + ticket.status">{{ ticket.status.replace('_', ' ') }}</span>
          <span :class="'badge badge-' + ticket.priority">{{ ticket.priority }}</span>
          <span class="lang-badge">{{ langFlag(ticket.language) }}</span>
          <span v-if="ticket.outlook_conversation_id" class="source-badge email-badge">
            <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/><path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/></svg>
            Outlook Synced
          </span>
          <span class="meta-text">from <strong>{{ ticket.sender_email }}</strong> &middot; {{ formatDate(ticket.created_at) }}</span>
        </div>
      </div>
    </header>

    <div class="detail-layout">
      <!-- Main content -->
      <div class="main-panel">
        <!-- Conversation -->
        <div class="card conversation">
          <h2>
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor" style="vertical-align: -2px; margin-right: 6px; color: #6c5ce7;"><path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/></svg>
            Conversation
          </h2>
          <div v-if="ticket.outlook_conversation_id" class="outlook-sync-banner">
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor"><path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/><path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/></svg>
            <div class="outlook-sync-text">
              <strong>Linked to Outlook thread</strong>
              <span>This conversation is synced with Outlook. Replies from either platform appear in both.</span>
            </div>
          </div>
          <div class="messages">
            <div
              v-for="msg in ticket.messages"
              :key="msg.id"
              :class="['message', 'message-' + msg.sender_type]"
            >
              <div class="msg-header">
                <div class="msg-sender">
                  <span class="msg-avatar" :class="'avatar-' + msg.sender_type">{{ (msg.sender_name || msg.sender_type).charAt(0).toUpperCase() }}</span>
                  <strong>{{ msg.sender_name || msg.sender_type }}</strong>
                  <span v-if="msg.outlook_message_id" class="source-badge email-badge">
                    <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/><path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/></svg>
                    via Outlook
                  </span>
                </div>
                <span class="msg-time">{{ formatDate(msg.created_at) }}</span>
              </div>
              <div class="msg-body">{{ msg.body }}</div>
            </div>
          </div>

          <!-- Translation -->
          <div v-if="ticket.language && ticket.language !== 'en'" class="translate-bar">
            <template v-if="showTranslated && ticket.translated_body">
              <div class="translated-notice">
                <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.69.914 1.005a1 1 0 11-1.36 1.465c-.34-.316-.653-.644-.94-.984a18.8 18.8 0 01-3.02 2.97 1 1 0 11-1.146-1.637 16.77 16.77 0 002.694-2.54A16.7 16.7 0 013.2 7.24a1 1 0 111.83-.804 14.7 14.7 0 001.345 2.427A16.9 16.9 0 007.976 5H2a1 1 0 110-2h4V2a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98a1 1 0 11-1.79.895L15.383 16h-4.764l-.724 1.447a1 1 0 11-1.788-.894l.99-1.98.019-.038 2.99-5.982A1 1 0 0113 8zm-1.382 6h2.764L13 11.236 11.618 14z" clip-rule="evenodd"/></svg>
                Translated from {{ langFlag(ticket.language) }}
              </div>
              <div class="translated-body">{{ ticket.translated_body }}</div>
              <button class="btn btn-sm" @click="showTranslated = false">Hide translation</button>
            </template>
            <template v-else>
              <button
                class="btn btn-sm translate-btn"
                @click="ticket.translated_body ? (showTranslated = true) : translateTicket()"
                :disabled="translating"
              >
                <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.69.914 1.005a1 1 0 11-1.36 1.465c-.34-.316-.653-.644-.94-.984a18.8 18.8 0 01-3.02 2.97 1 1 0 11-1.146-1.637 16.77 16.77 0 002.694-2.54A16.7 16.7 0 013.2 7.24a1 1 0 111.83-.804 14.7 14.7 0 001.345 2.427A16.9 16.9 0 007.976 5H2a1 1 0 110-2h4V2a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98a1 1 0 11-1.79.895L15.383 16h-4.764l-.724 1.447a1 1 0 11-1.788-.894l.99-1.98.019-.038 2.99-5.982A1 1 0 0113 8zm-1.382 6h2.764L13 11.236 11.618 14z" clip-rule="evenodd"/></svg>
                {{ translating ? 'Translating...' : 'Translate to English' }}
              </button>
            </template>
          </div>

          <!-- Reply -->
          <div class="reply-box">
            <div v-if="ticket.outlook_message_id" class="outlook-reply-notice">
              <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/></svg>
              Your reply will also be sent to the customer's Outlook inbox
            </div>
            <textarea
              ref="replyTextarea"
              v-model="replyText"
              @input="autoResize"
              placeholder="Type your reply..."
              rows="4"
            ></textarea>
            <div v-if="showReplyTranslation && replyTranslation" class="translate-bar">
              <div class="translated-notice">
                <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.69.914 1.005a1 1 0 11-1.36 1.465c-.34-.316-.653-.644-.94-.984a18.8 18.8 0 01-3.02 2.97 1 1 0 11-1.146-1.637 16.77 16.77 0 002.694-2.54A16.7 16.7 0 013.2 7.24a1 1 0 111.83-.804 14.7 14.7 0 001.345 2.427A16.9 16.9 0 007.976 5H2a1 1 0 110-2h4V2a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98a1 1 0 11-1.79.895L15.383 16h-4.764l-.724 1.447a1 1 0 11-1.788-.894l.99-1.98.019-.038 2.99-5.982A1 1 0 0113 8zm-1.382 6h2.764L13 11.236 11.618 14z" clip-rule="evenodd"/></svg>
                Translated to English
              </div>
              <div class="translated-body">{{ replyTranslation }}</div>
              <button class="btn btn-sm" @click="showReplyTranslation = false">Hide translation</button>
            </div>
            <div class="reply-actions">
              <button
                class="btn"
                @click="replyTranslation && !showReplyTranslation ? (showReplyTranslation = true) : translateReply()"
                :disabled="translatingReply || !replyText.trim()"
              >
                <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.69.914 1.005a1 1 0 11-1.36 1.465c-.34-.316-.653-.644-.94-.984a18.8 18.8 0 01-3.02 2.97 1 1 0 11-1.146-1.637 16.77 16.77 0 002.694-2.54A16.7 16.7 0 013.2 7.24a1 1 0 111.83-.804 14.7 14.7 0 001.345 2.427A16.9 16.9 0 007.976 5H2a1 1 0 110-2h4V2a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98a1 1 0 11-1.79.895L15.383 16h-4.764l-.724 1.447a1 1 0 11-1.788-.894l.99-1.98.019-.038 2.99-5.982A1 1 0 0113 8zm-1.382 6h2.764L13 11.236 11.618 14z" clip-rule="evenodd"/></svg>
                {{ translatingReply ? 'Translating...' : 'Translate' }}
              </button>
              <button
                class="btn ai-btn"
                @click="runAI('draft')"
                :disabled="aiLoading !== null"
              >
                <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path d="M13 7H7v6h6V7z"/><path fill-rule="evenodd" d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z" clip-rule="evenodd"/></svg>
                {{ aiLoading === 'draft' ? 'Generating...' : 'AI Draft' }}
              </button>
              <button
                class="btn btn-primary"
                @click="sendReply"
                :disabled="sending || !replyText.trim()"
              >
                <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/></svg>
                {{ sending ? 'Sending...' : (ticket.outlook_message_id ? 'Send Reply & Email' : 'Send Reply') }}
              </button>
            </div>
          </div>
        </div>

      </div>

      <!-- Sidebar -->
      <div class="side-panel">
        <!-- Actions -->
        <div class="card sidebar-card">
          <h3>Status</h3>
          <select :value="ticket.status" @change="updateField('status', ($event.target as HTMLSelectElement).value)">
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="waiting">Waiting</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>

          <h3>Priority</h3>
          <select :value="ticket.priority" @change="updateField('priority', ($event.target as HTMLSelectElement).value)">
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>

          <h3>Assignee</h3>
          <select
            :value="ticket.assignee_id || ''"
            @change="updateField('assignee_id', ($event.target as HTMLSelectElement).value || null)"
          >
            <option value="">Unassigned</option>
            <option v-for="m in teamMembers" :key="m.id" :value="m.id">{{ m.name }} ({{ m.role }})</option>
          </select>
          <div v-if="ticket.ai_suggested_assignee" class="ai-suggestion">
            <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path d="M13 7H7v6h6V7z"/><path fill-rule="evenodd" d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z" clip-rule="evenodd"/></svg>
            AI suggests: <strong>{{ ticket.ai_suggested_assignee }}</strong> team
          </div>
          <button
            class="btn btn-sm sidebar-action-btn"
            @click="autoAssign"
            :disabled="autoAssigning || !(ticket.category || ticket.ai_category)"
          >
            {{ autoAssigning ? 'Assigning...' : 'Auto-Assign' }}
          </button>
        </div>

        <!-- AI Classification -->
        <div class="card sidebar-card">
          <h3 class="first">AI Classification</h3>
          <div v-if="ticket.ai_category" class="ai-info">
            <div class="ai-row">
              <span class="ai-label">Category</span>
              <span class="ai-value">{{ formatCategory(ticket.ai_category) }}</span>
            </div>
            <div class="ai-row">
              <span class="ai-label">Confidence</span>
              <span class="confidence-badge" :class="{ high: ticket.ai_confidence && ticket.ai_confidence >= 0.7, low: ticket.ai_confidence && ticket.ai_confidence < 0.4 }">
                {{ ticket.ai_confidence ? (ticket.ai_confidence * 100).toFixed(0) + '%' : 'N/A' }}
              </span>
            </div>
            <div v-if="ticket.ai_summary" class="ai-row ai-summary-row">
              <span class="ai-label">Summary</span>
              <span class="ai-summary">{{ ticket.ai_summary }}</span>
            </div>
          </div>
          <div v-else class="empty-state">No classification yet</div>
          <button
            class="btn btn-sm sidebar-action-btn"
            @click="runAI('categorize')"
            :disabled="aiLoading !== null"
          >
            <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path d="M13 7H7v6h6V7z"/><path fill-rule="evenodd" d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z" clip-rule="evenodd"/></svg>
            {{ aiLoading === 'categorize' ? 'Classifying...' : 'Re-classify with AI' }}
          </button>
        </div>

        <!-- Enrichment -->
        <div class="card sidebar-card">
          <h3 class="first">User Context</h3>
          <button
            class="btn btn-sm sidebar-action-btn"
            style="margin-bottom: 14px;"
            @click="runAI('enrich')"
            :disabled="aiLoading !== null"
          >
            <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clip-rule="evenodd"/></svg>
            {{ aiLoading === 'enrich' ? 'Loading...' : 'Fetch User Data' }}
          </button>

          <!-- User metadata -->
          <div v-if="parsedUserMeta" class="enrichment-section">
            <h4>User Info</h4>
            <div class="meta-grid">
              <div class="meta-item"><span class="meta-key">ID</span> <span class="meta-val">{{ parsedUserMeta.user_id }}</span></div>
              <div class="meta-item"><span class="meta-key">Plan</span> <span class="badge badge-open">{{ parsedUserMeta.plan }}</span></div>
              <div class="meta-item"><span class="meta-key">Status</span> <span class="meta-val">{{ parsedUserMeta.status }}</span></div>
              <div class="meta-item"><span class="meta-key">Decks</span> <span class="meta-val">{{ parsedUserMeta.deck_count }}</span></div>
            </div>
          </div>

          <!-- PostHog -->
          <div v-if="ticket.posthog_recording_url" class="enrichment-section">
            <h4>Session Recording</h4>
            <a :href="ticket.posthog_recording_url" target="_blank" class="btn btn-sm sidebar-action-btn">
              <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
              View in PostHog
            </a>
          </div>

          <!-- Sentry -->
          <div v-if="parsedSentry && parsedSentry.length > 0" class="enrichment-section">
            <h4>Sentry Issues</h4>
            <div v-for="issue in parsedSentry" :key="issue.id" class="sentry-issue">
              <a :href="issue.url" target="_blank" class="sentry-title">{{ issue.title }}</a>
              <div class="sentry-meta">{{ issue.level }} &middot; {{ issue.count }} events</div>
            </div>
          </div>
        </div>

        <!-- Tags -->
        <div class="card sidebar-card" v-if="ticket.tags">
          <h3 class="first">Tags</h3>
          <div class="tags">
            <span v-for="tag in ticket.tags.split(',')" :key="tag" class="tag">{{ tag.trim() }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="loading-page">
    <div class="loading-spinner"></div>
    <span>Loading ticket...</span>
  </div>
</template>

<style scoped>
.ticket-detail {
  padding: 24px 32px;
  max-width: 1200px;
  animation: fadeIn 0.3s ease;
  overflow-x: hidden;
}

.loading-page {
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

.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}

.back-btn {
  flex-shrink: 0;
  margin-top: 4px;
}

.header-info h1 {
  font-size: 20px;
  font-weight: 700;
  color: #1e1b3a;
  margin-bottom: 10px;
  line-height: 1.3;
}

.ticket-id {
  color: #8b8a9e;
  font-weight: 400;
  margin-right: 6px;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
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

.meta-text {
  font-size: 12px;
  color: #8b8a9e;
}

.meta-text strong {
  color: #4a4568;
  font-weight: 500;
}

.detail-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  min-width: 0;
}

.main-panel {
  min-width: 0;
}

/* Conversation */
.conversation h2 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1e1b3a;
}

.outlook-sync-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 1px solid #93c5fd;
  border-radius: 10px;
  margin-bottom: 16px;
  color: #1d4ed8;
}

.outlook-sync-banner svg {
  flex-shrink: 0;
  margin-top: 2px;
}

.outlook-sync-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}

.outlook-sync-text strong {
  font-size: 13px;
  color: #1e40af;
}

.outlook-sync-text span {
  color: #3b82f6;
}

.outlook-reply-notice {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #1d4ed8;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 10px;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.message {
  padding: 14px 18px;
  border-radius: 12px;
  border: 1px solid #ebe8f7;
  transition: box-shadow 0.15s ease;
}

.message:hover {
  box-shadow: 0 2px 8px rgba(108, 92, 231, 0.06);
}

.message-customer {
  background: linear-gradient(135deg, #f8f7ff 0%, #f0eeff 100%);
  border-color: #ddd8f7;
  border-left: 3px solid #6c5ce7;
}

.message-agent {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-color: #bbf7d0;
  border-left: 3px solid #10b981;
}

.message-system {
  background: #f8fafc;
  border-color: #e2e8f0;
  font-style: italic;
  border-left: 3px solid #94a3b8;
}

.msg-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 12px;
}

.msg-sender {
  display: flex;
  align-items: center;
  gap: 8px;
}

.msg-avatar {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}

.avatar-customer { background: linear-gradient(135deg, #8b7ef5, #6c5ce7); }
.avatar-agent { background: linear-gradient(135deg, #34d399, #10b981); }
.avatar-system { background: #94a3b8; }

.msg-header strong {
  color: #1e1b3a;
  text-transform: capitalize;
  font-weight: 600;
}

.source-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  letter-spacing: 0.3px;
}

.email-badge {
  background: #dbeafe;
  color: #1d4ed8;
}

.msg-time {
  color: #a5a3b8;
  font-size: 11px;
}

.msg-body {
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  color: #334155;
  overflow-x: auto;
}

.reply-box {
  border-top: 1px solid #ebe8f7;
  padding-top: 18px;
}

.reply-box textarea {
  margin-bottom: 10px;
  border-radius: 10px;
  background: #faf9ff;
  min-height: 100px;
  overflow-y: hidden;
  resize: none;
}

.reply-box textarea:focus {
  background: #fff;
}

.reply-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.ai-btn {
  color: #6c5ce7;
  border-color: #ddd8f7;
  background: #f8f7ff;
}

.ai-btn:hover {
  background: #ede9fe;
  border-color: #c4b5fd;
}

.translate-btn {
  color: #6c5ce7;
}

.translate-bar {
  padding: 14px 0;
  border-top: 1px solid #ebe8f7;
}

.translated-notice {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6c5ce7;
  font-weight: 600;
  margin-bottom: 10px;
}

.translated-body {
  font-size: 13px;
  color: #4a4568;
  line-height: 1.7;
  font-style: italic;
  background: #faf9ff;
  padding: 14px;
  border-radius: 10px;
  margin-bottom: 10px;
  white-space: pre-wrap;
  border: 1px solid #ede9fe;
  overflow-x: auto;
}

/* Sidebar */
.sidebar-card {
  margin-bottom: 16px;
}

.side-panel h3 {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: #8b8a9e;
  margin-bottom: 8px;
  margin-top: 16px;
  font-weight: 600;
}

.side-panel h3.first {
  margin-top: 0;
}

.side-panel select {
  width: 100%;
  margin-bottom: 4px;
  border-radius: 8px;
}

.sidebar-action-btn {
  margin-top: 8px;
  width: 100%;
  justify-content: center;
}

.ai-suggestion {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #6c5ce7;
  margin-top: 6px;
  font-weight: 500;
}

.ai-info {
  font-size: 13px;
}

.ai-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #f3f1fa;
}

.ai-row:last-child {
  border-bottom: none;
}

.ai-summary-row {
  flex-direction: column;
  align-items: flex-start;
}

.ai-label {
  color: #8b8a9e;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 500;
}

.ai-value {
  font-weight: 600;
  color: #1e1b3a;
}

.ai-summary {
  font-size: 12px;
  color: #4a4568;
  line-height: 1.5;
  margin-top: 4px;
}

.confidence-badge {
  font-weight: 700;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 20px;
  background: #fef3c7;
  color: #b45309;
}

.confidence-badge.high {
  background: #d1fae5;
  color: #065f46;
}

.confidence-badge.low {
  background: #fee2e2;
  color: #b91c1c;
}

.empty-state {
  font-size: 13px;
  color: #a5a3b8;
  font-style: italic;
  padding: 8px 0;
}

/* Enrichment */
.enrichment-section {
  margin-bottom: 14px;
  padding-top: 12px;
  border-top: 1px solid #f3f1fa;
}

.enrichment-section:first-child {
  border-top: none;
  padding-top: 0;
}

.enrichment-section h4 {
  font-size: 11px;
  text-transform: uppercase;
  color: #a5a3b8;
  margin-bottom: 8px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.meta-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.meta-key {
  color: #8b8a9e;
  font-weight: 500;
}

.meta-val {
  color: #1e1b3a;
  font-weight: 500;
}

.sentry-issue {
  padding: 8px 0;
  border-bottom: 1px solid #f3f1fa;
}

.sentry-issue:last-child {
  border-bottom: none;
}

.sentry-title {
  font-size: 12px;
  color: #b91c1c;
  text-decoration: none;
  font-weight: 500;
}

.sentry-title:hover {
  text-decoration: underline;
}

.sentry-meta {
  font-size: 10px;
  color: #a5a3b8;
  margin-top: 3px;
}

/* Tags */
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  background: #ede9fe;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  color: #6c5ce7;
  font-weight: 500;
}
</style>
