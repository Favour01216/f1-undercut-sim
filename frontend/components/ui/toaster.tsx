"use client"

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { Toast } from './toast'

interface ToastData {
    id: string
    title?: string
    description?: string
    variant?: 'default' | 'destructive' | 'success' | 'warning'
    duration?: number
}

interface ToastContextType {
    toasts: ToastData[]
    addToast: (toast: Omit<ToastData, 'id'>) => void
    removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export const useToast = () => {
    const context = useContext(ToastContext)
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider')
    }
    return context
}

interface ToastProviderProps {
    children: ReactNode
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
    const [toasts, setToasts] = useState<ToastData[]>([])

    const addToast = useCallback((toast: Omit<ToastData, 'id'>) => {
        const id = Math.random().toString(36).substr(2, 9)
        const newToast = { id, duration: 5000, ...toast }

        setToasts(prev => [...prev, newToast])

        // Auto-remove toast after duration
        setTimeout(() => {
            removeToast(id)
        }, newToast.duration)
    }, [])

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(toast => toast.id !== id))
    }, [])

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
            {children}
            <ToastContainer toasts={toasts} onRemove={removeToast} />
        </ToastContext.Provider>
    )
}

interface ToastContainerProps {
    toasts: ToastData[]
    onRemove: (id: string) => void
}

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onRemove }) => {
    if (toasts.length === 0) return null

    return (
        <div
            className="fixed top-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px]"
            aria-label="Notifications"
        >
            {toasts.map((toast) => (
                <Toast
                    key={toast.id}
                    variant={toast.variant}
                    onClose={() => onRemove(toast.id)}
                    className="mb-2 last:mb-0"
                >
                    <div>
                        {toast.title && (
                            <div className="font-semibold">{toast.title}</div>
                        )}
                        {toast.description && (
                            <div className={toast.title ? "text-sm opacity-90 mt-1" : ""}>
                                {toast.description}
                            </div>
                        )}
                    </div>
                </Toast>
            ))}
        </div>
    )
}

export { Toast }
