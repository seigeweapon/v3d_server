import { createContext, useContext, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface AuthContextProps {
  isAuthenticated: boolean
  token: string | null
  login: (token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextProps | undefined>(undefined)

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const navigate = useNavigate()
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'))

  const login = (newToken: string) => {
    localStorage.setItem('access_token', newToken)
    setToken(newToken)
    navigate('/')
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    setToken(null)
    navigate('/login')
  }

  const value = useMemo(
    () => ({
      isAuthenticated: Boolean(token),
      token,
      login,
      logout
    }),
    [token]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
