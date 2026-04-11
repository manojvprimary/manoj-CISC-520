# 🐾 AI-Powered Animal Rescue Assistant

## 🔗 Live Demo (Milestone 1)

AI Assistant: https://research-assistant-app-636745240622.us-central1.run.app 


---

## 📌 Project Overview

This project aims to build an **AI-powered assistant for animal rescue research and operations**.

The system will allow users to:

* Analyze animal rescue trends using natural language
* Generate charts, statistics, and insights
* Report stray animals and find nearby services (future scope)

---

## 🚀 Milestone 1: Current Capabilities

At this stage, the system demonstrates a **working end-to-end AI pipeline**:

### ✅ What the assistant can do now

* Accept natural language input via a chat interface
* Send user queries to a backend API deployed on Cloud Run
* Call an LLM to generate responses
* Return responses in real-time to the UI

### 🧠 Behavior

* For **animal rescue / analysis-related queries**:

  * Returns a placeholder response describing upcoming features
* For **general queries** (e.g., jokes, facts):

  * Responds normally using the LLM

---

## 🏗️ System Architecture

```
React Frontend (Cloud Run)
        ↓
Flask Backend API (Cloud Run)
        ↓
LLM API (OpenRouter)
        ↓
Response returned to UI
```

---

## 🔁 End-to-End Flow

1. User enters a message in the React chat UI
2. Frontend sends a POST request to `/chat` endpoint
3. Backend receives the request and constructs an LLM prompt
4. LLM generates a response based on:

   * system instructions
   * user input
5. Backend returns the response
6. Frontend renders it in the chat interface

---

## 🧰 Tech Stack

### Frontend

* React
* Axios

### Backend

* Flask
* Gunicorn

### AI / LLM

* OpenRouter (Mixtral model)

### Infrastructure

* Google Cloud Platform

  * Cloud Run (frontend + backend)

---

## 📦 Repository Structure

```
research-assistant/
├── backend/
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
└── frontend/
    ├── src/
    ├── Dockerfile
    └── nginx.conf
```

---

## ⚠️ Limitations (Milestone 1)

* No data analysis or chart generation yet
* No tool-based agent behavior yet
* No persistent memory (conversation history handled in frontend only)

---

## 🔮 Future Work

* Implement tool-based agent (code execution for data analysis)
* Add dataset for animal rescue trends
* Enable chart generation (matplotlib)
* Add reporting and location-based features
* Improve UI/UX (chat history, streaming, etc.)

---

## 🎯 Summary

This milestone establishes a **fully deployed, end-to-end AI system** with:

* a working frontend
* a backend API
* LLM integration

It serves as the foundation for building a more advanced **agentic data analysis assistant** in future milestones.

---
