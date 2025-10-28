"use client";

import React, { useState, useEffect } from "react";
import { F1SimulationForm } from "./F1SimulationForm";
import { F1Results } from "./F1Results";
import { SimulationResponse } from "../lib/f1-api";
import "../styles/f1-theme.css";

interface F1DashboardState {
  isLoading: boolean;
  results: SimulationResponse | null;
  error: string | null;
}

export default function F1Dashboard(): React.ReactElement {
  const [state, setState] = useState<F1DashboardState>({
    isLoading: false,
    results: null,
    error: null,
  });

  const [mounted, setMounted] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>("");

  // Fix hydration error by only rendering time on client
  useEffect(() => {
    setMounted(true);
    const updateTime = () => {
      setCurrentTime(new Date().toLocaleTimeString());
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleSimulationSuccess = (results: SimulationResponse) => {
    setState({
      isLoading: false,
      results,
      error: null,
    });
  };

  const handleReset = () => {
    setState({
      isLoading: false,
      results: null,
      error: null,
    });
  };

  return (
    <div className="f1-dashboard">
      {/* Header */}
      <header className="f1-header">
        <div className="f1-header-content">
          <div className="f1-logo">
            <div className="f1-logo-text">F1</div>
            <div className="f1-logo-subtitle">UNDERCUT SIMULATOR</div>
          </div>
          <div className="f1-status-indicator">
            <div
              className={`f1-status-dot ${
                state.isLoading ? "loading" : "ready"
              }`}
            ></div>
            <span className="f1-status-text">
              {state.isLoading ? "SIMULATION RUNNING" : "READY TO RACE"}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="f1-main">
        <div className="f1-container">
          {/* Simulation Form */}
          <div className="f1-section">
            <h2 className="f1-section-title">
              <span className="f1-title-icon">🏁</span>
              RACE STRATEGY SIMULATION
            </h2>
            <F1SimulationForm onSimulationSuccess={handleSimulationSuccess} />
          </div>

          {/* Error State */}
          {state.error && (
            <div className="f1-section">
              <div className="f1-error-container">
                <div className="f1-error-icon">⚠️</div>
                <h3 className="f1-error-title">SIMULATION ERROR</h3>
                <p className="f1-error-message">{state.error}</p>
                <button
                  onClick={handleReset}
                  className="f1-button f1-button-secondary"
                >
                  RESET SIMULATION
                </button>
              </div>
            </div>
          )}

          {/* Results */}
          {state.results && !state.isLoading && (
            <div className="f1-section">
              <div className="f1-results-header">
                <h2 className="f1-section-title">
                  <span className="f1-title-icon">🏆</span>
                  STRATEGIC ANALYSIS
                </h2>
                <button
                  onClick={handleReset}
                  className="f1-button f1-button-ghost"
                >
                  NEW SIMULATION
                </button>
              </div>
              <F1Results result={state.results} />
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="f1-footer">
        <div className="f1-footer-content">
          <div className="f1-footer-left">
            <p>
              F1 Undercut Simulator | Powered by Advanced Strategy Analytics
            </p>
          </div>
          <div className="f1-footer-right">
            <div className="f1-timing">
              <span className="f1-timing-label">LAP TIME:</span>
              <span className="f1-timing-value">
                {mounted ? currentTime : "--:--:--"}
              </span>
            </div>
          </div>
        </div>
      </footer>

      {/* Background Elements */}
      <div className="f1-background">
        <div className="f1-grid-lines"></div>
        <div className="f1-speed-lines"></div>
      </div>

      <style jsx>{`
        .f1-dashboard {
          min-height: 100vh;
          background: var(--f1-bg-primary);
          position: relative;
          overflow-x: hidden;
        }

        .f1-header {
          background: linear-gradient(135deg, #dc2626, #991b1b);
          border-bottom: 4px solid #00f5ff;
          position: sticky;
          top: 0;
          z-index: 100;
          box-shadow: 0 4px 20px rgba(220, 38, 127, 0.3);
        }

        .f1-header-content {
          max-width: 1400px;
          margin: 0 auto;
          padding: 1rem 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .f1-logo {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .f1-logo-text {
          font-family: var(--font-orbitron), "Orbitron", sans-serif;
          font-size: 3rem;
          font-weight: 900;
          color: white;
          text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
          letter-spacing: 0.1em;
        }

        .f1-logo-subtitle {
          font-family: var(--font-rajdhani), "Rajdhani", sans-serif;
          font-size: 0.9rem;
          color: #00f5ff;
          font-weight: 600;
          letter-spacing: 0.15em;
          text-transform: uppercase;
        }

        .f1-status-indicator {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          background: rgba(0, 0, 0, 0.3);
          padding: 0.5rem 1rem;
          border-radius: 25px;
          border: 1px solid #00f5ff;
        }

        .f1-status-dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: #00ff00;
        }

        .f1-status-dot.loading {
          background: #ffff00;
          animation: pulse 1.5s infinite;
        }

        .f1-status-text {
          font-family: var(--font-rajdhani), "Rajdhani", sans-serif;
          font-size: 0.8rem;
          color: white;
          font-weight: 600;
          letter-spacing: 0.1em;
        }

        .f1-main {
          flex: 1;
          position: relative;
          z-index: 10;
        }

        .f1-container {
          max-width: 1400px;
          margin: 0 auto;
          padding: 2rem;
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }

        .f1-section {
          background: rgba(0, 0, 0, 0.7);
          border-radius: 16px;
          border: 2px solid #333;
          padding: 2rem;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
          backdrop-filter: blur(10px);
          position: relative;
          overflow: hidden;
        }

        .f1-section::before {
          content: "";
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 4px;
          background: linear-gradient(90deg, #dc2626, #00f5ff, #dc2626);
        }

        .f1-section-title {
          font-family: var(--font-orbitron), "Orbitron", sans-serif;
          font-size: 1.8rem;
          color: white;
          margin-bottom: 1.5rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          letter-spacing: 0.05em;
        }

        .f1-title-icon {
          font-size: 2rem;
        }

        .f1-results-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .f1-footer {
          background: rgba(0, 0, 0, 0.9);
          border-top: 2px solid #333;
          padding: 1rem 2rem;
          margin-top: auto;
        }

        .f1-footer-content {
          max-width: 1400px;
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-family: var(--font-rajdhani), "Rajdhani", sans-serif;
          font-size: 0.9rem;
          color: #ccc;
        }

        .f1-timing {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .f1-timing-label {
          font-weight: 600;
          color: #00f5ff;
          letter-spacing: 0.1em;
        }

        .f1-timing-value {
          font-family: "Courier New", monospace;
          font-weight: bold;
          color: white;
        }

        .f1-background {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          z-index: 1;
          opacity: 0.1;
        }

        .f1-grid-lines {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-image: linear-gradient(90deg, #00f5ff 1px, transparent 1px),
            linear-gradient(0deg, #00f5ff 1px, transparent 1px);
          background-size: 50px 50px;
        }

        .f1-speed-lines {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 100px,
            #dc2626 100px,
            #dc2626 102px
          );
          animation: f1-speed-lines 20s infinite linear;
        }

        @keyframes pulse {
          0%,
          100% {
            opacity: 1;
          }
          50% {
            opacity: 0.3;
          }
        }

        @keyframes f1-speed-lines {
          from {
            transform: translateX(-200px) translateY(-200px);
          }
          to {
            transform: translateX(200px) translateY(200px);
          }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
          .f1-header-content {
            padding: 0.75rem 1rem;
            flex-direction: column;
            gap: 1rem;
          }

          .f1-logo-text {
            font-size: 2rem;
          }

          .f1-container {
            padding: 1rem;
          }

          .f1-section {
            padding: 1.5rem;
          }

          .f1-section-title {
            font-size: 1.4rem;
          }

          .f1-footer-content {
            flex-direction: column;
            gap: 0.5rem;
            text-align: center;
          }

          .f1-results-header {
            flex-direction: column;
            gap: 1rem;
            align-items: stretch;
          }
        }
      `}</style>
    </div>
  );
}

