'use client';

/**
 * F1 Undercut Simulator - History Table
 * Accessible session history with enhanced UX and loading states
 */

import React, { useState } from 'react';
import { SimulationSession, formatProbability, formatSeconds } from '@/lib/api';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Skeleton } from './ui/skeleton';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from './ui/table';
import {
    Clock,
    TrendingUp,
    MoreHorizontal,
    Trash2,
    Copy,
    ExternalLink,
    History,
    CheckCircle
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

interface HistoryTableProps {
    sessions: SimulationSession[];
    onSessionDelete?: (sessionId: string) => void;
    onSessionReplay?: (session: SimulationSession) => void;
    isLoading?: boolean;
}

interface SessionRowProps {
    session: SimulationSession;
    onDelete?: (sessionId: string) => void;
    onReplay?: (session: SimulationSession) => void;
}

// ============================================================================
// Helper Functions
// ============================================================================

const getSuccessVariant = (probability: number): 'default' | 'secondary' | 'destructive' => {
    if (probability >= 0.6) return 'default';   // Green for high success
    if (probability >= 0.4) return 'secondary'; // Gray for uncertain
    return 'destructive';                       // Red for likely failure
};

const formatTimestamp = (date: Date): string => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
};

const copySessionToClipboard = async (session: SimulationSession) => {
    const text = `F1 Undercut Simulation Result:
GP: ${session.request.gp.toUpperCase()} ${session.request.year}
Drivers: ${session.request.driver_a} vs ${session.request.driver_b}
Compound: ${session.request.compound_a}
Lap: ${session.request.lap_now}
Success Probability: ${formatProbability(session.response.p_undercut)}
Pit Loss: ${formatSeconds(session.response.pitLoss_s)}
Outlap Delta: ${formatSeconds(session.response.outLapDelta_s)}`;

    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        console.warn('Failed to copy to clipboard:', err);
        return false;
    }
};

// ============================================================================
// Components
// ============================================================================

