'use client';

/**
 * F1 Undercut Simulator - Result Cards
 * Display simulation results with accessibility and UX enhancements
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    SimulationRequest,
    apiClient,
    queryKeys,
    formatProbability,
    formatSeconds,
    getSuccessLikelihood
} from '@/lib/api';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Skeleton } from './ui/skeleton';
import { Alert, AlertDescription } from './ui/alert';
import {
    TrendingUp,
    Timer,
    Zap,
    Target,
    AlertTriangle,
    CheckCircle,
    XCircle,
    HelpCircle,
    Clock,
    RefreshCw
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

interface ResultCardsProps {
    currentRequest: SimulationRequest | null;
}

interface StatCardProps {
    title: string;
    value: string;
    subtitle?: string;
    icon: React.ReactNode;
    variant?: 'default' | 'success' | 'danger' | 'warning';
    isLoading?: boolean;
    ariaLabel?: string;
    description?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

const useRelativeTime = (timestamp?: Date) => {
    const [relativeTime, setRelativeTime] = useState<string>('');

    useEffect(() => {
        if (!timestamp) {
            setRelativeTime('');
            return;
        }

        const updateRelativeTime = () => {
            const now = new Date();
            const diffMs = now.getTime() - timestamp.getTime();
            const diffSeconds = Math.floor(diffMs / 1000);
            const diffMinutes = Math.floor(diffSeconds / 60);
            const diffHours = Math.floor(diffMinutes / 60);

            if (diffSeconds < 10) {
                setRelativeTime('just now');
            } else if (diffSeconds < 60) {
                setRelativeTime(`${diffSeconds}s ago`);
            } else if (diffMinutes < 60) {
                setRelativeTime(`${diffMinutes}m ago`);
            } else if (diffHours < 24) {
                setRelativeTime(`${diffHours}h ago`);
            } else {
                setRelativeTime(`${Math.floor(diffHours / 24)}d ago`);
            }
        };

        updateRelativeTime();
        const interval = setInterval(updateRelativeTime, 10000); // Update every 10 seconds

        return () => clearInterval(interval);
    }, [timestamp]);

    return relativeTime;
};

// ============================================================================
// Components
// ============================================================================

const StatCard: React.FC<StatCardProps> = ({
    title,
    value,
    subtitle,
    icon,
    variant = 'default',
    isLoading = false,
    ariaLabel,
    description
}) => {
    const variantStyles = {
        default: 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800',
        success: 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950',
        danger: 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950',
        warning: 'border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-950',
    };

    const iconStyles = {
        default: 'text-gray-600 dark:text-gray-400',
        success: 'text-green-600 dark:text-green-400',
        danger: 'text-red-600 dark:text-red-400',
        warning: 'text-yellow-600 dark:text-yellow-400',
    };

    return (
        <Card className={`transition-all duration-200 ${variantStyles[variant]}`}>
            <CardContent className="p-6">
                <div
                    className="flex items-center justify-between"
                    role="img"
                    aria-label={ariaLabel || `${title}: ${isLoading ? 'Loading' : value}`}
                >
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                            <div className={iconStyles[variant]} aria-hidden="true">{icon}</div>
                            <h3 className="font-medium text-sm text-gray-600 dark:text-gray-400 uppercase tracking-wide">
                                {title}
                            </h3>
                        </div>

                        {isLoading ? (
                            <Skeleton className="h-8 w-24 mb-1" />
                        ) : (
                            <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                                {value}
                            </p>
                        )}

                        {subtitle && (
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                {subtitle}
                            </p>
                        )}

                        {description && (
                            <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                                {description}
                            </p>
                        )}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

const EmptyState: React.FC = () => (
    <div className="text-center py-12" role="status" aria-live="polite">
        <div
            className="mx-auto w-24 h-24 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4"
            aria-hidden="true"
        >
            <Target className="w-10 h-10 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No simulation results yet
        </h3>
        <p className="text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
            Configure your simulation parameters and click &quot;Run Undercut Simulation&quot; to see results here.
        </p>
    </div>
);

const LoadingState: React.FC = () => (
    <div className="space-y-6" role="status" aria-live="polite" aria-label="Simulation in progress">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
                title="Undercut Probability"
                value=""
                icon={<TrendingUp className="w-5 h-5" />}
                isLoading={true}
                ariaLabel="Undercut probability loading"
            />
            <StatCard
                title="Pit Loss Time"
                value=""
                icon={<Timer className="w-5 h-5" />}
                isLoading={true}
                ariaLabel="Pit loss time loading"
            />
            <StatCard
                title="Outlap Delta"
                value=""
                icon={<Zap className="w-5 h-5" />}
                isLoading={true}
                ariaLabel="Outlap delta loading"
            />
            <StatCard
                title="Average Margin"
                value=""
                icon={<Target className="w-5 h-5" />}
                isLoading={true}
                ariaLabel="Average margin loading"
            />
        </div>

        <div className="flex justify-center">
            <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400" role="status">
                <RefreshCw className="animate-spin rounded-full h-4 w-4" aria-hidden="true" />
                <span>Running Monte Carlo simulation...</span>
            </div>
        </div>
    </div>
);

// ============================================================================
// Main Component
// ============================================================================

export const ResultCards: React.FC<ResultCardsProps> = ({ currentRequest }) => {
    const [lastUpdated, setLastUpdated] = useState<Date>();
    const relativeTime = useRelativeTime(lastUpdated);

    // Query for simulation results
    const { data: result, isLoading, error, dataUpdatedAt } = useQuery({
        queryKey: currentRequest ? queryKeys.simulation(currentRequest) : [],
        queryFn: () => currentRequest ? apiClient.simulate(currentRequest) : null,
        enabled: !!currentRequest,
        staleTime: 30 * 1000, // 30 seconds
    });

    // Update timestamp when data changes
    useEffect(() => {
        if (dataUpdatedAt && result) {
            setLastUpdated(new Date(dataUpdatedAt));
        }
    }, [dataUpdatedAt, result]);

    // Error state
    if (error) {
        return (
            <Alert variant="destructive" role="alert" aria-live="assertive">
                <AlertTriangle className="h-4 w-4" aria-hidden="true" />
                <AlertDescription>
                    <strong>Simulation Error:</strong> {error.message}
                    <br />
                    <small className="text-red-600 dark:text-red-400 mt-1 block">
                        Please check your parameters and try again, or contact support if the problem persists.
                    </small>
                </AlertDescription>
            </Alert>
        );
    }

    // Loading state
    if (isLoading && currentRequest) {
        return <LoadingState />;
    }

    // Empty state
    if (!currentRequest || !result) {
        return <EmptyState />;
    }

    // Calculate derived values
    const likelihood = getSuccessLikelihood(result.p_undercut);
    const avgMargin = result.avgMargin_s ?? (
        (result.pitLoss_s || 0) + (result.outLapDelta_s || 0) - 5
    ); // Rough estimate

    return (
        <div className="space-y-6">
            {/* Last Updated Timestamp */}
            {lastUpdated && relativeTime && (
                <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                    <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" aria-hidden="true" />
                        <span>Last updated: {relativeTime}</span>
                    </div>
                    <time
                        dateTime={lastUpdated.toISOString()}
                        className="text-xs"
                        title={lastUpdated.toLocaleString()}
                    >
                        {lastUpdated.toLocaleTimeString()}
                    </time>
                </div>
            )}

            {/* Primary Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Undercut Probability - Main KPI */}
                <div className="md:col-span-2 lg:col-span-1">
                    <StatCard
                        title="Undercut Probability"
                        value={formatProbability(result.p_undercut)}
                        subtitle={likelihood.label}
                        icon={<TrendingUp className="w-5 h-5" />}
                        variant={likelihood.variant}
                        ariaLabel={`Undercut success probability: ${formatProbability(result.p_undercut)}, ${likelihood.label}`}
                        description="Based on Monte Carlo simulation of pit stop scenarios"
                    />
                </div>

                {/* Pit Loss Time */}
                <StatCard
                    title="Pit Loss Time"
                    value={formatSeconds(result.pitLoss_s)}
                    subtitle="Time lost in pit lane"
                    icon={<Timer className="w-5 h-5" />}
                    ariaLabel={`Pit loss time: ${formatSeconds(result.pitLoss_s)}`}
                    description="Includes pit lane speed limit and service time"
                />

                {/* Outlap Delta */}
                <StatCard
                    title="Outlap Delta"
                    value={formatSeconds(result.outLapDelta_s)}
                    subtitle="Cold tire penalty"
                    icon={<Zap className="w-5 h-5" />}
                    ariaLabel={`Outlap penalty: ${formatSeconds(result.outLapDelta_s)}`}
                    description="Time lost on first lap with fresh tires"
                />

                {/* Average Margin */}
                <StatCard
                    title="Average Margin"
                    value={formatSeconds(Math.abs(avgMargin))}
                    subtitle={avgMargin > 0 ? "Advantage" : "Deficit"}
                    icon={<Target className="w-5 h-5" />}
                    variant={avgMargin > 0 ? 'success' : 'danger'}
                    ariaLabel={`Average margin: ${formatSeconds(Math.abs(avgMargin))} ${avgMargin > 0 ? 'advantage' : 'deficit'}`}
                    description="Expected time difference after undercut attempt"
                />
            </div>

            {/* Success Likelihood Banner */}
            <Card
                className={`border-2 ${likelihood.variant === 'success' ? 'border-green-500 bg-green-50 dark:bg-green-950' :
                    likelihood.variant === 'danger' ? 'border-red-500 bg-red-50 dark:bg-red-950' :
                        'border-yellow-500 bg-yellow-50 dark:bg-yellow-950'}`}
                role="status"
                aria-live="polite"
            >
                <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            {likelihood.variant === 'success' && <CheckCircle className="w-6 h-6 text-green-600" aria-hidden="true" />}
                            {likelihood.variant === 'danger' && <XCircle className="w-6 h-6 text-red-600" aria-hidden="true" />}
                            {likelihood.variant === 'warning' && <HelpCircle className="w-6 h-6 text-yellow-600" aria-hidden="true" />}

                            <div>
                                <h3 className="font-semibold text-lg">
                                    {likelihood.label}
                                </h3>
                                <p className="text-sm opacity-80">
                                    Based on {currentRequest.samples || 1000} Monte Carlo simulations
                                </p>
                            </div>
                        </div>

                        <Badge
                            variant={likelihood.variant === 'success' ? 'default' :
                                likelihood.variant === 'danger' ? 'destructive' : 'secondary'}
                            className="text-sm px-3 py-1"
                        >
                            {formatProbability(result.p_undercut)}
                        </Badge>
                    </div>
                </CardContent>
            </Card>

            {/* Assumptions & Details */}
            {result.assumptions && (
                <Card>
                    <CardContent className="p-6">
                        <h3 className="font-semibold mb-4 text-gray-900 dark:text-white">
                            Simulation Assumptions
                        </h3>
                        <div
                            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 text-sm"
                            role="table"
                            aria-label="Simulation parameters and assumptions"
                        >
                            <div role="cell">
                                <span className="text-gray-500 dark:text-gray-400 block" id="gap-label">Current Gap</span>
                                <span className="font-medium" aria-describedby="gap-label">
                                    {formatSeconds(result.assumptions.gap_s)}
                                </span>
                            </div>
                            <div role="cell">
                                <span className="text-gray-500 dark:text-gray-400 block" id="tyre-age-label">Driver B Tire Age</span>
                                <span className="font-medium" aria-describedby="tyre-age-label">
                                    {result.assumptions.tyre_age_b} laps
                                </span>
                            </div>
                            <div role="cell">
                                <span className="text-gray-500 dark:text-gray-400 block" id="deg-model-label">Degradation Model</span>
                                <span className="font-medium capitalize" aria-describedby="deg-model-label">
                                    {result.assumptions.degradation_model}
                                </span>
                            </div>
                            <div role="cell">
                                <span className="text-gray-500 dark:text-gray-400 block" id="pit-model-label">Pit Model</span>
                                <span className="font-medium capitalize" aria-describedby="pit-model-label">
                                    {result.assumptions.pit_model}
                                </span>
                            </div>
                            <div role="cell">
                                <span className="text-gray-500 dark:text-gray-400 block" id="outlap-model-label">Outlap Model</span>
                                <span className="font-medium capitalize" aria-describedby="outlap-model-label">
                                    {result.assumptions.outlap_model}
                                </span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};