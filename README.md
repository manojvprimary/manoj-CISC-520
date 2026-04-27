# Animal Rescue Research Assistant

An AI-powered research assistant for analyzing animal shelter and rescue data. Built with a Flask backend (Claude API) and a React frontend, deployed on Google Cloud Run.

CISC 520 — Data Engineering and Mining

Research Assitant: https://research-assistant-app-636745240622.us-central1.run.app/

## Architecture

```
research-assistant/
├── backend/               Flask API server
│   ├── main.py            App entry point and routes
│   ├── agent.py           Claude API agent loop (streaming + non-streaming)
│   ├── tools.py           Tool implementations (dataset loading, Python execution, NYC API)
│   ├── config.py          System prompt, tool definitions, constants
│   ├── data/              Local CSV datasets (SAC national shelter stats)
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/              React chat UI
    ├── src/
    │   ├── App.js         Main app component (chat logic, SSE streaming)
    │   ├── App.css        Styles (dark theme)
    │   ├── config.js      Backend URL and example prompts
    │   └── components/
    │       ├── Message.js      Chat message rendering (markdown, plots, tool pills)
    │       ├── CodeBlock.js    Syntax-highlighted code display with copy button
    │       ├── CodeModal.js    Full-screen code viewer
    │       ├── DataModal.js    Dataset sample table viewer
    │       └── ToolPill.js     Tool execution status indicator
    ├── Dockerfile
    └── nginx.conf
```

## Available Datasets

| Name | Source | Description |
|------|--------|-------------|
| `sac_national` | Local CSV | National US shelter stats by state (2024-2025) |
| `austin_shelter` | Kaggle | Austin Animal Center intake/outcome history |
| `adoption_prediction` | Kaggle | Pet adoption status prediction dataset |
| `animal_welfare` | Kaggle | Multi-organization animal welfare benchmarks |
| `animal_care` | Kaggle | Animal care metrics across shelter networks |
| `shelter_analytics` | Kaggle | Shelter analytics and operational data |
| `petfinder_db` | Kaggle | Petfinder animal shelter database |
| NYC live data | NYC Open Data API | Real-time NYC Animal Care & Control reports |

Users can also upload their own CSV files for analysis.

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

### Backend

```bash
cd research-assistant/backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"
python main.py
```

The backend runs on `http://localhost:8080`.

### Frontend

```bash
cd research-assistant/frontend
npm install
npm start        # dev server on http://localhost:3000
npm run build    # production build
```

Update `BACKEND_URL` in `src/config.js` to point to your backend (defaults to the Cloud Run deployment URL).

## Deployment (Google Cloud Run)

### Prerequisites

1. **Google Cloud account** with a project created. Note your project ID.
2. **Google Cloud CLI (`gcloud`)** installed — [install guide](https://cloud.google.com/sdk/docs/install).
3. **Docker** installed (Cloud Run source deploys use Cloud Build, but Docker is needed for local testing).
4. **Anthropic API key** from [console.anthropic.com](https://console.anthropic.com/).

### Authenticate and Configure GCP

```bash
# Log in to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable the required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Deploy the Backend

```bash
cd research-assistant/backend

gcloud run deploy research-assistant \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY="your-key-here"
```

This builds the Docker image via Cloud Build and deploys it to Cloud Run. Note the service URL in the output (e.g., `https://research-assistant-XXXXXX.us-central1.run.app`).

### Deploy the Frontend

Before deploying, update `BACKEND_URL` in `src/config.js` to point to the backend service URL from the previous step.

```bash
cd research-assistant/frontend

gcloud run deploy research-assistant-app \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

The frontend service URL in the output is your live application URL.

### Local Docker (Optional)

You can also run both services locally with Docker:

```bash
# Backend
cd research-assistant/backend
docker build -t research-assistant-backend .
docker run -p 8080:8080 -e ANTHROPIC_API_KEY="your-key" -e PORT=8080 research-assistant-backend

# Frontend (in a separate terminal)
cd research-assistant/frontend
docker build -t research-assistant-frontend .
docker run -p 3000:8080 research-assistant-frontend
```

## How It Works

1. User sends a question via the chat UI
2. The backend streams the request to Claude (Opus 4.7) with tool definitions
3. Claude decides which tools to call (load dataset, run Python code, fetch NYC data)
4. Tool results are fed back to Claude in a loop (up to 8 iterations)
5. Claude's text responses and generated charts stream back to the frontend via SSE

## Use of AI Tools

### Tools Used

| Tool | Mode of Use |
|------|-------------|
| **Claude Code** (Anthropic CLI) | Primary development tool — agentic code generation, refactoring, debugging, and deployment automation |
| **Claude.ai** (Anthropic web) | Design discussions, system prompt iteration, and report drafting |
| **GitHub Copilot** | Inline code completion during manual edits in VS Code |

### How AI Was Used

- **Agentic code generation** — The majority of the backend was developed through multi-turn sessions with Claude Code. This includes the Flask routes (`main.py`), the agentic tool-use loop (`agent.py`), all three tool implementations in `tools.py`, and the system prompt and tool schemas in `config.py`. Claude Code generated code, ran it, diagnosed errors from tracebacks, and iterated — often completing multi-file features in a single session.
- **Frontend development** — The React chat UI (`App.js`), all five components (`Message.js`, `CodeBlock.js`, `CodeModal.js`, `DataModal.js`, `ToolPill.js`), and the CSS styling were generated with Claude Code. The SSE streaming integration and markdown rendering setup (react-markdown + remark-gfm) were built through iterative prompting and testing.
- **Debugging** — Claude Code was used to debug issues including: the matplotlib plot-capture workaround for headless subprocesses, multi-level CSV header flattening for the SAC national dataset, CORS configuration between frontend and backend containers, and Docker build issues during Cloud Run deployment.
- **Deployment** — Docker configurations (both Dockerfiles, nginx.conf) and Google Cloud Run deployment commands were generated and iterated on with Claude Code, including troubleshooting container startup failures and environment variable configuration.
- **System prompt design** — The system prompt in `config.py` was iteratively refined through conversations on Claude.ai, testing different prompt structures and constraint phrasings to improve tool selection accuracy and output quality.
- **Report and documentation** — The project report and this README were drafted and refined with Claude Code.

### What Was Done Manually

Project scoping and dataset selection, testing all chat interactions and verifying output correctness against the underlying data, UX design decisions (dark theme, example prompts, tool pill design), and all final review and editing of AI-generated code and documentation.
