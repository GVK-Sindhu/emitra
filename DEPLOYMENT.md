# Render Deployment Manual

This guide describes how to deploy the Emitra ESG Ingestion Platform prototype using Render Blueprints (`render.yaml`).

---

## 1. Environment Variables Documentation

Set these variables in the **Render Dashboard** for the `emitra-backend` Web Service.

| Environment Variable | Description | Recommended Setting |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string. | Automatically populated via the blueprint database hook. |
| `SECRET_KEY` | Django security token. | Automatically generated if not supplied, or set to a custom string. |
| `DEBUG` | Django debug toggle. | Set to `False` in production. |
| `ALLOWED_HOSTS` | Allowed domain name header. | Set to `emitra-backend.onrender.com` (or your custom domain). |

---

## 2. Deployment Instructions

Follow these steps to deploy the application on Render:

### Step 1: Push Code to GitHub
Ensure all code and configurations (`render.yaml`, `Procfile`, and `build.sh`) are pushed to a repository on your GitHub account.

### Step 2: Create a Render Blueprint
1. Go to the [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Blueprint**.
3. Link your GitHub repository.
4. Render will parse the `render.yaml` configuration file and list the blueprint services:
   - `emitra-db` (PostgreSQL database)
   - `emitra-backend` (Django web service)
   - `emitra-frontend` (Static React site)
5. Click **Apply**.

### Step 3: Monitor Ingestion Build & Migration Logs
1. Open the `emitra-backend` service log on Render.
2. The build command will execute `build.sh` which:
   - Installs dependencies.
   - Applies database migrations.
   - Runs `python seed.py` to bootstrap the default tenant ("Acme Corporation").
3. Note the generated **ORGANIZATION ID** UUID printed in the backend build log.

### Step 4: Configure Frontend Tenant ID
1. Edit [api.js](file:///d:/projects/Emitra/src/services/api.js) line 4:
   ```javascript
   const DEFAULT_ORG_ID = 'your-newly-seeded-org-uuid-here';
   ```
2. Commit and push the change to GitHub. Render will automatically rebuild and deploy the static frontend site.

---

## 3. Post-Deployment Database Seeding & Admin Access
If you need to access the Django admin panel or manually run seeding again:
1. Open the Render Shell for `emitra-backend`.
2. Run:
   ```bash
   python manage.py createsuperuser
   ```
3. Access the admin dashboard at `https://emitra-backend.onrender.com/admin/`.