const TableSkeleton: React.FC = () => (
    <div
        className="space-y-3"
        role="status"
        aria-label="Loading simulation history"
        aria-live="polite"
    >
        {/* Header skeleton */}
        <div className="flex items-center justify-between mb-4">
            <div>
                <Skeleton className="h-6 w-40 mb-2" />
                <Skeleton className="h-4 w-32" />
            </div>
            <Skeleton className="h-8 w-20" />
        </div>

        {/* Table skeleton */}
        <Card>
            <CardContent className="p-0">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b">
                                {['Time', 'Race', 'Drivers', 'Success', 'Pit Loss', 'Outlap', 'Actions'].map((header, i) => (
                                    <th key={i} className="h-12 px-4 text-left">
                                        <Skeleton className="h-4 w-16" />
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {Array.from({ length: 3 }).map((_, i) => (
                                <tr key={i} className="border-b">
                                    <td className="p-4"><Skeleton className="h-4 w-12" /></td>
                                    <td className="p-4"><Skeleton className="h-4 w-20" /></td>
                                    <td className="p-4"><Skeleton className="h-4 w-24" /></td>
                                    <td className="p-4"><Skeleton className="h-6 w-16 rounded-full" /></td>
                                    <td className="p-4"><Skeleton className="h-4 w-12" /></td>
                                    <td className="p-4"><Skeleton className="h-4 w-12" /></td>
                                    <td className="p-4">
                                        <div className="flex gap-1">
                                            <Skeleton className="h-8 w-8" />
                                            <Skeleton className="h-8 w-8" />
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </CardContent>
        </Card>
    </div>
);

const SessionRow: React.FC<SessionRowProps> = ({ session, onDelete, onReplay }) => {
    const [showActions, setShowActions] = useState(false);
    const [copying, setCopying] = useState(false);

    const handleCopy = async () => {
        setCopying(true);
        const success = await copySessionToClipboard(session);
        if (success) {
            // Could add a toast notification here
        }
        setTimeout(() => setCopying(false), 1000);
    };

    const handleKeyDown = (event: React.KeyboardEvent, action: () => void) => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            action();
        }
    };

    return (
        <TableRow
            className="group hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors focus-within:bg-gray-50 dark:focus-within:bg-gray-800"
            onMouseEnter={() => setShowActions(true)}
            onMouseLeave={() => setShowActions(false)}
            onFocus={() => setShowActions(true)}
            onBlur={(e) => {
                // Only hide actions if focus is leaving the entire row
                if (!e.currentTarget.contains(e.relatedTarget as Node)) {
                    setShowActions(false);
                }
            }}
        >
            {/* Timestamp */}
            <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" aria-hidden="true" />
                    <time
                        dateTime={session.timestamp.toISOString()}
                        title={session.timestamp.toLocaleString()}
                        className="text-sm"
                    >
                        {formatTimestamp(session.timestamp)}
                    </time>
                </div>
            </TableCell>

            {/* Race Info */}
            <TableCell>
                <div className="space-y-1">
                    <div className="font-medium text-sm">
                        {session.request.gp.toUpperCase()} {session.request.year}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                        Lap {session.request.lap_now}
                    </div>
                </div>
            </TableCell>

            {/* Drivers */}
            <TableCell>
                <div className="space-y-1">
                    <div className="text-sm">
                        <span className="font-medium">{session.request.driver_a}</span>
                        <span className="text-gray-400 mx-1" aria-label="versus">vs</span>
                        <span className="font-medium">{session.request.driver_b}</span>
                    </div>
                    <Badge
                        variant="outline"
                        className="text-xs px-2 py-0"
                        aria-label={`Tire compound: ${session.request.compound_a}`}
                    >
                        {session.request.compound_a}
                    </Badge>
                </div>
            </TableCell>

            {/* Success Probability */}
            <TableCell>
                <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-gray-400" aria-hidden="true" />
                    <Badge
                        variant={getSuccessVariant(session.response.p_undercut)}
                        aria-label={`Success probability: ${formatProbability(session.response.p_undercut)}`}
                    >
                        {formatProbability(session.response.p_undercut)}
                    </Badge>
                </div>
            </TableCell>

            {/* Pit Loss */}
            <TableCell>
                <span
                    className="text-sm font-mono"
                    aria-label={`Pit loss time: ${formatSeconds(session.response.pitLoss_s)}`}
                >
                    {formatSeconds(session.response.pitLoss_s)}
                </span>
            </TableCell>

            {/* Outlap Delta */}
            <TableCell>
                <span
                    className="text-sm font-mono"
                    aria-label={`Outlap delta: ${formatSeconds(session.response.outLapDelta_s)}`}
                >
                    {formatSeconds(session.response.outLapDelta_s)}
                </span>
            </TableCell>

            {/* Actions */}
            <TableCell>
                <div
                    className="flex items-center justify-end gap-1"
                    role="group"
                    aria-label="Session actions"
                >
                    {(showActions || window.innerWidth <= 768) && (
                        <>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleCopy}
                                onKeyDown={(e) => handleKeyDown(e, handleCopy)}
                                className="h-8 w-8 p-0 focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                                title="Copy simulation results to clipboard"
                                aria-label="Copy simulation results"
                                disabled={copying}
                            >
                                {copying ? (
                                    <CheckCircle className="w-3 h-3 text-green-600" />
                                ) : (
                                    <Copy className="w-3 h-3" />
                                )}
                            </Button>

                            {onReplay && (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => onReplay(session)}
                                    onKeyDown={(e) => handleKeyDown(e, () => onReplay(session))}
                                    className="h-8 w-8 p-0 focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                                    title="Replay this simulation with same parameters"
                                    aria-label="Replay simulation"
                                >
                                    <ExternalLink className="w-3 h-3" />
                                </Button>
                            )}

                            {onDelete && (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => onDelete(session.id)}
                                    onKeyDown={(e) => handleKeyDown(e, () => onDelete(session.id))}
                                    className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950 focus:ring-2 focus:ring-red-500 focus:ring-offset-1"
                                    title="Remove simulation from history"
                                    aria-label="Remove from history"
                                >
                                    <Trash2 className="w-3 h-3" />
                                </Button>
                            )}
                        </>
                    )}
                </div>
            </TableCell>
        </TableRow>
    );
};

const EmptyState: React.FC = () => (
    <div
        className="text-center py-12"
        role="status"
        aria-live="polite"
    >
        <div
            className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4"
            aria-hidden="true"
        >
            <History className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No simulation history
        </h3>
        <p className="text-gray-500 dark:text-gray-400 mb-4">
            Your recent simulations will appear here once you start running undercut analyses.
        </p>
        <p className="text-sm text-gray-400 dark:text-gray-500">
            Session history helps you compare different scenarios and track your analysis progress.
        </p>
    </div>
);

// ============================================================================
// Main Component
// ============================================================================

export const HistoryTable: React.FC<HistoryTableProps> = ({
    sessions,
    onSessionDelete,
    onSessionReplay,
    isLoading = false
}) => {
    if (isLoading) {
        return <TableSkeleton />;
    }

    if (!sessions || sessions.length === 0) {
        return <EmptyState />;
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white text-lg">
                        Simulation History
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        {sessions.length} recent simulation{sessions.length !== 1 ? 's' : ''} •
                        Last 5 results are preserved
                    </p>
                </div>

                {sessions.length > 0 && onSessionDelete && (
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                            if (window.confirm(`Clear all ${sessions.length} simulation sessions from history?`)) {
                                sessions.forEach(s => onSessionDelete(s.id));
                            }
                        }}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950 focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                        aria-label="Clear all simulation history"
                    >
                        <Trash2 className="w-4 h-4 mr-2" aria-hidden="true" />
                        Clear All
                    </Button>
                )}
            </div>

            {/* Table */}
            <Card>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <Table
                            role="table"
                            aria-label="Simulation history table"
                            aria-describedby="history-description"
                        >
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-24" scope="col">Time</TableHead>
                                    <TableHead className="w-28" scope="col">Race</TableHead>
                                    <TableHead className="w-32" scope="col">Drivers</TableHead>
                                    <TableHead className="w-24" scope="col">Success Rate</TableHead>
                                    <TableHead className="w-20" scope="col">Pit Loss</TableHead>
                                    <TableHead className="w-20" scope="col">Outlap</TableHead>
                                    <TableHead className="w-20 text-right" scope="col">
                                        <span className="sr-only">Actions</span>
                                        Actions
                                    </TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {sessions.map((session) => (
                                    <SessionRow
                                        key={session.id}
                                        session={session}
                                        onDelete={onSessionDelete}
                                        onReplay={onSessionReplay}
                                    />
                                ))}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>

            {/* Screen reader description */}
            <p id="history-description" className="sr-only">
                Table showing simulation history with columns for timestamp, race details, driver matchups,
                success probability, pit loss time, outlap delta, and available actions like copy and delete.
            </p>

            {/* Keyboard Instructions */}
            <div className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                <p className="font-medium mb-1">Keyboard Navigation:</p>
                <ul className="space-y-1">
                    <li>• Use Tab to navigate through table rows and action buttons</li>
                    <li>• Press Enter or Space to activate buttons</li>
                    <li>• Hover over rows to reveal action buttons on desktop</li>
                    <li>• Action buttons are always visible on mobile devices</li>
                </ul>
            </div>
        </div>
    );
};