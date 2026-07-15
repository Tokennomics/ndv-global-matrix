# GitHub Pages Deployment Guide: Tokennomics EU Sovereign Terminal

To deploy your interactive terminal dashboard to the web via **GitHub Pages** (generating a public URL like `https://Tokennomics.github.io/ndv-global-matrix`), follow these simple configurations.

---

## Method 1: Enabling Pages via the GitHub Interface (Recommended)

Since `index.html` and `global_sovereign_ledger.csv` reside at the **root** of the repository, you can enable GitHub Pages directly without writing a compilation build script:

1. Go to your repository on GitHub: `https://github.com/Tokennomics/ndv-global-matrix`.
2. Click on the **Settings** tab in the top navigation bar.
3. In the left sidebar, under the "Code and automation" section, click on **Pages**.
4. Under **Build and deployment**:
   - **Source**: Select `Deploy from a branch`.
   - **Branch**: Click the dropdown, select **`main`**, and select the **`/ (root)`** folder.
5. Click **Save**.
6. Wait 1–2 minutes. GitHub will compile the page and display the public link at the top of the Pages settings window:
   `Your site is live at https://Tokennomics.github.io/ndv-global-matrix/`

---

## Method 2: Automated Deployment via Git Command Line

If you want to configure or push changes directly from a secondary branch, you can create a `gh-pages` branch using these terminal commands:

```bash
# 1. Create a detached branch for static pages
git checkout --orphan gh-pages

# 2. Clear out unnecessary source files from stage
git rm -rf .

# 3. Checkout only index.html and the master dataset
git checkout main index.html global_sovereign_ledger.csv

# 4. Commit and push the static files
git commit -m "Deploy dashboard to GitHub Pages"
git push origin gh-pages

# 5. Switch back to your working branch
git checkout main
```
Then, under **Settings -> Pages**, select the source branch as **`gh-pages`** and folder as **`/ (root)`**.
