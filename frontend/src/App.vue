<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from './api'

const route = useRoute()
const router = useRouter()

const user = computed(() => api.getUser())
const showSidebar = computed(() => route.name !== 'login')

function logout() {
  api.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app">
    <nav class="sidebar" v-if="showSidebar">
      <div class="logo">
        <img src="/studyflash.png" alt="Studyflash" class="logo-icon" />
        <span class="logo-text">Studyflash<br/><small>Support</small></span>
      </div>
      <ul class="nav-links">
        <li>
          <router-link to="/" :class="{ active: route.name === 'dashboard' }">
            <svg class="nav-svg" viewBox="0 0 20 20" fill="currentColor"><path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 6a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zm10 0a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"/></svg>
            Dashboard
          </router-link>
        </li>
        <li>
          <router-link to="/tickets" :class="{ active: route.name === 'tickets' || route.name === 'ticket-detail' }">
            <svg class="nav-svg" viewBox="0 0 20 20" fill="currentColor"><path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/><path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/></svg>
            Tickets
          </router-link>
        </li>
        <li>
          <router-link to="/team" :class="{ active: route.name === 'team' }">
            <svg class="nav-svg" viewBox="0 0 20 20" fill="currentColor"><path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zm8 0a3 3 0 11-6 0 3 3 0 016 0zm-4.07 11c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/></svg>
            Team
          </router-link>
        </li>
      </ul>
      <div class="sidebar-footer" v-if="user">
        <router-link to="/profile" class="user-info-link">
          <div class="user-info">
            <div class="user-avatar">{{ user.name?.charAt(0)?.toUpperCase() || '?' }}</div>
            <div class="user-details">
              <div class="user-name">{{ user.name }}</div>
              <div class="user-role">{{ user.role }}</div>
            </div>
          </div>
        </router-link>
        <button class="logout-btn" @click="logout">
          <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 001 1h12a1 1 0 001-1V4a1 1 0 00-1-1H3zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clip-rule="evenodd"/></svg>
          Sign out
        </button>
      </div>
    </nav>
    <main :class="showSidebar ? 'content' : 'content-full'">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #1e1b3a 0%, #16132e 100%);
  color: #e0e0e0;
  padding: 0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
  border-right: 1px solid rgba(108, 92, 231, 0.15);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.logo-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  object-fit: cover;
  flex-shrink: 0;
}

.logo-text {
  font-weight: 600;
  font-size: 15px;
  line-height: 1.2;
  color: #f0eeff;
}

.logo-text small {
  font-weight: 400;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.nav-links {
  list-style: none;
  padding: 16px 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-links li a {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.5);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.nav-links li a:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.9);
}

.nav-links li a.active {
  background: linear-gradient(135deg, rgba(108, 92, 231, 0.9), rgba(90, 75, 209, 0.9));
  color: #fff;
  box-shadow: 0 2px 10px rgba(108, 92, 231, 0.35);
}

.nav-svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  opacity: 0.85;
}

.sidebar-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding: 16px;
}

.user-info-link {
  text-decoration: none;
  display: block;
  margin-bottom: 10px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 10px;
  transition: background 0.2s ease;
}

.user-info-link:hover .user-info {
  background: rgba(255, 255, 255, 0.06);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #8b7ef5, #6c5ce7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
}

.user-details {
  min-width: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: #e8e5ff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  text-transform: capitalize;
}

.logout-btn {
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.4);
  padding: 7px 12px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  width: 100%;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-weight: 500;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.7);
  border-color: rgba(255, 255, 255, 0.12);
}

.content {
  flex: 1;
  margin-left: 240px;
  background: #f1f0f9;
  min-height: 100vh;
  overflow-x: hidden;
}

.content-full {
  flex: 1;
  background: #f1f0f9;
  min-height: 100vh;
}
</style>
