# Hosted console (GCP)

How the **web** console is deployed. Local desk stays [`dev.md`](dev.md) (`make demo`). No ADR for this path yet.

This is a **hosted shell**, not a live shift: `/api` has no backend until api/worker/sim land. The list will not fill.

## What is hosted

| Piece | Now | Later |
|-------|-----|--------|
| `web` | Cloud Run, public URL | same; `API_UPSTREAM` → api |
| api / worker / sim | absent | Cloud Run |
| Postgres | Cloud SQL `city-os` (Enterprise, `db-f1-micro`, `asia-southeast1`) | same |

## Project

| | |
|---|---|
| Project | `city-os-509403` (`city-os`) |
| Region | `asia-southeast1` (Singapore) |
| Artifact Registry | `desk` |
| Cloud Run service | `web` |
| Cloud SQL | `city-os` (connection `city-os-509403:asia-southeast1:city-os`) |
| DB password secret | `city-os-db-password` (do not put in git or chat) |

Images: `asia-southeast1-docker.pkg.dev/city-os-509403/desk/web:<sha>`.

## How `main` deploys

Push to `main` → Cloud Build (`cloudbuild.yaml`) → build `apps/web/Dockerfile` → push `desk/web` → `gcloud run deploy web`.

Caddy serves the Vite `dist` and strips `/api` toward `API_UPSTREAM` (default unused → 502). Same browser-origin shape as Vite in [`../apps/web/vite.config.ts`](../apps/web/vite.config.ts).

## One-time (empty project)

APIs already enabled on this project: Run, SQL, Artifact Registry, Cloud Build, Secret Manager, Compute.

```bash
gcloud config set project city-os-509403

gcloud artifacts repositories create desk \
  --repository-format=docker \
  --location=asia-southeast1 \
  --description="Desk container images"

# Cloud Build SA needs push + Cloud Run deploy (replace PROJECT_NUMBER).
PROJECT_NUMBER="$(gcloud projects describe city-os-509403 --format='value(projectNumber)')"
gcloud projects add-iam-policy-binding city-os-509403 \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role=roles/run.admin
gcloud projects add-iam-policy-binding city-os-509403 \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role=roles/artifactregistry.writer
gcloud iam service-accounts add-iam-policy-binding \
  "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role=roles/iam.serviceAccountUser
```

2nd-gen connection (region must match the trigger). Cloud Build Service Agent needs `roles/secretmanager.admin` so it can store the GitHub OAuth token. Then:

```bash
gcloud builds connections create github github \
  --project=city-os-509403 \
  --region=asia-southeast1
# Follow the printed OAuth URL; wait until installationState.stage is COMPLETE.

gcloud builds repositories create smart-city-os \
  --remote-uri=https://github.com/cheslav-zhur/smart-city-os.git \
  --connection=github \
  --region=asia-southeast1 \
  --project=city-os-509403

# 2nd-gen trigger requires a user-managed service account (compute default SA here).
gcloud builds triggers create github \
  --name=web-main \
  --repository=projects/city-os-509403/locations/asia-southeast1/connections/github/repositories/smart-city-os \
  --branch-pattern='^main$' \
  --build-config=cloudbuild.yaml \
  --region=asia-southeast1 \
  --project=city-os-509403 \
  --service-account=projects/city-os-509403/serviceAccounts/174386330501-compute@developer.gserviceaccount.com
```

`--region` on the trigger is the Cloud Build trigger region, not the Run region. If the GitHub connection lives in another region, match that.

Manual first deploy (same as the trigger, without waiting for `main`):

```bash
gcloud builds submit --config=cloudbuild.yaml --project=city-os-509403
```

## After deploy

Console URL: Cloud Run → `web` → URL. `/api/*` is 502 until api exists. Set `API_UPSTREAM` on the `web` service when that lands (private Run URL).

## Spend

Cloud SQL `city-os` bills while the instance exists, even with no traffic. Cloud Run `web` without `min-instances` is near-zero idle. Stop SQL when the hosted desk is not needed:

```bash
gcloud sql instances patch city-os --activation-policy=NEVER --project=city-os-509403
```

Start again: `--activation-policy=ALWAYS`.
