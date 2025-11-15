/**
 * Quick Sentry Frontend Test Script
 * This sends a test event directly to Sentry to verify the DSN is working
 */

import * as Sentry from '@sentry/node';

// Initialize Sentry with the frontend DSN
Sentry.init({
  dsn: "https://61b2a6bdd305796a504f4108d060780a@o4510369986904064.ingest.us.sentry.io/4510370087960576",
  environment: 'test',
  tracesSampleRate: 1.0,
});

console.log('🧪 Testing Sentry Frontend Integration...\n');

// Test 1: Capture a message
console.log('📨 Test 1: Sending test message to Sentry...');
Sentry.captureMessage('✅ Test message from frontend automated test!', 'info');

// Test 2: Capture an exception
console.log('⚠️  Test 2: Sending test exception to Sentry...');
try {
  throw new Error('🔥 Test error from frontend automated test!');
} catch (error) {
  Sentry.captureException(error);
}

// Test 3: Add breadcrumb and capture error
console.log('🍞 Test 3: Adding breadcrumb and capturing error...');
Sentry.addBreadcrumb({
  category: 'test',
  message: 'Automated test breadcrumb',
  level: 'info',
});

Sentry.captureException(new Error('Error with breadcrumb context'));

// Wait for Sentry to send events
console.log('\n⏳ Waiting for events to be sent to Sentry...');
setTimeout(() => {
  console.log('\n✅ Test complete! Check your Sentry dashboard at:');
  console.log('   https://sentry.io\n');
  console.log('You should see:');
  console.log('   • Test message: "✅ Test message from frontend automated test!"');
  console.log('   • Test error: "🔥 Test error from frontend automated test!"');
  console.log('   • Error with breadcrumb context\n');
  process.exit(0);
}, 3000);
