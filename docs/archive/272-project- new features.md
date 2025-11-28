272-project- new features

1\.

* K-nearest neighbor imputation when comparing synthetic data to actual data.  
* Measure euclidian distance between synthetic data and actual data.  
* Use KNN to find closest imputation  
* Business benefit: Reduces trial re-runs and cost.

2\. Comprehensive and visual statistical analysis between synthetic and actual data.

3\. 

# **Specific, file-level receipts (so you can’t say I hand-waved)**

* **Encryption claim vs code**: security-service/README.md \+ QUICKSTART\_GUIDE.md (“AES-256-GCM”) vs security-service/src/encryption.py (Fernet) and /encryption/encrypt logging the wrong algorithm in security-service/src/main.py.

* **Audit not immutable**: security-service/src/audit.py has single integrity\_hash—no chain, no WORM.

* **RLS not enforced**: RLS policies in database/init.sql, but app never sets app.current\_tenant (no set\_config anywhere) and many queries skip tenant\_id (e.g., database/database.py).

* **Schema mismatch**: database/init.sql (UUID users, JSONB roles, audit\_events) vs security-service/src/models.py (Integer users, string roles, audit\_logs).

* **No tracing/metrics in services**: only the gateway exposes /metrics (api-gateway/src/main.py).

* **K8s hardening missing**: no securityContext and no NetworkPolicy in kubernetes/deployments/\*.yaml.

* **Postgres PVC missing**: kubernetes/deployments/postgres.yaml deploys stateful DB with **no** PV/PVC.

* **SQLite default**: security-service/src/database.py.

* **OpenAI in prod path**: data-generation-service/requirements.txt \+ code in .../src/generators.py & main.py.

* **CORS “\*”**: e.g., analytics-service/src/main.py, edc-service/src/main.py.

---

# **“If you want to pass my class” — the minimum to be taken seriously (one hard sprint)**

1. **Fix the crypto lie and key management**

   * Pick **AES-256-GCM** or Fernet and make the **docs match the code**.

   * Implement **key versioning** (kid in metadata), rotation via **KMS/Vault**, and refuse startup if key is invalid.

   * Remove "hipaa\_compliant": true from health; compliance is an artifact, not a boolean.

2. **Enforce real multi-tenancy**

   * Propagate tenant\_id in JWT → gateway → services.

   * On every DB session, set app.current\_tenant (SET LOCAL) before queries.

   * Add **RLS unit tests** proving cross-tenant reads are impossible.

3. **Lock down the cluster**

   * **mTLS** (Linkerd/Istio), **NetworkPolicies**, and Pod securityContext (runAsNonRoot, readOnlyRootFilesystem, seccompProfile: RuntimeDefault).

   * Per-service service account \+ **audience-scoped JWT** for internal calls (no trust-on-network).

4. **Make the audit trail real**

   * Chain prev\_hash, push to **S3 with Object Lock** (WORM), and export a **verification job**.

   * Align on **one** table (audit\_events) across services.

5. **Resilience & scale**

   * Move heavy analytics to **async jobs** (Redis Streams/RabbitMQ), expose POST /jobs \+ GET /jobs/{id}.

   * Add **bulk ingest** \+ **idempotency keys** to EDC.

   * Gateway: **timeouts, retries with budgets, circuit breaker, request size limits**.

   * Add **tenant-aware** rate limits/quotas.

6. **Observability & tests**

   * **OpenTelemetry** (traces \+ metrics) in every service; propagate trace\_id/tenant\_id in logs.

   * Add **CI** (lint, unit, contract tests, docker build, Trivy scan, SBOM, signed images).

   * Bring back **Locust** with an SLO (e.g., p95 \< 300ms @ 200 RPS gateway, \<1% errors).

   * Create **Grafana dashboards** per service.

7. **Infra hygiene**

   * **PVC** for Postgres in K8s or remove that manifest and mandate **RDS** only—**with encryption at rest/in transit**.

   * ElastiCache: TLS in-transit, auth token.

   * No absolute paths in docs, ever.

# **What to reuse from the Devpost project (concretely)**

* **Missing-data aware imputation** using deep generative models (e.g., **GAIN / cGAN**) with explicit support for **MCAR/MAR/MNAR** scenarios. That’s literally what they claim: deep generative imputation, synthetic cohorts, and evaluation across missingness regimes. Build those *capabilities* into your data-generation-service and quality-service. 

* **Quality metrics for realism & imputation** your pipeline should compute automatically on every run: **Wasserstein distance**, **correlation preservation**, **RMSE**, etc. Expose these as an “evidence report” per dataset/model. 

* **Virtual cohort simulation / power analysis**: an API that lets analysts vary effect size, variance, dropout, allocation ratio and returns **power curves** and **sample-size** estimates. Their slides literally promise virtual patients \+ trial design optimization; you’ll implement the enterprise version with audit and versioning.  

