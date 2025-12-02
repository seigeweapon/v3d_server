import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import 'antd/dist/reset.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5分钟内数据被认为是新鲜的，不会重新请求
      cacheTime: 10 * 60 * 1000, // 缓存保留10分钟
      refetchOnMount: false, // 如果数据是新鲜的，不重新请求
      refetchOnWindowFocus: false, // 窗口聚焦时不重新请求
      retry: 1, // 失败时只重试1次
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)
