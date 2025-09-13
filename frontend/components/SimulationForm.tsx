'use client';

/**
 * F1 Undercut Simulator - Simulation Form
 * Comprehensive form for undercut simulation parameters with full accessibility
 */

import React, { useState, useId } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
    SimulationRequest,
    SimulationResponse,
    apiClient,
    validateSimulationRequest
} from '@/lib/api';
import { useToast } from '@/components/ui/toaster';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Label } from './ui/label';
import { Card, CardContent } from './ui/card';
import { Loader2, Play, AlertTriangle, Info } from 'lucide-react';

// ============================================================================
// Form Schema & Validation
// ============================================================================

const simulationSchema = z.object({
    gp: z.string().min(1, 'Grand Prix is required'),
    year: z.number().min(2020).max(2030),
    driver_a: z.string().min(1, 'Driver A is required'),
    driver_b: z.string().min(1, 'Driver B is required'),
    compound_a: z.enum(['SOFT', 'MEDIUM', 'HARD']),
    lap_now: z.number().min(1).max(80),
    samples: z.number().min(100).max(10000).optional(),
});

type SimulationFormData = z.infer<typeof simulationSchema>;

// ============================================================================
// Constants
// ============================================================================

const GRAND_PRIX_OPTIONS = [
    { value: 'bahrain', label: '🇧🇭 Bahrain International Circuit' },
    { value: 'imola', label: '🇮🇹 Autodromo Enzo e Dino Ferrari (Imola)' },
    { value: 'monza', label: '🇮🇹 Autodromo Nazionale Monza' },
];

const YEAR_OPTIONS = [
    { value: 2024, label: '2024 Season' },
    { value: 2023, label: '2023 Season' },
];

const DRIVER_OPTIONS = [
    { value: 'VER', label: '🏆 Max Verstappen (VER) - Red Bull Racing' },
    { value: 'HAM', label: '🏆 Lewis Hamilton (HAM) - Mercedes' },
    { value: 'RUS', label: '🏎️ George Russell (RUS) - Mercedes' },
    { value: 'LEC', label: '🏎️ Charles Leclerc (LEC) - Ferrari' },
    { value: 'SAI', label: '🏎️ Carlos Sainz (SAI) - Ferrari' },
    { value: 'NOR', label: '🏎️ Lando Norris (NOR) - McLaren' },
    { value: 'PIA', label: '🏎️ Oscar Piastri (PIA) - McLaren' },
    { value: 'ALO', label: '🏎️ Fernando Alonso (ALO) - Aston Martin' },
    { value: 'STR', label: '🏎️ Lance Stroll (STR) - Aston Martin' },
    { value: 'PER', label: '🏎️ Sergio Perez (PER) - Red Bull Racing' },
];

const COMPOUND_OPTIONS = [
    { value: 'SOFT', label: '🔴 Soft Compound', description: 'Fastest degradation, maximum grip' },
    { value: 'MEDIUM', label: '🟡 Medium Compound', description: 'Balanced performance and durability' },
    { value: 'HARD', label: '⚪ Hard Compound', description: 'Longest lasting, slowest lap times' },
];

// ============================================================================
// Component
// ============================================================================

interface SimulationFormProps {
    onSimulationComplete: (request: SimulationRequest, response: SimulationResponse) => void;
}

