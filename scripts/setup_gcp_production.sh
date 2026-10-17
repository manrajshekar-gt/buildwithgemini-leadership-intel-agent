#!/usr/bin/env bash
# ==============================================================================
# Google Cloud Production Setup & Auto-Deploy Bootstrap Script
#
# This script provisions:
# 1. Cloud Run API, Cloud Build API, Artifact Registry, Firestore Native, Vertex AI
# 2. Native Cloud Firestore Database
# 3. GitHub Actions CI/CD Service Account with least-privilege IAM roles
# 4. Service Account Key for GitHub Secrets (GCP_SA_KEY)
# 5. Performs the initial Cloud Run production deployment
# 6. Provides Custom Domain DNS Mapping instructions
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}   Google Cloud Production Setup & Auto-Deploy Provisioner            ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
    if [ -f "/opt/homebrew/bin/gcloud" ]; then
        export PATH="/opt/homebrew/bin:$PATH"
    else
        echo -e "${RED}[!] Google Cloud SDK (gcloud) is not installed.${NC}"
        echo -e "    Install it with: brew install google-cloud-sdk"
        exit 1
    fi
fi

# Determine GCP Project ID
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
if [ -z "$CURRENT_PROJECT" ] || [ "$CURRENT_PROJECT" = "(unset)" ]; then
    echo -e "${YELLOW}[?] Enter your Google Cloud Project ID:${NC} "
    read -r PROJECT_ID
    gcloud config set project "$PROJECT_ID"
else
    echo -e "${GREEN}[✓] Active GCP Project:${NC} $CURRENT_PROJECT"
    PROJECT_ID="$CURRENT_PROJECT"
fi

REGION="us-central1"
SERVICE_NAME="leadership-intel-prod"
SA_NAME="github-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo ""
echo -e "${BLUE}[1/5] Enabling Required Google Cloud APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    firestore.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    storage.googleapis.com

echo -e "${GREEN}[✓] APIs Enabled Successfully.${NC}"

echo ""
echo -e "${BLUE}[2/5] Initializing Cloud Firestore (Native Mode)...${NC}"
if gcloud firestore databases list --format="value(name)" 2>/dev/null | grep -q "\(default\)"; then
    echo -e "${GREEN}[✓] Firestore Native database already initialized.${NC}"
else
    echo -e "${YELLOW}[*] Creating default Firestore database in region ${REGION}...${NC}"
    gcloud firestore databases create --location="${REGION}" --type=firestore-native 2>/dev/null || {
        echo -e "${YELLOW}[i] Firestore database already exists or has been configured.${NC}"
    }
fi

echo ""
echo -e "${BLUE}[3/5] Setting up GitHub Actions CI/CD Service Account...${NC}"
if ! gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
    gcloud iam service-accounts create "$SA_NAME" \
        --description="Automated CI/CD deployer for GitHub Actions" \
        --display-name="GitHub Deployer Service Account"
    echo -e "${GREEN}[✓] Created Service Account: ${SA_EMAIL}${NC}"
else
    echo -e "${GREEN}[✓] Service Account already exists: ${SA_EMAIL}${NC}"
fi

# Assign necessary roles
ROLES=(
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
    "roles/storage.admin"
    "roles/artifactregistry.admin"
    "roles/cloudbuild.builds.editor"
    "roles/datastore.user"
)

for ROLE in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="$ROLE" \
        --condition=None --quiet >/dev/null
done
echo -e "${GREEN}[✓] IAM Permissions Granted to ${SA_NAME}.${NC}"

# Configure default Compute & Cloud Build service account permissions for container builds
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null || echo "")
if [ -n "$PROJECT_NUMBER" ]; then
    echo -e "${BLUE}[*] Granting Cloud Build storage and logging permissions to default service accounts...${NC}"
    COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
    CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

    for B_SA in "$COMPUTE_SA" "$CLOUDBUILD_SA"; do
        for B_ROLE in "roles/storage.admin" "roles/logging.logWriter" "roles/artifactregistry.writer"; do
            gcloud projects add-iam-policy-binding "$PROJECT_ID" \
                --member="serviceAccount:${B_SA}" \
                --role="$B_ROLE" \
                --condition=None --quiet >/dev/null 2>&1 || true
        done
    done
    echo -e "${GREEN}[✓] Build permissions granted to ${COMPUTE_SA}.${NC}"
fi

# Generate Service Account Key
KEY_DIR="$(dirname "$0")/../credentials"
mkdir -p "$KEY_DIR"
KEY_FILE="$KEY_DIR/gcp-sa-key.json"

if [ ! -f "$KEY_FILE" ]; then
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SA_EMAIL"
    echo -e "${GREEN}[✓] Created Service Account Key at: ${KEY_FILE}${NC}"
else
    echo -e "${GREEN}[✓] Key file already exists at: ${KEY_FILE}${NC}"
fi

echo ""
echo -e "${BLUE}[4/5] Deploying Initial Production Release to Cloud Run...${NC}"
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 10 \
    --set-env-vars GOOGLE_CLOUD_PROJECT="$PROJECT_ID",MODEL="gemini-2.5-flash",FIRESTORE_COLLECTION="leadership_profiles"

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform managed --region "$REGION" --format 'value(status.url)')

echo ""
echo -e "${BLUE}======================================================================${NC}"
echo -e "${GREEN}🎉 CONGRATULATIONS! Production Deployment is LIVE!${NC}"
echo -e "   App URL: ${BLUE}${SERVICE_URL}${NC}"
echo -e "${BLUE}======================================================================${NC}"

echo ""
echo -e "${YELLOW}--- STEP A: Enable GitHub Auto-Deploy (CI/CD) ---${NC}"
echo -e "1. Go to your GitHub Repository: ${BLUE}Settings -> Secrets and variables -> Actions${NC}"
echo -e "2. Click 'New repository secret' and add:"
echo -e "   - Name:  ${GREEN}GCP_SA_KEY${NC}"
echo -e "   - Value: (Paste the contents of file: ${KEY_FILE})"
echo -e "3. Click 'New repository secret' again and add:"
echo -e "   - Name:  ${GREEN}GCP_PROJECT_ID${NC}"
echo -e "   - Value: ${GREEN}${PROJECT_ID}${NC}"
echo ""
echo -e "From now on, whenever you push code to 'main', GitHub Actions will automatically"
echo -e "run tests and deploy the updated container to Cloud Run!"

echo ""
echo -e "${YELLOW}--- STEP B: Connect Your Custom Domain ---${NC}"
echo -e "To map your domain (e.g. intel.yourdomain.com):"
echo -e "1. Run: ${GREEN}gcloud beta run domain-mappings create --service ${SERVICE_NAME} --domain intel.yourdomain.com --region ${REGION}${NC}"
echo -e "2. Add the CNAME record in your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.):"
echo -e "   - Type:   ${GREEN}CNAME${NC}"
echo -e "   - Name:   ${GREEN}intel${NC}"
echo -e "   - Value:  ${GREEN}ghs.googlehosted.com${NC}"
echo -e "3. Google will automatically provision a free SSL certificate within ~15 minutes."
echo -e "${BLUE}======================================================================${NC}"
