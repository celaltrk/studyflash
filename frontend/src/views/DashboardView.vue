<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api'
import type { DashboardStats } from '../types'

const stats = ref<DashboardStats | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    stats.value = await api.getStats()
  } finally {
    loading.value = false
  }
})

function formatCategory(cat: string): string {
  return cat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function maxCategoryCount(): number {
  if (!stats.value) return 1
  const counts = Object.values(stats.value.category_breakdown) as number[]
  return Math.max(...counts, 1)
}
</script>

<template>
  <div class="dashboard">
    <header class="page-header">
      <div>
        <h1>Dashboard</h1>
        <p class="subtitle">Support ticket overview</p>
      </div>
    </header>

    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <span>Loading dashboard...</span>
    </div>

    <template v-else-if="stats">
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-icon stat-icon-total">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/><path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5z" clip-rule="evenodd"/></svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_tickets }}</div>
            <div class="stat-label">Total Tickets</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon stat-icon-open">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/></svg>
          </div>
          <div class="stat-content">
            <div class="stat-value color-blue">{{ stats.open_tickets }}</div>
            <div class="stat-label">Open</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon stat-icon-progress">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"/></svg>
          </div>
          <div class="stat-content">
            <div class="stat-value color-amber">{{ stats.in_progress_tickets }}</div>
            <div class="stat-label">In Progress</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon stat-icon-resolved">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
          </div>
          <div class="stat-content">
            <div class="stat-value color-green">{{ stats.resolved_tickets }}</div>
            <div class="stat-label">Resolved</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon stat-icon-unassigned">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clip-rule="evenodd"/></svg>
          </div>
          <div class="stat-content">
            <div class="stat-value color-red">{{ stats.unassigned_tickets }}</div>
            <div class="stat-label">Unassigned</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon stat-icon-ai">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path d="M13 7H7v6h6V7z"/><path fill-rule="evenodd" d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z" clip-rule="evenodd"/></svg>
          </div>
          <div class="stat-content">
            <div class="stat-value color-purple">{{ stats.avg_ai_confidence ? (stats.avg_ai_confidence * 100).toFixed(0) + '%' : 'N/A' }}</div>
            <div class="stat-label">Avg AI Confidence</div>
          </div>
        </div>
      </div>

      <div class="card category-breakdown">
        <h2>Tickets by Category</h2>
        <div class="category-bars">
          <div
            v-for="(count, category) in stats.category_breakdown"
            :key="category"
            class="category-row"
          >
            <span class="cat-label">{{ formatCategory(category as string) }}</span>
            <div class="cat-bar-wrapper">
              <div
                class="cat-bar"
                :style="{ width: (count as number / maxCategoryCount() * 100) + '%' }"
              ></div>
            </div>
            <span class="cat-count">{{ count }}</span>
          </div>
        </div>
      </div>

      <div class="cta-section">
        <router-link to="/tickets" class="btn btn-primary cta-btn">
          <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor"><path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/><path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/></svg>
          View All Tickets
        </router-link>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 32px;
  max-width: 1100px;
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

.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.stat-card {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #ebe8f7;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(108, 92, 231, 0.04);
}

.stat-card:hover {
  box-shadow: 0 4px 16px rgba(108, 92, 231, 0.1);
  transform: translateY(-1px);
}

.stat-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon-total { background: #f1f0f9; color: #6c5ce7; }
.stat-icon-open { background: #dbeafe; color: #1e40af; }
.stat-icon-progress { background: #fef3c7; color: #b45309; }
.stat-icon-resolved { background: #d1fae5; color: #065f46; }
.stat-icon-unassigned { background: #fee2e2; color: #b91c1c; }
.stat-icon-ai { background: #ede9fe; color: #6d28d9; }

.stat-content {
  min-width: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e1b3a;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #8b8a9e;
  margin-top: 2px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.color-blue { color: #1e40af; }
.color-amber { color: #b45309; }
.color-green { color: #065f46; }
.color-red { color: #b91c1c; }
.color-purple { color: #6c5ce7; }

.category-breakdown {
  margin-bottom: 20px;
}

.category-breakdown h2 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #1e1b3a;
}

.category-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 10px;
}

.cat-label {
  width: 180px;
  font-size: 13px;
  color: #4a4568;
  text-align: right;
  flex-shrink: 0;
  font-weight: 500;
}

.cat-bar-wrapper {
  flex: 1;
  height: 24px;
  background: #f1f0f9;
  border-radius: 8px;
  overflow: hidden;
}

.cat-bar {
  height: 100%;
  background: linear-gradient(90deg, #8b7ef5, #6c5ce7);
  border-radius: 8px;
  min-width: 6px;
  transition: width 0.5s ease;
}

.cat-count {
  width: 36px;
  font-size: 14px;
  font-weight: 700;
  color: #1e1b3a;
  text-align: right;
}

.cta-section {
  text-align: center;
  margin-top: 8px;
}

.cta-btn {
  padding: 10px 24px;
  font-size: 14px;
}
</style>
