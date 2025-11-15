# Sentry Setup - Frontend (React)

## ✅ Configuration Complete

Sentry has been successfully integrated into the React frontend application.

---

## 📦 Installed Packages

```json
{
  "@sentry/react": "latest"
}
```

---

## 🔧 Configuration Details

### 1. Main Configuration (`src/main.tsx`)

Sentry is initialized **before** the React app renders:

```typescript
Sentry.init({
  dsn: "https://61b2a6bdd305796a504f4108d060780a@o4510369986904064.ingest.us.sentry.io/4510370087960576",

  // Performance Monitoring
  tracesSampleRate: 1.0, // 100% in development

  // Session Replay
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,

  // API Tracking
  tracePropagationTargets: [
    'localhost',
    /^http:\/\/localhost:8000/, // API Gateway
    /^http:\/\/localhost:8002/, // Data Generation Service
    /^http:\/\/localhost:8003/, // Analytics Service
    /^http:\/\/localhost:8005/, // Security Service
  ],

  environment: import.meta.env.MODE, // 'development' or 'production'
})
```

### 2. Error Boundary (`src/components/SentryErrorBoundary.tsx`)

The entire app is wrapped in a Sentry Error Boundary to catch React component errors:

```tsx
<SentryErrorBoundary>
  <App />
</SentryErrorBoundary>
```

**Features:**
- Catches React component errors
- Shows user-friendly error UI
- Reports errors to Sentry
- Allows users to retry after error

### 3. Test Components (`src/components/SentryErrorButton.tsx`)

Two test buttons for verifying Sentry integration:

- **SentryErrorButton**: Throws an intentional error
- **SentryMessageButton**: Sends a test message to Sentry

---

## 🧪 How to Test

### Option 1: Use Test Buttons

Add the test buttons to any component:

```tsx
import { SentryErrorButton, SentryMessageButton } from './components/SentryErrorButton';

function YourComponent() {
  return (
    <div>
      <SentryErrorButton />
      <SentryMessageButton />
    </div>
  );
}
```

### Option 2: Manually Trigger Error

Add this button anywhere in your app:

```tsx
<button onClick={() => {
  throw new Error('Test error from React!');
}}>
  Test Sentry Error
</button>
```

### Option 3: Capture Message

```tsx
import * as Sentry from '@sentry/react';

Sentry.captureMessage('Hello from React!', 'info');
```

### Option 4: Capture Exception

```tsx
import * as Sentry from '@sentry/react';

try {
  // Some code
} catch (error) {
  Sentry.captureException(error);
}
```

---

## 🎯 What You'll See in Sentry

### Issues Tab
- All JavaScript errors
- React component errors
- Unhandled promise rejections
- Stack traces with source maps (when configured)

### Performance Tab
- Page load times
- API call performance
- Component render times
- Distributed tracing to backend services

### Replays Tab
- Session recordings for errors
- User interactions before error
- Console logs
- Network requests

---

## 🔒 Features Enabled

✅ **Error Tracking**
- Automatic error capture
- React error boundaries
- Unhandled promise rejections

✅ **Performance Monitoring**
- Page load metrics
- API call tracking
- Component performance

✅ **Session Replay**
- 10% of normal sessions
- 100% of sessions with errors

✅ **Distributed Tracing**
- Traces API calls to backend
- End-to-end request tracking

✅ **User Context**
- IP addresses
- Browser information
- User agent data

---

## 📊 Production Recommendations

Before deploying to production, adjust these settings in `main.tsx`:

```typescript
Sentry.init({
  // ... other config

  // Reduce sampling for cost optimization
  tracesSampleRate: 0.1,  // 10% of transactions
  replaysSessionSampleRate: 0.01,  // 1% of sessions
  replaysOnErrorSampleRate: 1.0,   // 100% of error sessions

  // Add release tracking
  release: `frontend@${import.meta.env.VITE_APP_VERSION}`,

  // Add environment-specific config
  environment: import.meta.env.MODE,

  // Filter out sensitive data
  beforeSend(event) {
    // Remove passwords, tokens, etc.
    if (event.request?.headers?.Authorization) {
      delete event.request.headers.Authorization;
    }
    return event;
  },
})
```

---

## 🚀 Advanced Usage

### Set User Context

```typescript
import * as Sentry from '@sentry/react';

Sentry.setUser({
  id: user.id,
  email: user.email,
  username: user.username,
});
```

### Add Breadcrumbs

```typescript
Sentry.addBreadcrumb({
  category: 'auth',
  message: 'User logged in',
  level: 'info',
});
```

### Custom Tags

```typescript
Sentry.setTag('page_locale', 'en-us');
Sentry.setTag('feature_flag', 'new-dashboard');
```

### Create Profiler

Measure React component performance:

```tsx
import * as Sentry from '@sentry/react';

const MyComponent = Sentry.withProfiler(
  function MyComponent() {
    return <div>Content</div>;
  }
);
```

---

## 🔍 Debugging

### Check Sentry Status

```typescript
// In browser console
if (window.Sentry) {
  console.log('Sentry is loaded');
}
```

### Test Error Capture

```typescript
import * as Sentry from '@sentry/react';

Sentry.captureMessage('Test message', 'debug');
console.log('Message sent to Sentry');
```

### View Configuration

```typescript
// Add to component during development
console.log(Sentry.getCurrentHub().getClient()?.getOptions());
```

---

## 📝 File Structure

```
frontend/
├── src/
│   ├── main.tsx                           # Sentry initialization
│   ├── components/
│   │   ├── SentryErrorBoundary.tsx       # Error boundary component
│   │   └── SentryErrorButton.tsx         # Test buttons
│   └── ...
├── package.json                          # @sentry/react dependency
└── SENTRY_SETUP.md                       # This file
```

---

## 🔗 Useful Links

- [Sentry React Documentation](https://docs.sentry.io/platforms/javascript/guides/react/)
- [Error Boundaries](https://docs.sentry.io/platforms/javascript/guides/react/features/error-boundary/)
- [Performance Monitoring](https://docs.sentry.io/platforms/javascript/guides/react/performance/)
- [Session Replay](https://docs.sentry.io/platforms/javascript/guides/react/session-replay/)

---

**Last Updated**: 2025-11-15
**Sentry SDK Version**: @sentry/react (latest)
**Frontend DSN**: https://61b2a6bdd305796a504f4108d060780a@o4510369986904064.ingest.us.sentry.io/4510370087960576
