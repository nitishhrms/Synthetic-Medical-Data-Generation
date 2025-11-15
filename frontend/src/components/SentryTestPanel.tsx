import * as Sentry from '@sentry/react';

/**
 * Sentry Test Panel - Add this to your app for easy Sentry testing
 * Remove this component after verifying Sentry is working
 */
export function SentryTestPanel() {
  const handleThrowError = () => {
    throw new Error('🔥 Test error from React - Sentry should catch this!');
  };

  const handleCaptureMessage = () => {
    Sentry.captureMessage('✅ Test message from React frontend!', 'info');
    alert('Message sent to Sentry! Check your Sentry dashboard.');
  };

  const handleCaptureException = () => {
    try {
      // Simulate an error
      const data: any = null;
      data.someMethod(); // This will throw
    } catch (error) {
      Sentry.captureException(error);
      alert('Exception captured and sent to Sentry!');
    }
  };

  const handleAddBreadcrumb = () => {
    Sentry.addBreadcrumb({
      category: 'test',
      message: 'User clicked breadcrumb test button',
      level: 'info',
    });
    alert('Breadcrumb added! Now trigger an error to see it in Sentry.');
  };

  return (
    <div className="fixed bottom-4 right-4 bg-white border-2 border-gray-300 rounded-lg shadow-lg p-4 max-w-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-bold text-gray-900">🔍 Sentry Test Panel</h3>
        <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
          DEV ONLY
        </span>
      </div>

      <div className="space-y-2">
        <button
          onClick={handleThrowError}
          className="w-full px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors text-sm font-medium"
        >
          🔥 Throw Error (Will crash)
        </button>

        <button
          onClick={handleCaptureMessage}
          className="w-full px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors text-sm font-medium"
        >
          📨 Send Message
        </button>

        <button
          onClick={handleCaptureException}
          className="w-full px-3 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 transition-colors text-sm font-medium"
        >
          ⚠️ Capture Exception
        </button>

        <button
          onClick={handleAddBreadcrumb}
          className="w-full px-3 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors text-sm font-medium"
        >
          🍞 Add Breadcrumb
        </button>
      </div>

      <p className="mt-3 text-xs text-gray-500 border-t pt-2">
        Click buttons to test Sentry integration. Check{' '}
        <a
          href="https://sentry.io"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          Sentry Dashboard
        </a>
        {' '}for results.
      </p>
    </div>
  );
}
