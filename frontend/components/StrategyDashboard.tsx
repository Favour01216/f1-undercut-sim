'use client';

/**
 * F1 Undercut Simulator - Strategy Dashboard
 * Production-grade dashboard with comprehensive accessibility and UX polish
 */

import React, { useState, useCallback } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { SimulationRequest, SimulationSession, generateSessionId } from '@/lib/api';
import { SimulationForm } from './SimulationForm';
import { ResultCards } from './ResultCards';
import { Heatmap } from './Heatmap';
import { HistoryTable } from './HistoryTable';
import { BackendStatusBanner } from './BackendStatusBanner';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

// Create query client instance
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 5 * 60 * 1000, // 5 minutes
            refetchOnWindowFocus: false,
            retry: 1,
        },
    },
});

interface StrategyDashboardContentProps { }

const StrategyDashboardContent: React.FC<StrategyDashboardContentProps> = () => {
    // Session management
    const [sessions, setSessions] = useState<SimulationSession[]>([]);
    const [currentRequest, setCurrentRequest] = useState<SimulationRequest | null>(null);
    const [isSessionsLoading, setIsSessionsLoading] = useState(false);

    // Handle new simulation
    const handleSimulation = useCallback((request: SimulationRequest, response: any) => {
        setIsSessionsLoading(true);

        const newSession: SimulationSession = {
            id: generateSessionId(),
            timestamp: new Date(),
            request,
            response,
        };

        // Add to sessions (keep last 5)
        setSessions((prev) => [newSession, ...prev.slice(0, 4)]);
        setCurrentRequest(request);

        // Simulate brief loading state for better UX
        setTimeout(() => setIsSessionsLoading(false), 500);
    }, []);

    // Handle session deletion
    const handleSessionDelete = useCallback((sessionId: string) => {
        setSessions((prev) => prev.filter(session => session.id !== sessionId));
    }, []);

    // Handle session replay
    const handleSessionReplay = useCallback((session: SimulationSession) => {
        setCurrentRequest(session.request);
        // Could trigger a new simulation here if desired
    }, []);

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            {/* Skip Navigation Links for Screen Readers */}
            <div className="sr-only">
                <a
                    href="#main-content"
                    className="fixed top-4 left-4 z-50 bg-blue-600 text-white px-4 py-2 rounded-md focus:not-sr-only focus:z-50"
                >
                    Skip to main content
                </a>
                <a
                    href="#simulation-form"
                    className="fixed top-4 left-4 z-50 bg-blue-600 text-white px-4 py-2 rounded-md focus:not-sr-only focus:z-50"
                >
                    Skip to simulation form
                </a>
                <a
                    href="#results-section"
                    className="fixed top-4 left-4 z-50 bg-blue-600 text-white px-4 py-2 rounded-md focus:not-sr-only focus:z-50"
                >
                    Skip to results
                </a>
            </div>

            {/* Backend Status Banner */}
            <BackendStatusBanner />

            {/* Main Dashboard */}
            <main id="main-content" className="container mx-auto px-4 py-8">
                {/* Header */}
                <header className="mb-8">
                    <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                        🏁 F1 Undercut Strategy Dashboard
                    </h1>
                    <p className="text-gray-600 dark:text-gray-300 text-lg">
                        Analyze undercut opportunities with real-time Monte Carlo simulations
                    </p>
                </header>

                {/* Main Layout - Grid for desktop, stack for mobile */}
                <div className="grid grid-cols-1 xl:grid-cols-5 gap-8">
                    {/* Left Panel - Simulation Form (2/5 width on desktop) */}
                    <section
                        className="xl:col-span-2 space-y-6"
                        aria-labelledby="form-section-title"
                    >
                        <h2 id="form-section-title" className="sr-only">
                            Simulation Configuration
                        </h2>

                        <Card id="simulation-form">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <span className="text-blue-600 dark:text-blue-400" aria-hidden="true">⚙️</span>
                                    Simulation Parameters
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <SimulationForm onSimulationComplete={handleSimulation} />
                            </CardContent>
                        </Card>

                        {/* Session History - Only show if we have sessions */}
                        {(sessions.length > 0 || isSessionsLoading) && (
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <span className="text-purple-600 dark:text-purple-400" aria-hidden="true">📊</span>
                                        Recent Simulations
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <HistoryTable
                                        sessions={sessions}
                                        onSessionDelete={handleSessionDelete}
                                        onSessionReplay={handleSessionReplay}
                                        isLoading={isSessionsLoading}
                                    />
                                </CardContent>
                            </Card>
                        )}
                    </section>

                    {/* Right Panel - Results and Analysis (3/5 width on desktop) */}
                    <section
                        className="xl:col-span-3 space-y-6"
                        aria-labelledby="results-section-title"
                    >
                        <h2 id="results-section-title" className="sr-only">
                            Simulation Results and Analysis
                        </h2>

                        {/* Results Cards */}
                        <Card id="results-section">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <span className="text-green-600 dark:text-green-400" aria-hidden="true">🎯</span>
                                    Simulation Results
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ResultCards currentRequest={currentRequest} />
                            </CardContent>
                        </Card>

                        {/* Heatmap Analysis */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <span className="text-orange-600 dark:text-orange-400" aria-hidden="true">🔥</span>
                                    Gap-Compound Analysis
                                </CardTitle>
                                <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                                    Explore undercut probability across different gaps and tire compounds
                                </p>
                            </CardHeader>
                            <CardContent>
                                <Heatmap currentRequest={currentRequest} />
                            </CardContent>
                        </Card>
                    </section>
                </div>

                {/* Footer */}
                <footer className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
                    <div className="text-center text-gray-500 dark:text-gray-400">
                        <p className="mb-2">
                            F1 Undercut Simulator • Built with Next.js, FastAPI, and Formula 1 data
                        </p>
                        <p className="text-sm">
                            For educational and analysis purposes. Real F1 strategy involves many more variables.
                        </p>

                        {/* Accessibility Statement */}
                        <details className="mt-4 text-left max-w-2xl mx-auto">
                            <summary className="cursor-pointer text-sm font-medium hover:text-gray-700 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded">
                                Accessibility Features
                            </summary>
                            <div className="mt-2 text-xs text-gray-400 dark:text-gray-500 space-y-2">
                                <p>This dashboard is designed with accessibility in mind:</p>
                                <ul className="list-disc list-inside space-y-1 ml-4">
                                    <li>Full keyboard navigation support</li>
                                    <li>Screen reader compatible with ARIA labels and live regions</li>
                                    <li>High contrast colors meeting WCAG AA standards</li>
                                    <li>Skip navigation links for efficient browsing</li>
                                    <li>Alternative text and descriptions for all visual elements</li>
                                    <li>Structured headings and semantic HTML</li>
                                </ul>
                                <p>
                                    If you encounter any accessibility issues, please report them to our development team.
                                </p>
                            </div>
                        </details>
                    </div>
                </footer>
            </main>
        </div>
    );
};

/**
 * Main Strategy Dashboard Component with React Query Provider
 */
export const StrategyDashboard: React.FC = () => {
    return (
        <QueryClientProvider client={queryClient}>
            <StrategyDashboardContent />
            {process.env.NODE_ENV === 'development' && (
                <ReactQueryDevtools initialIsOpen={false} />
            )}
        </QueryClientProvider>
    );
};

export default StrategyDashboard;