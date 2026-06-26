<div align="center">

# 🛡️ AI NOC Copilot 
**The Air-Gapped, Autonomous Command Center for Enterprise Networks**

[![100% Offline](https://img.shields.io/badge/Status-100%25_Offline-success?style=for-the-badge)](#)
[![GPU Accelerated](https://img.shields.io/badge/Compute-NVIDIA_GPU-blue?style=for-the-badge)](#)
[![Model](https://img.shields.io/badge/LLM-Qwen2--7B-orange?style=for-the-badge)](#)
[![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20ChromaDB-blueviolet?style=for-the-badge)](#)

*Predict failures, simulate Root Cause Analysis (RCA), and listen to voice alerts without sending a single byte of telemetry to the cloud.*

### 🎥 [Watch the Full Demo Video Here!](https://drive.google.com/file/d/1gPec0Sj5l7fn3P3PfbpWjmFc9EavsRTC/view?usp=drive_link)

---

<!-- Add your screenshot here! Just drag and drop it into GitHub -->
![NOC Dashboard Screenshot Placeholder](https://via.placeholder.com/1000x500.png?text=Add+Your+Stunning+Dashboard+Screenshot+Here)

</div>

<br>

> [!IMPORTANT]
> **Enterprise-Grade Security:** This project was built from the ground up to operate in highly classified, air-gapped environments. It runs entirely on local silicon. No OpenAI API. No internet dependency. Zero data exfiltration.

## 🚨 The Problem

Modern Network Operations Centers (NOCs) managing complex SD-WAN and MPLS underlays suffer from two major issues:
1. **Reactive Tooling:** Engineers only start diagnosing *after* the dashboard turns red or the SLA is breached.
2. **Security Constraints:** In enterprise, government, or critical infrastructure environments, sending sensitive network telemetry or routing tables to public cloud APIs (like OpenAI) is strictly prohibited.

## 💡 The Solution

The **AI NOC Copilot** is a 100% air-gapped, autonomous AI agent that ingests enterprise networking documentation and diagnoses network failures in real-time. It doesn't just answer questions; it simulates autonomous Root Cause Analysis (RCA), predicts failures, and communicates via voice—all while completely disconnected from the internet.

---

## ✨ Full Feature Overview

We built a massive suite of features across UI, AI, and backend architectures to create a $100k enterprise product feel.

### 🎭 The "Wow-Factor" Features (Grand Prize Additions)
*   **🎤 Voice Synthesis:** Uses native browser APIs to physically speak critical alerts aloud to the NOC operator, simulating a real command center.
*   **🧠 Autonomous RCA Chain:** Streams its step-by-step thinking process live on screen (e.g., *Querying RAG... Cross-referencing telemetry...*) before providing the final answer.
*   **⏱️ Predictive Timeline:** A reactive UI element that visually maps the trajectory from *System Stress* to *Predicted Outage*.
*   **📊 RAG Confidence Meter:** Calculates and displays a visual confidence score (e.g., `[████████░░] 87%`) based on the relevance of the retrieved vectors.
*   **📄 1-Click Offline Export:** Generates professional, timestamped incident diagnostic reports locally (.txt format) for compliance logging.

### 🖥️ Dynamic & Reactive Interface
*   **Reactive Network Status Bar:** Shows Latency, Packet Loss, Active Tunnels, BGP Peers, and Threat Level. Metrics react and spike instantly (e.g., latency jumps to 340ms and turns red) when simulated scenarios are triggered.
*   **Live Alert Feed:** A scrolling marquee of simulated incoming Syslog/SNMP alerts (Info/Warning/Critical) that brings the dashboard to life.
*   **Severity Badging:** The LLM automatically classifies its diagnostic response with a colored severity badge (🔴 CRITICAL, 🟡 WARNING, 🟢 INFO).
*   **Response Analytics:** Displays inference speed ("Diagnosed in 3.4s") and tracks the exact source document used to generate the answer.
*   **Interactive Architecture Modal:** A sleek UI modal that breaks down the system architecture visually.
*   **Mobile Responsiveness:** A full-screen UI that perfectly adapts to mobile phones and iPads for on-the-go viewing.

---

## 🏗️ Architectural Design & RAG Logic

```mermaid
graph LR
    A[NOC Operator] -->|Browser UI| B(FastAPI Server)
    B -->|Query| C[(ChromaDB Vault)]
    C -->|Retrieved Vectors| D[SentenceTransformers]
    D -->|Context Prompt| E{Qwen2-7B Model}
    E -->|SSE Stream| B
    B -->|Real-time Markdown| A
    
    style A fill:#0f172a,stroke:#06b6d4,stroke-width:2px,color:#fff
    style B fill:#0f172a,stroke:#3b82f6,stroke-width:2px,color:#fff
    style C fill:#0f172a,stroke:#10b981,stroke-width:2px,color:#fff
    style E fill:#0f172a,stroke:#f59e0b,stroke-width:2px,color:#fff