# **Add these features to your platform (clean, product-ready)**

## **1\) Imputation & Synthesis service (productionized)**

**APIs (versioned):**

* POST /synth/v1/train: upload schema \+ training config (which variables are categorical/ordinal, constraints, privacy budget).

* POST /synth/v1/generate: params: n, conditioning (e.g., arm, biomarker strata), returns batch id.

* POST /impute/v1/run: missingness report \+ imputed dataset; store lineage to raw input.

* GET /evidence/v1/runs/{id}: JSON “evidence pack” (Wasserstein, RMSE, corr deltas, leakage risk).

**Under the hood:** add **model registry** (who trained it, data version, metrics, approval status), **idempotency keys**, **asynchronous jobs** (queue \+ workers), and **audit-grade artifacts** (hashes, prev\_hash chain). Use the Devpost claims (GAIN/cGAN; Wasserstein/RMSE; MCAR/MAR/MNAR) as your acceptance tests. 

## **2\) Virtual Trial Designer**

* POST /simulate/v1/power: inputs (effect size, σ, α, dropout, allocation, endpoint type) → **power curve** \+ recommended **N per arm**; keep full simulation seed for reproducibility. Their deck calls out virtual cohorts / smarter design—ship the enterprise version. 

---

# **“Serious analytics” plan (dashboards that matter to clinical teams)**

## **A. What to show (modules a sponsor expects)**

1. **Missingness & Imputation Quality**

   * Heatmap by **variable × visit × site**, “% missing” trend, **Little’s MCAR test** outcome, **pre vs post** imputation deltas.

   * Distribution overlays (real vs imputed vs synthetic), **Wasserstein distance** table with alert thresholds. 

2. **RBQM (Risk-Based Quality Management)**

   * KRIs: query rate/100 CRFs, late data entry %, AE reporting timeliness, protocol deviations, screen-fail rate.

   * **QTL** (quality tolerance limits) alarms with drill-downs by site/CRO.

3. **Enrollment & Retention**

   * Actual vs target, dropout Kaplan-Meier, screen-fail reasons, site activation funnel.

4. **Safety Snapshot (lite)**

   * MedDRA SOC/HLGT distribution of AEs, serious AE proportion, time-to-report.

5. **Trial-design “What-if”**

   * Interactive **power curves** and **sample-size calculators** backed by your simulate API.

## **B. Where to compute**

* **Storage:** columnar OLAP (ClickHouse/Snowflake/BigQuery) for fast group-bys; parquet “raw” zone for audit.

* **Transforms:** **dbt** to materialize star schemas (facts: visits, labs, queries, AEs; dims: subject, site, study, time; plus “metrics” marts for KRI/QTL).

* **Serving:**

  * **Open-source BI**: **Apache Superset** (role-based, multi-tenant), or **Metabase** for fast wins.

  * **Custom UI** (your app): build React screens with **ECharts** or **Vega-Lite** for tight integration and per-tenant theming.

  * **Time-series ops** (infra/SLOs): Grafana (Prometheus/Tempo) is separate from business dashboards.

## **C. How to wire it (fastest path that still scales)**

* Add an **analytics warehouse** schema in your Postgres → replicate to ClickHouse/Snowflake nightly (or stream with Debezium/Kafka later).

* Create **dbt models** for: fact\_observation, fact\_ae, fact\_query, dim\_subject, dim\_site, dim\_visit, plus **marts**: mart\_missingness, mart\_wasserstein, mart\_kri\_qtl.

* Stand up **Superset**: connect to OLAP, define slices:

  * “Missingness Matrix”, “Imputation Delta”, “Wasserstein Leaderboard”, “Enrollment Burn-down”, “QTL Breaches by Site”.

* Embed the top 6 charts in your app via iframe or re-implement in React using the same SQL as API sources.

---

# **Implementation backlog (2 sprints, concrete)**

**Sprint 1 – Data & jobs**

* Add **/train, /generate, /impute** async endpoints \+ Redis/RabbitMQ workers; persist runs \+ metrics.

* Compute **Wasserstein/KS**, **RMSE on holdout**, **corr delta**; store metrics per column \+ overall. (Backed by the literature to keep reviewers calm.  )

* New tables: model\_run, imputation\_run, evidence\_metric, simulation\_run (with config JSON & seeds).

* Build POST /simulate/v1/power \+ cached **power-curve** results.

**Sprint 2 – Dashboards & product polish**

* Add **dbt** project \+ marts (mart\_missingness, mart\_kri\_qtl, mart\_power\_curves).

* Spin up **Superset**; ship a “Clinical Analytics” menu with 6 dashboards listed above.

* Front-end: add “Analytics” section with tabs: *Quality*, *RBQM*, *Enrollment*, *Safety*, *Design*.

* Multi-tenant RBAC: charts auto-filter by tenant\_id (and optionally study\_id).

---

