# Leadership Intelligence Agent (ExecutiveIntel.ai)
## Product Definition, Architecture & Investor / Executive Pitch Deck

---

## 1. Executive Summary & Vision
**Leadership Intelligence Agent** is an autonomous enterprise B2B intelligence platform powered by **Google Gemini 2.5 Flash**, **Vertex AI**, and **Google Cloud Firestore**. 

It replaces costly, stale, and fragmented executive data vendors (e.g., ZoomInfo, BoardEx, PitchBook) by autonomously scraping, verifying, synthesizing, and vector-indexing C-Suite leadership, Board of Directors governance, verified contact points, official social signals, SEC DEF 14A proxy compensation, and strategic ecosystem graphs in real time.

---

## 2. The Problem
1. **Stale B2B Databases**: Traditional data providers sell scraped records that are months or years out of date. High executive turnover makes static databases untrustworthy.
2. **Missing Strategic Context**: Sales and business development teams don't just need an email; they need to understand an executive's board committees, recent public statements, active strategic partners, and direct competitors.
3. **Prohibitive Cost**: Enterprise data licenses range from $15,000 to $100,000+ annually for rigid seat-based access.
4. **Disjointed Workflows**: Moving discovered leads into Salesforce or HubSpot requires manual data entry and human cross-referencing.

---

## 3. The Solution: Autonomous Multi-Modal Agent
An intelligent serverless application that turns a single company name or domain into a 360-degree executive profile in **under 3.5 seconds**:
- **Zero-Latency Ingestion**: High-speed web scraping + Wikipedia + public records.
- **Deep Cognitive Synthesis**: Gemini 2.5 Flash on Vertex AI extracts names, titles, governance roles, corporate emails, verified X handles, and the last 3 public announcements.
- **Ecosystem Mapping**: Extracts active strategic partners (with links) and direct market competitors (with positioning).
- **SEC Filing Intelligence**: Synthesizes executive compensation and board committee data from Form DEF 14A proxy statements.
- **Dynamic Creative Branding**: Vertex AI Imagen 3 / Flash-Image generates custom, cheerful vector logos for every organization.
- **Semantic Vector Talent Discovery**: Natural-language RAG search allowing recruiters to search by skills and board requirements (e.g. *"board member with cybersecurity in fintech"*).
- **Enterprise CRM Gateway**: Native webhooks push clean intelligence directly into HubSpot or Salesforce with 1 click.

---

## 4. Product Pitch Deck (10-Slide Investor & Executive Presentation)

### Slide 1: Title & Vision
* **Headline**: ExecutiveIntel: Autonomous Leadership & Competitive Intelligence
* **Sub-headline**: Real-time C-Suite, Board Governance, and Ecosystem Discovery powered by Google Gemini 2.5.
* **Presenter**: Manraj Shekar

### Slide 2: The Market Problem
* **The Stale Data Crisis**: 25% of executive positions turn over annually. Static B2B databases decay faster than vendors can refresh them.
* **The Cost Barrier**: Enterprises spend tens of thousands of dollars on fragmented tools just to piece together leadership lists, emails, and competitor benchmarks.

### Slide 3: The Solution
* **Autonomous Real-Time Synthesis**: Enter any domain or company name $\rightarrow$ our Gemini agent crawls, verifies, synthesizes, and stores comprehensive profiles in seconds.
* **Instant Cache + Real-Time Fallback**: Firestore Native database delivers sub-50ms reads on indexed organizations, with autonomous real-time discovery for new queries.

### Slide 4: Key Capabilities & Differentiators
1. **C-Suite & Board Governance**: Clear separation between operational leadership and independent board oversight.
2. **Contact & Social Verification**: Corporate email discovery + verified individual and company X handles with recent public statements.
3. **Ecosystem & Competitive Mapping**: Live partner graphs and competitor benchmark cards with direct URLs.
4. **SEC DEF 14A Compensation Radar**: Governance committee assignments and compensation benchmarks.
5. **AI Vector Talent Search**: Natural language semantic discovery across executive skillsets.

### Slide 5: Product Architecture (GCP Cloud-Native)
* **Frontend**: Responsive, modern glassmorphic Web UI + Operations Admin Dashboard.
* **Backend**: High-concurrency FastAPI running on serverless Google Cloud Run.
* **AI Cognitive Tier**: Google Gemini 2.5 Flash (`us-central1`) via the Google GenAI SDK.
* **Generative Creative Tier**: Imagen 3 / Flash-Image vector branding engine.
* **Persistence Tier**: Google Cloud Firestore (Native Mode) for sub-50ms document reads.
* **Storage Tier**: Google Cloud Storage (GCS) for public asset delivery.

