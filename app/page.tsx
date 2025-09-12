'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Loader2, BarChart3, Timer, Zap } from 'lucide-react'
import { SimulationChart } from '@/components/simulation-chart'
import { api } from '@/lib/api'

interface Session {
  session_key: string
  session_name: string
  date_start: string
  location: string
  circuit_short_name: string
  year: number
}

export default function HomePage() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [selectedSession, setSelectedSession] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState<any>(null)
  const [year, setYear] = useState(new Date().getFullYear())

  useEffect(() => {
    const loadSessions = async () => {
      try {
        setLoading(true)
        const data = await api.getSessions(year)
        setSessions(data.sessions || [])
      } catch (error) {
        console.error('Failed to load sessions:', error)
      } finally {
        setLoading(false)
      }
    }
    
    loadSessions()
  }, [year])

  const runSimulation = async () => {
    if (!selectedSession) return

    try {
      setLoading(true)
      setAnalysis(null)

      // Run tire degradation analysis
      const degradationData = await api.analyzeTireDegradation(selectedSession)
      
      // Run pit strategy optimization
      const strategyData = await api.optimizePitStrategy({
        current_position: 8,
        current_lap: 15,
        total_laps: 50,
        current_tire: 'MEDIUM',
        tire_age: 12,
        fuel_load: 45.0,
        weather: 'dry',
        traffic_density: 0.6
      })

      setAnalysis({
        degradation: degradationData,
        strategy: strategyData
      })
    } catch (error) {
      console.error('Simulation failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">F1 Undercut Simulator</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Analyze tire degradation, optimize pit strategies, and discover undercut opportunities
          using real Formula 1 data and advanced modeling.
        </p>
      </div>

      {/* Configuration Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Simulation Configuration
          </CardTitle>
          <CardDescription>
            Select a session to analyze pit strategy and undercut opportunities
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Year</label>
              <Select value={year.toString()} onValueChange={(value: string) => setYear(parseInt(value))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[2024, 2023, 2022, 2021].map((y) => (
                    <SelectItem key={y} value={y.toString()}>
                      {y}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Session</label>
              <Select value={selectedSession} onValueChange={setSelectedSession} disabled={loading}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a session" />
                </SelectTrigger>
                <SelectContent>
                  {sessions.map((session) => (
                    <SelectItem key={session.session_key} value={session.session_key}>
                      {session.location} - {session.session_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button 
                onClick={runSimulation} 
                disabled={!selectedSession || loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Zap className="mr-2 h-4 w-4" />
                    Run Simulation
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Section */}
      {analysis && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Best Strategy</CardTitle>
                <Timer className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {analysis.strategy?.recommended_strategy?.strategy_type || 'N/A'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {analysis.strategy?.recommended_strategy?.description || ''}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Position Gain</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  +{analysis.strategy?.recommended_strategy?.expected_position_gain?.toFixed(1) || '0.0'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Expected positions
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Confidence</CardTitle>
                <Badge variant="secondary">
                  {Math.round((analysis.strategy?.recommended_strategy?.confidence || 0) * 100)}%
                </Badge>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(analysis.strategy?.recommended_strategy?.risk_factor || 0) < 0.5 ? 'Low' : 'High'} Risk
                </div>
                <p className="text-xs text-muted-foreground">
                  Strategy risk level
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Charts */}
          <Card>
            <CardHeader>
              <CardTitle>Analysis Results</CardTitle>
              <CardDescription>
                Tire degradation and pit strategy visualization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SimulationChart data={analysis} />
            </CardContent>
          </Card>

          {/* Detailed Results */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Tire Degradation Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analysis.degradation?.analyses?.map((analysis: any, index: number) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="outline">{analysis.compound}</Badge>
                        <span className="text-sm text-muted-foreground">
                          {analysis.stint_length} laps
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">Degradation/lap:</span>
                          <div className="font-medium">{analysis.degradation_per_lap}s</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Total loss:</span>
                          <div className="font-medium">{analysis.total_degradation}s</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Strategy Options</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[analysis.strategy?.recommended_strategy, ...(analysis.strategy?.alternative_strategies || [])].map((strategy: any, index: number) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant={index === 0 ? "default" : "secondary"}>
                          {strategy?.strategy_type}
                        </Badge>
                        <span className="text-sm font-medium">
                          +{strategy?.expected_position_gain?.toFixed(1)} positions
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {strategy?.description}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}