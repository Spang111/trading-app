export type AuthUser = {
  id: number
  username: string
  email: string
  wallet_address: string | null
  role: string
  status: string
  email_verified: boolean
  created_at: string
  updated_at: string
}

export const AUTH_TOKEN_STORAGE_KEY = "ai-trading-access-token"
