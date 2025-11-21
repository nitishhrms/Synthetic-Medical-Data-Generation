# Bug Report: Data Generation "Insufficient Data" & Missing Placebo Arm

**Date:** 2025-11-20
**Status:** Open / Handover
**Priority:** High (Blocker for Analytics)

## Issue Description
When generating a "Comprehensive Study" (e.g., Hypertension, Phase 3), the resulting dataset often fails to produce valid analytics for the final visit (e.g., "Month 12"). The error message in the Analytics tab is:
`Statistics calculation failed: Insufficient data for both arms at 'Month 12'. Missing arms: Placebo. Available: {'Active': 379}.`

This indicates that while "Active" arm data is generated for the final visit, the "Placebo" arm data is either missing entirely for that visit or not being generated at all.

## Observations & Logs
1.  **Frontend Error:** "Insufficient data for both arms... Missing arms: Placebo".
2.  **Backend Logs (`data-generation-service`):**
    *   `DEBUG: generate_comprehensive_study - n_per_arm=50, total_subjects=100`
    *   `DEBUG: Treatment Arms - Active: 50, Placebo: 50`
    *   *Crucially:* `UserWarning: No demographics data for hypertension Phase 3. Using defaults.`
    *   *Crucially:* `UserWarning: No baseline characteristics data for hypertension Phase 3. Using defaults.`

## Suspected Root Causes
The user suspects the issue lies in the **AACT Statistics Cache** (`data/AACT/processed/aact_statistics_cache.json`) or the `aact_utils.py` loader.

1.  **Missing/Malformed AACT Data:** The logs explicitly state "No demographics data... Using defaults". This suggests that `aact_utils.py` is failing to find or parse data for "hypertension" / "Phase 3" from the cache file, causing it to fall back to default values.
2.  **Default Fallback Logic:** If the fallback logic in `generators.py` (specifically `generate_vitals_mvn_aact`) is triggered, it might have a bug where it fails to generate the Placebo arm correctly for the final visit, or the `visit_schedule` derived from defaults is inconsistent between arms.
3.  **Cache Formatting:** The user suspects `aact_statistics_cache.json` might be improperly formatted (e.g., `NaN` values, incorrect nesting) which `aact_utils.py` might not be handling robustly, leading to empty returns.

## Relevant Code Files
*   **`data/AACT/processed/aact_statistics_cache.json`**: The source of truth for real-world trial stats.
*   **`microservices/data-generation-service/src/aact_utils.py`**: The loader that reads the cache. Check `get_demographics` and `get_baseline_characteristics`.
*   **`microservices/data-generation-service/src/generators.py`**: Specifically `generate_vitals_mvn_aact`. This function uses the AACT data (or defaults) to generate the vitals.
*   **`microservices/data-generation-service/src/main.py`**: The orchestration logic for `generate_comprehensive_study`.

## Reproduction Steps
1.  Start the stack (`npm run dev` in frontend, `uvicorn` for services).
2.  Go to **Generate** tab.
3.  Select **Indication:** Hypertension, **Phase:** Phase 3.
4.  Click **Generate Complete Study**.
5.  Go to **Analytics** tab.
6.  Observe the "Insufficient data" error.
7.  Check terminal logs for `data-generation-service` to see the "No demographics data" warnings.

## Next Steps for Team Member
1.  **Validate Cache:** Inspect `aact_statistics_cache.json` to see if "hypertension" -> "Phase 3" -> "demographics" actually exists and is valid JSON.
2.  **Debug Loader:** Add logging to `aact_utils.py` inside `get_demographics` to see exactly what it reads from the JSON and why it returns `None` (triggering the warning).
3.  **Fix Generator:** If the fallback defaults are used, ensure `generate_vitals_mvn_aact` in `generators.py` correctly generates Placebo data for *all* visits, including the final one.
