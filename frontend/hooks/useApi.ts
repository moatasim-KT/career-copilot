import { useState, useEffect } from 'react'
import { ApiResponse } from '@/types'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

interface UseApiOptions {
  immediate?: boolean
}

export function useApi<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  options: UseApiOptions = { immediate: true }
) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  })

  const execute = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))
    
    try {
      const response = await apiCall()
      
      if (response.success && response.data) {
        setState({
          data: response.data,
          loading: false,
          error: null,
        })
      } else {
        setState({
          data: null,
          loading: false,
          error: response.error || 'Unknown error occurred',
        })
      }
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      })
    }
  }

  useEffect(() => {
    if (options.immediate) {
      execute()
    }
  }, [])

  return {
    ...state,
    execute,
    refetch: execute,
  }
}