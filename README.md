🛡️ AI NOC Copilot (Air-Gapped Enterprise Edition)
Autonomous SD-WAN & MPLS Diagnostics for Highly Secure Environments

100% Offline
 
GPU Accelerated
 
Model
 
Stack


🚨 The Problem
Modern Network Operations Centers (NOCs) managing complex SD-WAN and MPLS underlays suffer from two major issues:

Tooling is Reactive: Engineers only start diagnosing after the dashboard turns red or the SLA is breached.
Security Constraints: In enterprise, government, or critical infrastructure environments, sending sensitive network telemetry or routing tables to public cloud APIs (like OpenAI) is strictly prohibited.
💡 Our Solution
The AI NOC Copilot is a 100% air-gapped, autonomous AI agent that ingests enterprise networking documentation and diagnoses network failures in real-time. It doesn't just answer questions; it simulates autonomous Root Cause Analysis (RCA), predicts failures, and communicates via voice—all while completely disconnected from the internet.

✨ "Wow-Factor" Features
🎤 Autonomous Voice Synthesis: Uses native browser APIs to physically speak critical alerts and diagnostic results aloud to the NOC operator.
🧠 Simulated RCA Reasoning Chain: Autonomously streams its step-by-step thinking process (e.g., Querying RAG... Cross-referencing telemetry...) before answering.
⏱️ Predictive Failure Timeline: A reactive UI element that visually maps the trajectory from System Stress to Predicted Outage.
📊 RAG Confidence Meter: Calculates and displays a visual confidence score based on the relevance of the retrieved vector knowledge.
📄 Instant PDF/TXT Export: Generates professional, timestamped incident diagnostic reports locally for compliance logging.
🏗️ Architectural Design
Our architecture was designed with a strict Zero-Internet policy. Every component runs locally on a SLURM-managed High-Performance Computing (HPC) cluster.

Frontend UI (The Command Center): Pure HTML/CSS/JS. No external CDNs. Features Server-Sent Events (SSE) to consume real-time LLM token streams.
Backend Orchestrator: FastAPI serving endpoints for UI rendering and asynchronous LLM streaming.
Knowledge Retrieval (RAG): ChromaDB stores 199 dense vectors generated from Cisco SD-WAN CVDs and AWS Connectivity guides using SentenceTransformers.
The Brain (LLM): Qwen2-7B running locally via HuggingFace Transformers and PyTorch on an NVIDIA GPU, utilizing TextIteratorStreamer for zero-latency output.
🧗 Challenges We Faced & Overcame
Building a modern AI app in a restricted HPC environment presented unique hurdles:

The SQLite3 Vector Database Crisis
Challenge: ChromaDB requires a modern SQLite3 version to run, but our college's shared HPC login nodes had an outdated OS-level SQLite binary that we lacked sudo permissions to update.
Solution: We engineered a dynamic Python monkey-patch using pysqlite3-binary to inject a modern SQLite runtime into the system modules (sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')) before ChromaDB booted.
Zero-Latency Streaming in an Air-Gapped Sandbox
Challenge: Generating 1024 tokens locally can take several seconds. Waiting for the full generation ruined the "real-time" copilot illusion.
Solution: We decoupled the LLM generation into a background threading.Thread and attached a TextIteratorStreamer. We then piped those tokens through a FastAPI Server-Sent Event (SSE) generator, achieving instant typewriter-effect rendering in the browser.
Creating "Wow" without the Web
Challenge: We wanted massive visual and auditory impact (PDFs, Voice, Graphs) but couldn't npm install complex libraries or hit external APIs.
Solution: We aggressively utilized native browser features. We wrote custom vanilla CSS for the predictive timelines and leveraged window.speechSynthesis for offline robotic voice alerts.
🚀 The Journey & Process
This project evolved rapidly during the hackathon:

Phase 1 (Data): Downloaded and chunked dense networking PDFs into local embeddings.
Phase 2 (Infrastructure): Battled the SLURM cluster to get GPU nodes mapped correctly to our RAG pipeline.
Phase 3 (Integration): Built the FastAPI bridge to connect the Vector DB to the LLM.
Phase 4 (UX Polish): Realized that a simple "chat box" isn't impressive. We pivoted to building an immersive, dark-mode NOC dashboard with reactive metrics, scrolling syslog alerts, and voice readouts to simulate a live enterprise command center.
🔭 Future Scope
To transition this from a Hackathon prototype to a deployed Enterprise System, the Q3 Roadmap includes:

Live Telemetry Ingestion: Replacing simulated metrics by integrating Logstash/Fluentd to ingest live NetFlow, SNMP traps, and Syslogs directly from physical routers.
Closed-Loop Auto-Remediation: Upgrading the agent from purely diagnostic to active execution. The Copilot will use Netmiko or Ansible to securely SSH into routers and apply CLI fixes autonomously after human approval.
ITSM Integration: Automatic API hooks into ServiceNow and Jira to open tickets and attach the generated diagnostic reports instantly.
Massive Scale Knowledge Base: Expanding the ChromaDB vault from 2 PDFs to thousands of internal enterprise wikis, historical closed tickets, and complete vendor documentation libraries.
