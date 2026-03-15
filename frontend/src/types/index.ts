export interface TeamMember {
  id: string
  name: string
  email: string
  role: string
  is_active: boolean
}

export interface UserProfile {
  id: string
  email: string
  display_name: string
  role: 'admin' | 'support' | 'billing' | 'engineering'
  department: string | null
  phone: string | null
  avatar_url: string | null
  bio: string | null
  is_active: boolean
  max_open_tickets: number
  open_ticket_count: number
  created_at: string | null
  updated_at: string | null
}

export interface UserProfileCreate {
  email: string
  password: string
  display_name: string
  role: 'admin' | 'support' | 'billing' | 'engineering'
  department?: string
  phone?: string
  bio?: string
  max_open_tickets?: number
}

export interface UserProfileUpdate {
  display_name?: string
  role?: 'admin' | 'support' | 'billing' | 'engineering'
  department?: string
  phone?: string
  avatar_url?: string
  bio?: string
  is_active?: boolean
  max_open_tickets?: number
}

export interface AutoAssignResult {
  assigned: boolean
  assignee_id?: string
  assignee_name?: string
  role?: string
  open_tickets?: number
  message?: string
}

export interface Message {
  id: number
  ticket_id: number
  sender_type: 'customer' | 'agent' | 'system'
  sender_name: string
  sender_email: string
  body: string
  is_ai_draft: boolean
  outlook_message_id: string | null
  created_at: string
}

export interface Ticket {
  id: number
  external_id: string | null
  outlook_conversation_id: string | null
  outlook_message_id: string | null
  subject: string
  body: string
  sender_email: string
  sender_name: string
  source: string
  status: 'open' | 'in_progress' | 'waiting' | 'resolved' | 'closed'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  category: string | null
  tags: string
  language: string
  translated_body: string | null
  assignee_id: string | null
  assignee: TeamMember | null
  ai_category: string | null
  ai_summary: string | null
  ai_draft_response: string | null
  ai_confidence: number | null
  ai_suggested_assignee: string | null
  sentry_issues: string | null
  posthog_recording_url: string | null
  user_metadata: string | null
  created_at: string
  updated_at: string
  messages: Message[]
}

export interface TicketListItem {
  id: number
  external_id: string | null
  subject: string
  sender_email: string
  sender_name: string
  source: string
  status: string
  priority: string
  category: string | null
  tags: string
  language: string
  assignee_id: string | null
  assignee: TeamMember | null
  ai_category: string | null
  ai_confidence: number | null
  created_at: string
  updated_at: string
  message_count: number
}

export interface TicketListResponse {
  tickets: TicketListItem[]
  total: number
  page: number
  page_size: number
}

export interface DashboardStats {
  total_tickets: number
  open_tickets: number
  in_progress_tickets: number
  resolved_tickets: number
  unassigned_tickets: number
  avg_ai_confidence: number | null
  category_breakdown: Record<string, number>
}
