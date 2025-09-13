'use client';

/**
 * F1 Undercut Simulator - Backend Status Banner
 * Display connection status and backend health information
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, queryKeys } from '@/lib/api';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import {
    CheckCircle,
    XCircle,
    AlertTriangle,
    RefreshCw,
    Server,
    Wifi,
    WifiOff
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

interface BackendStatusBannerProps {
    compact?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export const BackendStatusBanner: React.FC<BackendStatusBannerProps> = ({ compact = false }) => {
    // Query backend status
    const {
        data: status,
        isLoading,
        error,
        refetch,
        isRefetching
    } = useQuery({
        queryKey: queryKeys.status,
        queryFn: () => apiClient.checkStatus(),
        refetchInterval: 30000, // Check every 30 seconds
        retry: 2,
        staleTime: 10000, // 10 seconds
    });

    // Determine connection state
    const getConnectionState = () => {
        if (isLoading && !status) return 'checking';
        if (error) return 'error';
        if (status) return 'connected';
        return 'unknown';
    };

    const connectionState = getConnectionState();

    // Render compact version
    if (compact) {
        return (
            <div className="flex items-center gap-2">
                {connectionState === 'connected' && (
                    <>
                        <Wifi className="w-4 h-4 text-green-500" />
                        <span className="text-sm text-green-600 dark:text-green-400">
                            Backend Connected
                        </span>
                    </>
                )}
                {connectionState === 'error' && (
                    <>
                        <WifiOff className="w-4 h-4 text-red-500" />
                        <span className="text-sm text-red-600 dark:text-red-400">
                            Backend Offline
                        </span>
                    </>
                )}
                {connectionState === 'checking' && (
                    <>
                        <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
                        <span className="text-sm text-blue-600 dark:text-blue-400">
                            Checking...
                        </span>
                    </>
                )}
            </div>
        );
    }

    // Full banner version
    return (
        <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <div className="container mx-auto px-4 py-3">
                {/* Connected State */}
                {connectionState === 'connected' && status && (
                    <Alert className="border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-800">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <AlertDescription className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <span className="text-green-800 dark:text-green-200 font-medium">
                                    ✅ Backend Connected
                                </span>
                                <div className="flex items-center gap-3 text-sm text-green-700 dark:text-green-300">
                                    <Badge variant="outline" className="border-green-300">
                                        <Server className="w-3 h-3 mr-1" />
                                        {status.version}
                                    </Badge>
                                    <span>API Ready</span>
                                </div>
                            </div>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => refetch()}
                                disabled={isRefetching}
                                className="text-green-600 hover:text-green-700 hover:bg-green-100 dark:hover:bg-green-900"
                            >
                                {isRefetching ? (
                                    <RefreshCw className="w-4 h-4 animate-spin" />
                                ) : (
                                    <RefreshCw className="w-4 h-4" />
                                )}
                            </Button>
                        </AlertDescription>
                    </Alert>
                )}

                {/* Error State */}
                {connectionState === 'error' && (
                    <Alert variant="destructive">
                        <XCircle className="h-4 w-4" />
                        <AlertDescription className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <span className="font-medium">
                                    ❌ Backend Disconnected
                                </span>
                                <div className="text-sm opacity-90">
                                    Cannot connect to F1 Undercut Simulator API
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => refetch()}
                                    disabled={isRefetching}
                                    className="border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-950"
                                >
                                    {isRefetching ? (
                                        <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                                    ) : (
                                        <RefreshCw className="w-4 h-4 mr-2" />
                                    )}
                                    Retry
                                </Button>
                            </div>
                        </AlertDescription>
                    </Alert>
                )}

                {/* Checking State */}
                {connectionState === 'checking' && (
                    <Alert>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        <AlertDescription>
                            <div className="flex items-center gap-4">
                                <span className="font-medium">Connecting to backend...</span>
                                <div className="text-sm text-gray-600 dark:text-gray-400">
                                    Checking F1 Undercut Simulator API status
                                </div>
                            </div>
                        </AlertDescription>
                    </Alert>
                )}

                {/* Warning for development */}
                {status && process.env.NODE_ENV === 'development' && (
                    <div className="mt-2">
                        <Alert className="border-yellow-200 bg-yellow-50 dark:bg-yellow-950 dark:border-yellow-800">
                            <AlertTriangle className="h-4 w-4 text-yellow-600" />
                            <AlertDescription className="text-yellow-800 dark:text-yellow-200">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm">
                                        🚧 Development Mode - Backend running on localhost:8000
                                    </span>
                                    <Badge variant="outline" className="border-yellow-300 text-xs">
                                        DEV
                                    </Badge>
                                </div>
                            </AlertDescription>
                        </Alert>
                    </div>
                )}
            </div>
        </div>
    );
};
