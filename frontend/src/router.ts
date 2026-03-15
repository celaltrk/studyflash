import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('./views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('./views/DashboardView.vue'),
    },
    {
      path: '/tickets',
      name: 'tickets',
      component: () => import('./views/TicketListView.vue'),
    },
    {
      path: '/tickets/:id',
      name: 'ticket-detail',
      component: () => import('./views/TicketDetailView.vue'),
    },
    {
      path: '/team',
      name: 'team',
      component: () => import('./views/TeamView.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('./views/ProfileView.vue'),
    },
  ],
})

// Auth guard
router.beforeEach((to, _from, next) => {
  const isPublic = to.meta.public === true
  const isAuthenticated = !!localStorage.getItem('access_token')

  if (!isPublic && !isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
