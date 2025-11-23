import { trialPlanningApi, medicalImagingApi } from './src/services/api.ts';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const fetch = require('node-fetch');

// Polyfill fetch for Node.js environment
(global as any).fetch = fetch;
(global as any).localStorage = {
    getItem: () => null,
    setItem: () => { },
    removeItem: () => { },
    length: 0,
    clear: () => { },
    key: () => null
};

// Mock environment variables
process.env.VITE_ANALYTICS_URL = "http://localhost:8003";
process.env.VITE_EDC_URL = "http://localhost:8001";

async function testFrontendApi() {
    console.log("Testing Frontend API Integration...");

    // 1. Test Trial Planning API
    console.log("\n--- Testing Trial Planning API ---");
    try {
        const result = await trialPlanningApi.assessFeasibility({
            baseline_data: [],
            target_effect: -5.0,
            power: 0.8,
            dropout_rate: 0.1,
            alpha: 0.05
        });
        console.log("✅ Feasibility Assessment: SUCCESS");
    } catch (error: any) {
        console.error("❌ Feasibility Assessment: FAILED", error.message);
    }

    // 2. Test Medical Imaging API
    console.log("\n--- Testing Medical Imaging API ---");
    try {
        const status = await medicalImagingApi.getStatus();
        console.log("✅ Imaging Status: SUCCESS", status);
    } catch (error: any) {
        console.error("❌ Imaging Status: FAILED", error.message);
    }
}

testFrontendApi();
