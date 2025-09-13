import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { X, CheckCircle, AlertTriangle, XCircle, Info } from "lucide-react"
import { cn } from "@/lib/utils"

const toastVariants = cva(
    "group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-6 pr-8 shadow-lg transition-all data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full",
    {
        variants: {
            variant: {
                default: "border-gray-200 bg-white text-gray-900 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100",
                destructive:
                    "destructive group border-red-200 bg-red-50 text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-100",
                success:
                    "border-green-200 bg-green-50 text-green-900 dark:border-green-800 dark:bg-green-950 dark:text-green-100",
                warning:
                    "border-yellow-200 bg-yellow-50 text-yellow-900 dark:border-yellow-800 dark:bg-yellow-950 dark:text-yellow-100",
            },
        },
        defaultVariants: {
            variant: "default",
        },
    }
)

export interface ToastProps
    extends React.ComponentPropsWithoutRef<"div">,
    VariantProps<typeof toastVariants> {
    onClose?: () => void
}

const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
    ({ className, variant, onClose, children, ...props }, ref) => {
        const Icon = variant === 'success' ? CheckCircle :
            variant === 'destructive' ? XCircle :
                variant === 'warning' ? AlertTriangle :
                    Info

        return (
            <div
                ref={ref}
                className={cn(toastVariants({ variant }), className)}
                role="alert"
                aria-live="polite"
                aria-atomic="true"
                {...props}
            >
                <div className="flex items-center space-x-3">
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    <div className="flex-1">{children}</div>
                </div>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="absolute right-2 top-2 rounded-md p-1 text-current/50 opacity-0 transition-opacity hover:text-current/75 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-current group-hover:opacity-100"
                        aria-label="Close notification"
                    >
                        <X className="h-4 w-4" />
                    </button>
                )}
            </div>
        )
    }
)
Toast.displayName = "Toast"

export { Toast, toastVariants }
