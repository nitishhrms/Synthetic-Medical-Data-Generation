#!/usr/bin/env node
/**
 * Frontend API Integration Test
 * Tests the aactApi.ts service with actual backend endpoints
 */

const API_BASE_URL = 'http://localhost:8002';

// Simple fetch implementation for testing
async function testFetch(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `${API_BASE_URL}${endpoint}${queryString ? '?' + queryString : ''}`;

    console.log(`\n📡 Fetching: ${url}`);

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        console.log(`✅ Success! Keys: ${Object.keys(data).join(', ')}`);
        return data;
    } catch (error) {
        console.error(`❌ Error: ${error.message}`);
        return null;
    }
}

async function main() {
    console.log('\n' + '='.repeat(80));
    console.log('Frontend AACT API Integration Test');
    console.log('='.repeat(80));

    // Test 1: Demographics
    console.log('\n1️⃣  Testing Demographics API');
    const demo = await testFetch('/aact/analytics/demographics', {
        indication: 'hypertension',
        phase: 'Phase 3'
    });
    if (demo) {
        console.log(`   Age groups: ${demo.age_distribution?.length || 0}`);
        console.log(`   Gender types: ${demo.gender_distribution?.length || 0}`);
        console.log(`   Race categories: ${demo.race_distribution?.length || 0}`);
    }

    // Test 2: Adverse Events
    console.log('\n2️⃣  Testing Adverse Events API');
    const ae = await testFetch('/aact/analytics/adverse_events', {
        indication: 'hypertension'
    });
    if (ae) {
        console.log(`   Common AEs: ${ae.common_aes?.length || 0}`);
        console.log(`   SOC categories: ${ae.soc_distribution?.length || 0}`);
        console.log(`   Severity levels: ${ae.severity_distribution?.length || 0}`);
    }

    // Test 3: Labs
    console.log('\n3️⃣  Testing Labs API');
    const labs = await testFetch('/aact/analytics/labs', {
        indication: 'hypertension'
    });
    if (labs) {
        console.log(`   Hematology params: ${labs.hematology?.length || 0}`);
        console.log(`   Chemistry params: ${labs.chemistry?.length || 0}`);
        console.log(`   Urinalysis params: ${labs.urinalysis?.length || 0}`);
    }

    // Summary
    console.log('\n' + '='.repeat(80));
    const allPassed = demo && ae && labs;
    if (allPassed) {
        console.log('✅ All frontend API calls successful!');
        console.log('   Ready for Analytics component integration.');
    } else {
        console.log('❌ Some API calls failed. Check backend server.');
    }
    console.log('='.repeat(80) + '\n');
}

main().catch(console.error);
