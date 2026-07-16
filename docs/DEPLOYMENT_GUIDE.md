# Sovereign Terminal Production Deployment Protocol
**Classification**: Public Release Documentation  
**Version**: 1.1

This protocol details the configuration required to establish the static hosting pipeline for the Tokennomics Sovereign Terminal and register the weekly update cron pipeline on the target repository.

---

## Section 1: Local Terminal Integration (GitHub Actions)

Due to default GitHub API security restrictions protecting workflow configurations, automated integration tokens are restricted from modifying files inside the `.github/` namespace. The cron automation pipeline must be synchronized manually via a credentialed local terminal:

1. Open your local terminal interface.
2. Navigate to the repository root directory:
   ```bash
   cd C:/Users/Robert/.gemini/antigravity/scratch/ndv_engine
   ```
3. Stage, commit, and push the workflow files using the local credentials manager:
   ```bash
   git add .github/
   git commit -m "Enable weekly UN data automation"
   git push origin main
   ```

---

## Section 2: Static Hosting Architecture (GitHub Pages)

To expose the interactive schema-agnostic terminal dashboard to public auditable URLs:

1. Navigate to the remote repository management interface:
   [https://github.com/Tokennomics/ndv-global-matrix](https://github.com/Tokennomics/ndv-global-matrix)
2. Select the **Settings** panel from the upper navigation layout.
3. Locate the **Code and automation** section in the left navigation sidebar and click **Pages**.
4. Under the **Build and deployment** specification:
   - **Source**: Select `Deploy from a branch`.
   - **Branch**: Select `main`.
   - **Folder**: Select `/ (root)`.
5. Click **Save** to commit the hosting directive.

---

## Section 3: Verification & Ingestion Audit

Upon saving, the deployment pipeline will initialize. Within 120 seconds, the public endpoint will stabilize at:
`https://Tokennomics.github.io/ndv-global-matrix/`

Execute the following verification checklist:
- Check that the application successfully performs the asynchronous fetch sequence for `global_sovereign_ledger.csv`.
- Verify the rendering of all 190+ countries in the ledger directory.
- Confirm the automatic redistribution calculations under the Cohesion Transfer Matrix are properly displayed.