### Slide 6: Business & Revenue Model
* **Freemium Tier**: 50 company searches / month free.
* **Growth Tier ($99/mo)**: Unlimited searches, batch CSV ingestion (up to 500 domains/batch), full CSV/JSON data export.
* **Enterprise Tier ($499/mo)**: Dedicated CRM Webhooks (Salesforce / HubSpot), automated weekly competitor digest reports, custom vector RAG indexing.

### Slide 7: Unit Economics & Margins
* **Average Cost per Company Discovery**:
  - Gemini 2.5 Flash input/output tokens: **~$0.0005**
  - Custom Imagen logo generation: **~$0.030**
  - Firestore storage & Cloud Run compute: **~$0.0001**
  - **Total Cost of Discovery: ~$0.031 per organization**
* **Gross Margin**: **> 92%** on subscription revenue.

### Slide 8: Go-to-Market Strategy
1. **B2B Outbound Sales Teams (SDRs/AEs)**: Accelerating pre-call account research from 30 minutes to 3 seconds.
2. **Executive Search & Talent Recruiters**: Leveraging the Semantic Vector Search for board member placements.
3. **Private Equity & Corporate Venture Capital**: Conducting rapid competitive landscape and ecosystem audits.

### Slide 9: Product Roadmap
- **Q1**: Live LinkedIn profile scraping and real-time email MX record ping verification.
- **Q2**: Automatic SEC EDGAR 10-K financial metric parsing (revenue, EBITDA, employee headcount).
- **Q3**: Chrome Extension for on-the-fly intelligence while browsing LinkedIn or company websites.
- **Q4**: Real-time executive job change alert webhooks.

### Slide 10: The Ask & Conclusion
* **Status**: Fully functional MVP deployed on Google Cloud Run with verified customer catalog.
* **Next Steps**: Expand ingestion pipelines, scale user onboarding, and integrate native Salesforce AppExchange package.

---

## 5. Instructions for Continuing Beyond the Classroom

### 5.1 Prerequisites on Your Personal Machine
1. **Install Git**: `brew install git` (Mac) or `sudo apt install git` (Linux) or download from [git-scm.com](https://git-scm.com).
2. **Install Python 3.11+**: Ensure Python and `pip` are installed.
3. **Install Google Cloud SDK (`gcloud`)**:
   Follow instructions at [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install).

---

### 5.2 Clone Your Personal GitHub Repository
```bash
git clone https://github.com/manrajshekar-gt/buildwithgemini-leadership-intel-agent.git
cd buildwithgemini-leadership-intel-agent
```

---

### 5.3 Configure Your Personal Google Cloud Account ($300 Free Credits)
1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project (e.g. `my-leadership-intel-prod`).
2. Log in and configure your local CLI:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   gcloud config set project YOUR_PERSONAL_PROJECT_ID
   ```
3. Enable necessary APIs:
   ```bash
   gcloud services enable \
     run.googleapis.com \
     firestore.googleapis.com \
     storage.googleapis.com \
     aiplatform.googleapis.com \
     cloudbuild.googleapis.com
   ```
4. Create your Firestore Native Database and Assets Storage Bucket:
   ```bash
   # Create Firestore Database in us-central1
   gcloud firestore databases create --location=us-central1 --type=firestore-native

   # Create Cloud Storage bucket for company logos
   gcloud storage buckets create gs://leadership-intel-assets-YOUR_PERSONAL_PROJECT_ID --location=us-central1
   
   # Make bucket objects publicly viewable
   gcloud storage buckets add-iam-policy-binding gs://leadership-intel-assets-YOUR_PERSONAL_PROJECT_ID \
     --member=allUsers --role=roles/storage.objectViewer
   ```

---

### 5.4 Running the Application Locally
Create a Python virtual environment and launch FastAPI:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r frontend/requirements.txt

# Set your personal GCP project environment variables
export GOOGLE_CLOUD_PROJECT="YOUR_PERSONAL_PROJECT_ID"
export ASSET_BUCKET_NAME="leadership-intel-assets-YOUR_PERSONAL_PROJECT_ID"
export GOOGLE_GENAI_USE_VERTEXAI="true"

# Start the uvicorn development server
uvicorn main:app --app-dir frontend --host 0.0.0.0 --port 8080 --reload
```
Open **`http://localhost:8080`** for the Search Portal and **`http://localhost:8080/admin.html`** for the Admin & Telemetry Operations Dashboard.

---

### 5.5 Deploying to Cloud Run in Your Personal Account
Whenever you want to deploy your changes to a permanent public HTTPS URL:
```bash
cd frontend
gcloud run deploy leadership-portal \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=YOUR_PERSONAL_PROJECT_ID,ASSET_BUCKET_NAME=leadership-intel-assets-YOUR_PERSONAL_PROJECT_ID,GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_LOCATION=us-central1"
```
Cloud Run will build the container with Cloud Build and output your live production URL.
