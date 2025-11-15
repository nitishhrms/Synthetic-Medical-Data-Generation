import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react'
import './index.css'
import App from './App.tsx'
import { SentryErrorBoundary } from './components/SentryErrorBoundary'

// Initialize Sentry as early as possible
Sentry.init({
  dsn: "https://61b2a6bdd305796a504f4108d060780a@o4510369986904064.ingest.us.sentry.io/4510370087960576",
  // Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
  // Adjust this value in production (e.g., 0.1 = 10% of transactions)
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
  // Performance Monitoring
  tracesSampleRate: 1.0, // Capture 100% of transactions in development
  // Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
  tracePropagationTargets: [
    'localhost',
    /^https:\/\/yourserver\.io\/api/,
    /^http:\/\/localhost:8000/, // API Gateway
    /^http:\/\/localhost:8002/, // Data Generation Service
    /^http:\/\/localhost:8003/, // Analytics Service
    /^http:\/\/localhost:8005/, // Security Service
  ],
  // Session Replay
  replaysSessionSampleRate: 0.1, // Sample 10% of sessions
  replaysOnErrorSampleRate: 1.0, // Sample 100% of sessions with errors
  // Setting this option to true will send default PII data to Sentry.
  // For example, automatic IP address collection on events
  sendDefaultPii: true,
  environment: import.meta.env.MODE || 'development',
})

const container = document.getElementById('root')
const root = createRoot(container!)

root.render(
  <StrictMode>
    <SentryErrorBoundary>
      <App />
    </SentryErrorBoundary>
  </StrictMode>,
)
