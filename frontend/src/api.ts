const API_BASE = 'http://localhost:8000/api'

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = localStorage.getItem('access_token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: getAuthHeaders(),
    ...options,
  })
  if (res.status === 401) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export const api = {
  // Auth
  async login(email: string, password: string) {
    const res = await request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('user', JSON.stringify(res))
    return res
  },
  logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  },
  getUser() {
    const data = localStorage.getItem('user')
    return data ? JSON.parse(data) : null
  },
  isAuthenticated() {
    return !!localStorage.getItem('access_token')
  },

  // Tickets
  getTickets(params: Record<string, string | number>) {
    const qs = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString()
    return request<any>(`/tickets?${qs}`)
  },
  getTicket(id: number) {
    return request<any>(`/tickets/${id}`)
  },
  updateTicket(id: number, data: Record<string, any>) {
    return request<any>(`/tickets/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },
  addMessage(ticketId: number, body: string) {
    const user = api.getUser()
    return request<any>(`/tickets/${ticketId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        body,
        sender_type: 'agent',
        sender_name: user?.name || 'Support Agent',
        sender_email: user?.email || '',
      }),
    })
  },

  // Team
  getTeamMembers() {
    return request<any[]>('/team')
  },

  // AI
  categorizeTicket(id: number) {
    return request<any>(`/ai/categorize/${id}`, { method: 'POST' })
  },
  draftResponse(id: number) {
    return request<any>(`/ai/draft/${id}`, { method: 'POST' })
  },
  enrichTicket(id: number) {
    return request<any>(`/ai/enrich/${id}`, { method: 'POST' })
  },
  translateTicket(id: number) {
    return request<any>(`/ai/translate/${id}`, { method: 'POST' })
  },
  translateText(text: string, language?: string) {
    return request<any>('/ai/translate-text', {
      method: 'POST',
      body: JSON.stringify({ text, language: language || 'auto' }),
    })
  },
  batchCategorize() {
    return request<any>('/ai/batch-categorize', { method: 'POST' })
  },

  // Users
  getUsers(params?: { role?: string; active_only?: boolean }) {
    const qs = new URLSearchParams()
    if (params?.role) qs.set('role', params.role)
    if (params?.active_only !== undefined) qs.set('active_only', String(params.active_only))
    const query = qs.toString()
    return request<any[]>(`/users${query ? '?' + query : ''}`)
  },
  getMyProfile() {
    return request<any>('/users/me')
  },
  getUserProfile(id: string) {
    return request<any>(`/users/${id}`)
  },
  createUser(data: Record<string, any>) {
    return request<any>('/users', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
  updateUser(id: string, data: Record<string, any>) {
    return request<any>(`/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },
  autoAssignTicket(ticketId: number) {
    return request<any>(`/users/auto-assign?ticket_id=${ticketId}`, {
      method: 'POST',
    })
  },

  // Stats
  getStats() {
    return request<any>('/tickets/stats')
  },
}