export const SimulationForm: React.FC<SimulationFormProps> = ({ onSimulationComplete }) => {
    const [customGap, setCustomGap] = useState<number>(5.0);
    const { addToast } = useToast();

    // Generate unique IDs for form fields
    const formId = useId();
    const gpId = `${formId}-gp`;
    const yearId = `${formId}-year`;
    const driverAId = `${formId}-driver-a`;
    const driverBId = `${formId}-driver-b`;
    const compoundId = `${formId}-compound`;
    const lapId = `${formId}-lap`;
    const samplesId = `${formId}-samples`;
    const gapId = `${formId}-gap`;

    // Form setup
    const form = useForm<SimulationFormData>({
        resolver: zodResolver(simulationSchema),
        defaultValues: {
            gp: 'bahrain',
            year: 2024,
            driver_a: 'VER',
            driver_b: 'HAM',
            compound_a: 'SOFT',
            lap_now: 25,
            samples: 1000,
        },
    });

    // Mutation for simulation
    const simulationMutation = useMutation({
        mutationFn: async (data: SimulationFormData) => {
            const request: SimulationRequest = {
                ...data,
                // For demo purposes, we'll use the custom gap
                // In a real implementation, this might come from live timing data
            };

            const response = await apiClient.simulate(request);

            // Validate response structure
            if (!response || typeof response.p_undercut === 'undefined') {
                throw new Error('Invalid simulation response received');
            }

            return { request, response };
        },
        onSuccess: ({ request, response }) => {
            onSimulationComplete(request, response);
            addToast({
                title: 'Simulation Complete',
                description: `Successfully analyzed ${request.driver_a} vs ${request.driver_b} undercut scenario`,
                variant: 'success',
            });
        },
        onError: (error) => {
            addToast({
                title: 'Simulation Failed',
                description: error.message || 'An unexpected error occurred during simulation',
                variant: 'destructive',
                duration: 8000,
            });
        },
    });

    // Form submission
    const onSubmit = (data: SimulationFormData) => {
        // Validate request
        const errors = validateSimulationRequest(data);
        if (errors.length > 0) {
            // Set form errors
            errors.forEach((error) => {
                form.setError('root', { message: error });
            });
            return;
        }

        simulationMutation.mutate(data);
    };

    return (
        <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-6"
            aria-labelledby="simulation-form-title"
            role="form"
            noValidate
        >
            {/* Screen reader heading */}
            <h2 id="simulation-form-title" className="sr-only">
                F1 Undercut Simulation Configuration Form
            </h2>

            {/* Race Configuration */}
            <Card>
                <CardContent className="pt-6">
                    <fieldset className="space-y-4">
                        <legend className="font-semibold text-lg text-gray-900 dark:text-white mb-4">
                            Race Configuration
                        </legend>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Grand Prix */}
                            <div className="space-y-2">
                                <Label htmlFor={gpId} className="text-base font-medium">
                                    Grand Prix Circuit
                                    <span className="text-red-500 ml-1" aria-label="required">*</span>
                                </Label>
                                <Select
                                    value={form.watch('gp')}
                                    onValueChange={(value) => form.setValue('gp', value)}
                                    required
                                    aria-describedby={`${gpId}-description`}
                                >
                                    <SelectTrigger
                                        id={gpId}
                                        className="w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        aria-label="Select Grand Prix circuit"
                                    >
                                        <SelectValue placeholder="Select Grand Prix circuit" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {GRAND_PRIX_OPTIONS.map((option) => (
                                            <SelectItem key={option.value} value={option.value}>
                                                {option.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p id={`${gpId}-description`} className="text-sm text-gray-600 dark:text-gray-400">
                                    Choose the F1 circuit for simulation analysis
                                </p>
                            </div>

                            {/* Year */}
                            <div className="space-y-2">
                                <Label htmlFor={yearId} className="text-base font-medium">
                                    Racing Season
                                    <span className="text-red-500 ml-1" aria-label="required">*</span>
                                </Label>
                                <Select
                                    value={form.watch('year').toString()}
                                    onValueChange={(value) => form.setValue('year', parseInt(value))}
                                    required
                                    aria-describedby={`${yearId}-description`}
                                >
                                    <SelectTrigger
                                        id={yearId}
                                        className="w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        aria-label="Select racing season year"
                                    >
                                        <SelectValue placeholder="Select racing season" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {YEAR_OPTIONS.map((option) => (
                                            <SelectItem key={option.value} value={option.value.toString()}>
                                                {option.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p id={`${yearId}-description`} className="text-sm text-gray-600 dark:text-gray-400">
                                    F1 season year for historical data analysis
                                </p>
                            </div>
                        </div>
                    </fieldset>
                </CardContent>
            </Card>

            {/* Driver Configuration */}
            <Card>
                <CardContent className="pt-6">
                    <fieldset className="space-y-4">
                        <legend className="font-semibold text-lg text-gray-900 dark:text-white mb-4">
                            Driver Selection
                        </legend>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Driver A (Pitting) */}
                            <div className="space-y-2">
                                <Label htmlFor={driverAId} className="text-base font-medium">
                                    Driver A (Attempting Undercut)
                                    <span className="text-red-500 ml-1" aria-label="required">*</span>
                                </Label>
                                <Select
                                    value={form.watch('driver_a')}
                                    onValueChange={(value) => form.setValue('driver_a', value)}
                                    required
                                    aria-describedby={`${driverAId}-description`}
                                >
                                    <SelectTrigger
                                        id={driverAId}
                                        className="w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        aria-label="Select driver attempting undercut"
                                    >
                                        <SelectValue placeholder="Select driver attempting undercut" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {DRIVER_OPTIONS.map((option) => (
                                            <SelectItem key={option.value} value={option.value}>
                                                {option.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p id={`${driverAId}-description`} className="text-sm text-gray-600 dark:text-gray-400">
                                    Driver who will pit for fresh tires
                                </p>
                            </div>

                            {/* Driver B (Staying Out) */}
                            <div className="space-y-2">
                                <Label htmlFor={driverBId} className="text-base font-medium">
                                    Driver B (Target of Undercut)
                                    <span className="text-red-500 ml-1" aria-label="required">*</span>
                                </Label>
                                <Select
                                    value={form.watch('driver_b')}
                                    onValueChange={(value) => form.setValue('driver_b', value)}
                                    required
                                    aria-describedby={`${driverBId}-description`}
                                >
                                    <SelectTrigger
                                        id={driverBId}
                                        className="w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        aria-label="Select target driver for undercut"
                                    >
                                        <SelectValue placeholder="Select target driver" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {DRIVER_OPTIONS.map((option) => (
                                            <SelectItem key={option.value} value={option.value}>
                                                {option.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p id={`${driverBId}-description`} className="text-sm text-gray-600 dark:text-gray-400">
                                    Driver currently ahead who will stay out
                                </p>
                            </div>
                        </div>
                    </fieldset>
                </CardContent>
            </Card>

            {/* Situation Configuration */}
            <Card>
                <CardContent className="pt-6">
                    <fieldset className="space-y-4">
                        <legend className="font-semibold text-lg text-gray-900 dark:text-white mb-4">
                            Race Situation Parameters
                        </legend>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {/* Compound */}
                            <div className="space-y-2">
                                <Label htmlFor={compoundId} className="text-base font-medium">
                                    New Tire Compound
                                    <span className="text-red-500 ml-1" aria-label="required">*</span>
                                </Label>
                                <Select
                                    value={form.watch('compound_a')}
                                    onValueChange={(value) => form.setValue('compound_a', value as 'SOFT' | 'MEDIUM' | 'HARD')}
                                    required
                                    aria-describedby={`${compoundId}-description`}
                                >
                                    <SelectTrigger
                                        id={compoundId}
                                        className="w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        aria-label="Select new tire compound"
                                    >
                                        <SelectValue placeholder="Select tire compound" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {COMPOUND_OPTIONS.map((option) => (
                                            <SelectItem key={option.value} value={option.value}>
                                                <div>
                                                    <div className="font-medium">{option.label}</div>
                                                    <div className="text-xs text-gray-500">{option.description}</div>
                                                </div>
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p id={`${compoundId}-description`} className="text-sm text-gray-600 dark:text-gray-400">
                                    Tire compound for fresh pit stop
                                </p>
                            </div>

                            {/* Current Lap */}
                            <div className="space-y-2">
                                <Label htmlFor={lapId} className="text-base font-medium">
                                    Current Lap Number
                                    <span className="text-red-500 ml-1" aria-label="required">*</span>
                                </Label>
                                <Input
                                    id={lapId}
                                    type="number"
                                    min={1}
                                    max={80}
                                    className="focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    aria-describedby={`${lapId}-description`}
                                    {...form.register('lap_now', { valueAsNumber: true })}
                                />
                                <p id={`${lapId}-description`} className="text-sm text-gray-600 dark:text-gray-400">
                                    Current race lap (1-80)
                                </p>
                            </div>

                            {/* Samples */}
                            <div className="space-y-2">
                                <Label htmlFor={samplesId} className="text-base font-medium">
                                    Monte Carlo Samples
                                </Label>
                                <Input
                                    id={samplesId}
                                    type="number"
                                    min={100}
                                    max={10000}
                                    step={100}
                                    className="focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    aria-describedby={`${samplesId}-description`}
                                    {...form.register('samples', { valueAsNumber: true })}
                                />
                                <p id={`${samplesId}-description`} className="text-sm text-gray-600 dark:text-gray-400">
                                    Simulation iterations (100-10,000)
                                </p>
                            </div>
                        </div>
                    </fieldset>
                </CardContent>
            </Card>

            {/* Custom Gap Input - Demo Mode */}
            <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
                <CardContent className="pt-6">
                    <fieldset className="space-y-4">
                        <legend className="font-semibold text-lg text-blue-900 dark:text-blue-100 mb-4">
                            <Info className="inline-block w-5 h-5 mr-2" aria-hidden="true" />
                            Gap Override (Demo Mode)
                        </legend>
                        <div className="space-y-2">
                            <Label htmlFor={gapId} className="text-base font-medium text-blue-900 dark:text-blue-100">
                                Current Gap to Driver B (seconds)
                            </Label>
                            <Input
                                id={gapId}
                                type="number"
                                min={0}
                                max={60}
                                step={0.1}
                                value={customGap}
                                onChange={(e) => setCustomGap(parseFloat(e.target.value))}
                                className="w-full max-w-xs bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                aria-describedby={`${gapId}-description`}
                            />
                            <p id={`${gapId}-description`} className="text-sm text-blue-700 dark:text-blue-300">
                                In production, this would come from live timing data
                            </p>
                        </div>
                    </fieldset>
                </CardContent>
            </Card>

            {/* Error Display */}
            {form.formState.errors.root && (
                <div
                    className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4"
                    role="alert"
                    aria-live="polite"
                >
                    <div className="flex items-center">
                        <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400 mr-2" aria-hidden="true" />
                        <span className="text-red-800 dark:text-red-200 font-medium">Form Validation Error</span>
                    </div>
                    <p className="text-red-700 dark:text-red-300 mt-1">
                        {form.formState.errors.root.message}
                    </p>
                </div>
            )}

            {/* Submit Button */}
            <Button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 focus:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
                size="lg"
                disabled={simulationMutation.isPending}
                aria-describedby="submit-description"
            >
                {simulationMutation.isPending ? (
                    <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" aria-hidden="true" />
                        <span>Running Simulation...</span>
                        <span className="sr-only">Please wait, Monte Carlo simulation in progress</span>
                    </>
                ) : (
                    <>
                        <Play className="mr-2 h-5 w-5" aria-hidden="true" />
                        <span>Run Undercut Simulation</span>
                    </>
                )}
            </Button>
            <p id="submit-description" className="text-sm text-gray-600 dark:text-gray-400 text-center">
                Executes Monte Carlo simulation to calculate undercut success probability
            </p>
        </form>
    );
};