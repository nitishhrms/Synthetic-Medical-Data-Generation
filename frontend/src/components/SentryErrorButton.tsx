import * as Sentry from '@sentry/react';

/**
 * Test button to verify Sentry error tracking
 * This component intentionally throws an error when clicked
 */
export function SentryErrorButton() {
  return (
    <button
      onClick={() => {
        throw new Error('This is your first error!');
      }}
      className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
    >
      Break the world (Test Sentry)
    </button>
  );
}

/**
 * Test button to capture a message in Sentry
 */
export function SentryMessageButton() {
  const handleClick = () => {
    Sentry.captureMessage('Test message from React frontend!', 'info');
    alert('Message sent to Sentry!');
  };

  return (
    <button
      onClick={handleClick}
      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
    >
      Send Test Message to Sentry
    </button>
  );
}
