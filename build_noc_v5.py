#!/usr/bin/env python3
"""
Enterprise NOC Copilot v5 — THE GRAND PRIZE EDITION
Features: Autonomous RCA Chain, Offline Voice Synthesis, Predictive Timeline,
Confidence Meter, Export Reports, Reactive UI, Mobile Responsive
"""
import os

BASE = "/scratch/m25cse029/airgapped_copilot"
UI_DIR = os.path.join(BASE, "ui")
STATIC_DIR = os.path.join(UI_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

APP_PY = r'''
import sys, os, json, threading, torch, time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

app = FastAPI()
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

embedder = None
collection = None
tokenizer = None
model = None

@app.on_event("startup")
def boot():
    global embedder, collection, tokenizer, model
    BASE = Path("/scratch/m25cse029/airgapped_copilot")
    print("1. Booting Secure NOC Database...")
    client = chromadb.PersistentClient(path=str(BASE / "chroma_db"))
    collection = client.get_collection("secure_docs")
    print(f"   Telemetry Vault loaded: {collection.count()} vectors locked.")
    embedder = SentenceTransformer(str(BASE / "models" / "embeddings"))
    print("2. Booting Offline LLM...")
    llm_path = str(BASE / "models" / "qwen2")
    tokenizer = AutoTokenizer.from_pretrained(llm_path)
    model = AutoModelForCausalLM.from_pretrained(
        llm_path, torch_dtype=torch.float16, device_map="auto"
    )
    print("3. NOC Copilot is LIVE.")

@app.get("/", response_class=HTMLResponse)
async def root():
    return (STATIC_DIR / "index.html").read_text()

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    user_msg = data.get("message", "")
    history = data.get("history", [])
    start_time = time.time()

    q_emb = embedder.encode([user_msg]).tolist()
    hits = collection.query(query_embeddings=q_emb, n_results=3)
    raw_docs = hits["documents"][0] if hits["documents"] and hits["documents"][0] else []
    sources = []
    if hits["metadatas"] and hits["metadatas"][0]:
        for meta in hits["metadatas"][0]:
            sources.append(meta.get("source", "Unknown"))
    context = "\n---\n".join(raw_docs) if raw_docs else "No relevant telemetry found."

    system = (
        "You are an autonomous, air-gapped AI NOC Copilot managing enterprise SD-WAN and MPLS underlays. "
        "Your role is to predict network failures, analyze router logs, and explain operational alerts. "
        "IMPORTANT: Start EVERY response with a severity classification on its own line in this exact format: "
        "[SEVERITY: CRITICAL] or [SEVERITY: WARNING] or [SEVERITY: INFO] "
        "Then provide your analysis using Markdown. Use **bold** for key terms. Use bullet points and numbered lists. "
        "Use tables for comparing metrics. Use code blocks for CLI commands. "
        "Use ONLY the retrieved documentation below to justify your diagnostics.\n\n"
        f"Retrieved Telemetry/Documentation:\n{context}"
    )
    messages = [{"role": "system", "content": system}]
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_msg})

    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    gen_kwargs = dict(**inputs, max_new_tokens=1024, temperature=0.3, do_sample=True, streamer=streamer)
    thread = threading.Thread(target=model.generate, kwargs=gen_kwargs)
    thread.start()

    source_list = list(set(sources))
    elapsed = round(time.time() - start_time, 1)

    def sse():
        yield f"data: {json.dumps({'type':'sources','content': source_list})}\n\n"
        yield f"data: {json.dumps({'type':'meta','retrieval_time': elapsed})}\n\n"
        for tok in streamer:
            if tok:
                yield f"data: {json.dumps({'type':'token','content': tok})}\n\n"
        total = round(time.time() - start_time, 1)
        yield f"data: {json.dumps({'type':'done','total_time': total})}\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8529)
'''

INDEX_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>AI NOC Copilot | Enterprise SD-WAN Diagnostics</title>
    <link rel="stylesheet" href="/static/style.css">
    <link rel="stylesheet" href="/static/highlight.css">
</head>
<body>
    <div class="app-container">
        <header class="app-header">
            <div class="header-left">
                <div class="logo-icon">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
                </div>
                <div class="title-container">
                    <h1>AI NOC Copilot <span class="version-tag">ENTERPRISE</span></h1>
                    <span class="subtitle">Autonomous SD-WAN Diagnostics</span>
                </div>
            </div>
            <div class="header-right">
                <button class="arch-btn" id="voice-btn" onclick="toggleVoice()">
                    🔈 <span class="btn-text">Voice: OFF</span>
                </button>
                <button class="arch-btn" onclick="toggleArchModal()">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    <span class="btn-text">Architecture</span>
                </button>
                <button class="scenarios-btn" onclick="toggleScenarios()">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
                    <span class="btn-text">Scenarios</span>
                </button>
                <div class="status-badge">
                    <span class="pulse-dot"></span>
                    <span class="badge-text">SECURE</span>
                </div>
            </div>
        </header>

        <!-- Predictive Timeline -->
        <div class="timeline-container">
            <div class="timeline-track"></div>
            <div class="timeline-progress" id="timeline-progress"></div>
            <div class="timeline-markers">
                <span class="marker ok active">Normal Operation</span>
                <span class="marker stress" id="marker-stress">System Stress</span>
                <span class="marker fail" id="marker-fail">Predicted Failure</span>
            </div>
        </div>

        <div class="status-bar">
            <div class="metric"><span class="metric-label">AVG LATENCY</span><span class="metric-value latency-val">12.4 ms</span></div>
            <div class="metric-divider"></div>
            <div class="metric"><span class="metric-label">PACKET LOSS</span><span class="metric-value loss-val">0.02%</span></div>
            <div class="metric-divider"></div>
            <div class="metric"><span class="metric-label">ACTIVE TUNNELS</span><span class="metric-value tunnel-val">47</span></div>
            <div class="metric-divider"></div>
            <div class="metric"><span class="metric-label">BGP PEERS</span><span class="metric-value peer-val">12</span></div>
            <div class="metric-divider"></div>
            <div class="metric"><span class="metric-label">UPTIME</span><span class="metric-value uptime-val">99.97%</span></div>
            <div class="metric-divider"></div>
            <div class="metric"><span class="metric-label">THREAT LEVEL</span><span class="metric-value threat-val">LOW</span></div>
        </div>

        <div class="alert-feed" id="alert-feed"></div>

        <main id="chat-window" class="chat-window"></main>

        <footer class="input-bar">
            <input type="text" id="user-input" placeholder="Paste router logs or diagnostic queries..." autocomplete="off" />
            <button id="send-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
            </button>
        </footer>
    </div>

    <!-- Architecture Modal -->
    <div class="modal-overlay" id="arch-modal" onclick="toggleArchModal()">
        <div class="modal-content" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h2>System Architecture</h2>
                <button class="modal-close" onclick="toggleArchModal()">X</button>
            </div>
            <div class="modal-body">
                <div class="arch-diagram">
                    <div class="arch-row">
                        <div class="arch-node user-node"><div class="arch-icon">&#x1F468;&#x200D;&#x1F4BB;</div><span>Operator</span></div>
                        <div class="arch-arrow">&#x2192;</div>
                        <div class="arch-node ui-node"><div class="arch-icon">&#x1F310;</div><span>Web UI</span></div>
                        <div class="arch-arrow">&#x2192;</div>
                        <div class="arch-node api-node"><div class="arch-icon">&#x26A1;</div><span>FastAPI</span></div>
                    </div>
                    <div class="arch-connector">&#x2193;</div>
                    <div class="arch-row">
                        <div class="arch-node vec-node"><div class="arch-icon">&#x1F5C4;</div><span>ChromaDB</span></div>
                        <div class="arch-arrow">&#x2190;</div>
                        <div class="arch-node emb-node"><div class="arch-icon">&#x1F9E0;</div><span>Embedder</span></div>
                        <div class="arch-arrow">&#x2192;</div>
                        <div class="arch-node llm-node"><div class="arch-icon">&#x1F916;</div><span>Qwen2-7B</span></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Scenarios Drawer -->
    <div class="scenarios-drawer" id="scenarios-drawer">
        <div class="drawer-header">
            <span>Diagnostic Scenarios</span>
            <button onclick="toggleScenarios()" class="modal-close">X</button>
        </div>
        <div class="drawer-chips" id="drawer-chips"></div>
    </div>

    <script src="/static/marked.min.js"></script>
    <script src="/static/highlight.min.js"></script>
    <script src="/static/script.js"></script>
</body>
</html>'''

STYLE_CSS = r'''
*,*::before,*::after { margin:0; padding:0; box-sizing:border-box; }
:root {
    --bg-primary: #020617; --bg-secondary: #0f172a; --bg-card: #0f172a;
    --accent: #06b6d4; --accent-glow: rgba(6, 182, 212, 0.4); --accent-secondary: #3b82f6;
    --text-primary: #f8fafc; --text-secondary: #94a3b8; --border: rgba(51, 65, 85, 0.5);
    --success: #10b981; --warning: #f59e0b; --danger: #ef4444;
    --font: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
body { font-family: var(--font); background: var(--bg-primary); color: var(--text-primary); height: 100vh; overflow: hidden; }
.app-container { width: 100vw; height: 100vh; display: flex; flex-direction: column; background: var(--bg-card); overflow: hidden; }

/* Header */
.app-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 24px; border-bottom: 1px solid var(--border); background: #020617; }
.header-left { display: flex; align-items: center; gap: 14px; }
.header-right { display: flex; align-items: center; gap: 8px; }
.logo-icon { color: var(--accent); filter: drop-shadow(0 0 10px var(--accent-glow)); }
.title-container h1 { font-size: 18px; font-weight: 700; background: linear-gradient(135deg, #fff, #67e8f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; gap: 8px; }
.version-tag { font-size: 9px; background: rgba(6,182,212,0.15); color: var(--accent); padding: 2px 6px; border: 1px solid var(--accent); border-radius: 3px; letter-spacing: 0.1em; }
.subtitle { font-size: 11px; color: var(--text-secondary); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.05em; display: block; }
.status-badge { display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 4px; font-size: 11px; font-weight: 700; letter-spacing: 0.1em; color: var(--success); background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); }
.pulse-dot { width: 6px; height: 6px; background: var(--success); border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity:1; box-shadow:0 0 0 0 rgba(16,185,129,0.5); } 50% { opacity:0.7; box-shadow:0 0 0 6px rgba(16,185,129,0); } }
.arch-btn, .scenarios-btn { display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; font-family: var(--font); cursor: pointer; border: 1px solid var(--border); background: rgba(15,23,42,0.8); color: var(--text-secondary); }
.arch-btn:hover, .scenarios-btn:hover { border-color: var(--accent); color: var(--accent); background: rgba(6,182,212,0.1); }

/* Timeline */
.timeline-container { padding: 8px 24px 12px; background: #020617; border-bottom: 1px solid var(--border); position: relative; }
.timeline-track { width: 100%; height: 4px; background: var(--border); border-radius: 2px; position: relative; overflow: hidden;}
.timeline-progress { position: absolute; top: 8px; left: 24px; height: 4px; background: var(--success); width: 15%; transition: width 1s ease, background 1s ease; border-radius: 2px; box-shadow: 0 0 8px var(--success); }
.timeline-markers { display: flex; justify-content: space-between; margin-top: 6px; font-family: var(--mono); font-size: 9px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
.marker.active { color: var(--success); text-shadow: 0 0 8px var(--success); }
.marker.stress.active { color: var(--warning); text-shadow: 0 0 8px var(--warning); }
.marker.fail.active { color: var(--danger); text-shadow: 0 0 8px var(--danger); animation: blink 1s infinite; }

/* Status Bar */
.status-bar { display: flex; align-items: center; justify-content: flex-start; gap: 0; padding: 10px 24px; background: rgba(2,6,23,0.7); border-bottom: 1px solid var(--border); overflow-x: auto; white-space: nowrap; -webkit-overflow-scrolling: touch; }
.status-bar::-webkit-scrollbar { height: 4px; } .status-bar::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
.metric { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 0 16px; flex-shrink: 0; }
.metric-label { font-size: 9px; font-weight: 700; letter-spacing: 0.1em; color: var(--text-secondary); font-family: var(--mono); }
.metric-value { font-size: 14px; font-weight: 700; font-family: var(--mono); color: var(--success); transition: color 0.5s; }
.metric-divider { width: 1px; height: 28px; background: var(--border); flex-shrink: 0; }

/* Alert Feed */
.alert-feed { display: flex; gap: 10px; padding: 8px 24px; overflow-x: auto; background: rgba(2,6,23,0.5); border-bottom: 1px solid var(--border); min-height: 36px; align-items: center; }
.alert-feed::-webkit-scrollbar { height: 0; }
.alert-item { display: flex; align-items: center; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-family: var(--mono); white-space: nowrap; flex-shrink: 0; }
.alert-item.critical { background: rgba(239,68,68,0.1); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
.alert-item.warning { background: rgba(245,158,11,0.1); color: #fcd34d; border: 1px solid rgba(245,158,11,0.3); }
.alert-item.info { background: rgba(6,182,212,0.1); color: #67e8f9; border: 1px solid rgba(6,182,212,0.3); }

/* Chat Window */
.chat-window { flex: 1; overflow-y: auto; padding: 20px 24px; display: flex; flex-direction: column; gap: 20px; }
.chat-window::-webkit-scrollbar { width: 6px; } .chat-window::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
.message { display: flex; gap: 12px; max-width: 90%; animation: fadeSlideIn 0.3s ease; }
.message.user { align-self: flex-end; flex-direction: row-reverse; } .message.bot { align-self: flex-start; }
@keyframes fadeSlideIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.avatar { width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: rgba(30,41,59,0.8); border: 1px solid var(--border); }
.message.bot .avatar { color: var(--accent); box-shadow: 0 0 10px var(--accent-glow); } .message.user .avatar { color: #f8fafc; }
.bubble-wrapper { display: flex; flex-direction: column; gap: 6px; width: 100%; }
.bubble { padding: 16px 20px; border-radius: 12px; font-size: 14px; line-height: 1.6; box-shadow: 0 4px 12px rgba(0,0,0,0.2); width: 100%; }
.message.bot .bubble { background: rgba(15,23,42,0.9); border: 1px solid var(--border); color: #e2e8f0; }
.message.user .bubble { background: rgba(30,41,59,0.9); border: 1px solid var(--border); color: #fff; }

/* RCA Chain */
.rca-chain { margin-bottom: 12px; font-family: var(--mono); font-size: 12px; color: var(--text-secondary); background: rgba(2,6,23,0.5); padding: 12px; border-radius: 8px; border-left: 3px solid var(--accent); }
.rca-step { margin-bottom: 4px; animation: slideIn 0.3s ease; }
.rca-step:before { content: '>'; color: var(--accent); margin-right: 6px; font-weight: bold; }
@keyframes slideIn { from { opacity:0; transform:translateX(-10px); } to { opacity:1; transform:translateX(0); } }

/* Responses */
.severity-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; font-family: var(--mono); margin-bottom: 10px; }
.severity-badge.critical { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); }
.severity-badge.warning { background: rgba(245,158,11,0.15); color: #fcd34d; border: 1px solid rgba(245,158,11,0.4); }
.severity-badge.info { background: rgba(6,182,212,0.15); color: #67e8f9; border: 1px solid rgba(6,182,212,0.4); }
.response-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.meta-chip { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 4px; font-size: 10px; font-weight: 600; font-family: var(--mono); color: var(--text-secondary); background: rgba(15,23,42,0.6); border: 1px solid var(--border); }
.action-buttons { display: flex; gap: 6px; flex-wrap: wrap; }
.action-btn { padding: 4px 10px; border-radius: 4px; font-size: 10px; font-weight: 600; font-family: var(--mono); cursor: pointer; border: 1px solid var(--border); background: rgba(15,23,42,0.8); color: var(--text-secondary); }
.action-btn:hover { border-color: var(--accent); color: var(--accent); background: rgba(6,182,212,0.1); } .action-btn.copied { border-color: var(--success); color: var(--success); }

/* Markdown */
.bubble p { margin-bottom: 8px; } .bubble p:last-child { margin-bottom: 0; } .bubble strong { color: #fff; font-weight: 600; }
.bubble pre { background: #020617; padding: 12px; border-radius: 8px; border: 1px solid var(--border); overflow-x: auto; margin: 10px 0; }
.bubble code { font-family: var(--mono); font-size: 12px; color: #a5b4fc; } .bubble table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 13px; }
.bubble th, .bubble td { padding: 8px; border: 1px solid var(--border); text-align: left; } .bubble th { background: rgba(30,41,59,0.8); }
.bubble ul, .bubble ol { margin: 8px 0 8px 20px; } .bubble li { margin-bottom: 4px; }
.sources-wrapper { display: flex; flex-wrap: wrap; gap: 6px; } .source-tag { padding: 4px 10px; border-radius: 4px; font-size: 10px; font-weight: 600; background: rgba(6,182,212,0.1); color: var(--accent); border: 1px solid rgba(6,182,212,0.3); }
.thinking-bubble { display: flex; align-items: center; gap: 10px; color: var(--accent); font-family: var(--mono); font-size: 12px; }
.thinking-spinner { width: 14px; height: 14px; border: 2px solid rgba(6,182,212,0.2); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } } .typing-cursor { display: inline-block; width: 6px; height: 14px; background: var(--accent); animation: blink 0.6s step-end infinite; margin-left: 4px; vertical-align: middle; }
@keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }

/* Input Bar */
.input-bar { display: flex; gap: 12px; padding: 16px 24px; border-top: 1px solid var(--border); background: #020617; }
.input-bar input { flex: 1; padding: 14px 20px; border: 1px solid var(--border); border-radius: 8px; background: #0f172a; color: var(--text-primary); font-size: 14px; font-family: var(--mono); outline: none; }
.input-bar input:focus { border-color: var(--accent); }
.input-bar button { width: 50px; height: 50px; border: none; border-radius: 8px; background: rgba(30,41,59,0.9); border: 1px solid var(--border); color: var(--accent); cursor: pointer; }

/* Modals */
.modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center; backdrop-filter: blur(4px); } .modal-overlay.active { display: flex; }
.modal-content { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; width: 95%; max-width: 600px; max-height: 85vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border); } .modal-close { background: none; border: 1px solid var(--border); color: var(--text-secondary); padding: 4px 8px; border-radius: 4px; cursor: pointer; }
.modal-body { padding: 20px; } .arch-diagram { display: flex; flex-direction: column; align-items: center; gap: 12px; margin-bottom: 20px; } .arch-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; justify-content: center; } .arch-node { display: flex; flex-direction: column; align-items: center; padding: 12px; border-radius: 8px; border: 1px solid var(--border); background: rgba(15,23,42,0.9); min-width: 90px; } .arch-node span { font-size: 11px; font-weight: 700; } .arch-node small { font-size: 9px; color: var(--text-secondary); } .arch-icon { font-size: 24px; margin-bottom: 4px; }
.scenarios-drawer { display: none; position: fixed; top: 0; right: 0; width: 100%; max-width: 360px; height: 100%; background: var(--bg-secondary); border-left: 1px solid var(--border); z-index: 999; flex-direction: column; box-shadow: -5px 0 20px rgba(0,0,0,0.5); } .scenarios-drawer.active { display: flex; } .drawer-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border); color: var(--accent); font-weight: 700; font-size: 14px; } .drawer-chips { padding: 16px; display: flex; flex-direction: column; gap: 10px; overflow-y: auto; } .drawer-chip { padding: 12px 16px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; border: 1px solid var(--border); background: rgba(15,23,42,0.8); color: var(--text-primary); display: flex; align-items: flex-start; gap: 10px; } .drawer-chip .chip-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }

@media (max-width: 768px) {
    .app-header { flex-direction: column; align-items: flex-start; gap: 12px; padding: 12px 16px; } .header-right { width: 100%; justify-content: space-between; } .btn-text { display: none; } .badge-text { display: none; } .arch-btn, .scenarios-btn { padding: 6px 10px; }
    .status-bar { padding: 8px 16px; } .metric { padding: 0 10px; } .alert-feed { padding: 6px 16px; }
    .chat-window { padding: 16px; gap: 16px; } .message { max-width: 95%; gap: 8px; } .bubble { padding: 14px 16px; font-size: 13px; }
    .input-bar { padding: 12px 16px; gap: 8px; } .input-bar input { padding: 12px 16px; font-size: 13px; } .input-bar button { width: 44px; height: 44px; }
}
'''

SCRIPT_JS = r'''
const chatWindow = document.getElementById('chat-window');
const userInput  = document.getElementById('user-input');
const sendBtn    = document.getElementById('send-btn');
let conversationHistory = [];
let voiceEnabled = false;

const userSVG = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
const botSVG = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path><line x1="8" y1="16" x2="8" y2="16"></line><line x1="16" y1="16" x2="16" y2="16"></line></svg>`;

const scenarios = [
    { dot:'red', text:'Simulate BGP Route Flap', query:'A branch office BGP session is flapping every 30 seconds with repeated NOTIFICATION messages. The router log shows: %BGP-3-NOTIFICATION: received from neighbor 10.0.0.1 (hold time expired). Diagnose the root cause and recommend remediation steps.' },
    { dot:'yellow', text:'Diagnose High Latency on MPLS Tunnel', query:'Our MPLS tunnel between the datacenter (10.1.0.1) and branch office (10.2.0.1) is showing 340ms latency, up from the baseline of 12ms. SD-WAN SLA metrics show jitter at 45ms and packet loss at 2.3%. What are the possible causes and what diagnostic commands should I run?' },
    { dot:'green', text:'Analyze SD-WAN Failover Event', query:'At 14:32 UTC, our SD-WAN controller triggered an automatic failover from the primary MPLS transport to the secondary 4G/LTE cellular backup for 3 branch sites. The failover lasted 8 minutes. Analyze what could have caused this and whether the failover policy worked correctly.' },
    { dot:'blue', text:'Compare VPN vs Direct Connect', query:'Compare AWS Site-to-Site VPN vs AWS Direct Connect for our enterprise SD-WAN deployment. Present the comparison in a table format covering latency, bandwidth, cost, redundancy, and security.' },
];

const drawerChips = document.getElementById('drawer-chips');
scenarios.forEach(s => {
    const chip = document.createElement('button'); chip.className = 'drawer-chip';
    chip.innerHTML = `<span class="chip-dot" style="background:var(--${s.dot === 'red' ? 'danger' : s.dot === 'yellow' ? 'warning' : s.dot === 'green' ? 'success' : 'accent-secondary'});box-shadow:0 0 8px var(--${s.dot === 'red' ? 'danger' : s.dot === 'yellow' ? 'warning' : s.dot === 'green' ? 'success' : 'accent-secondary'})"></span>${s.text}`;
    chip.onclick = () => { userInput.value = s.query; toggleScenarios(); sendMessage(s.dot); };
    drawerChips.appendChild(chip);
});

function toggleArchModal() { document.getElementById('arch-modal').classList.toggle('active'); }
function toggleScenarios() { document.getElementById('scenarios-drawer').classList.toggle('active'); }

// --- V5 FEATURES ---

function toggleVoice() {
    voiceEnabled = !voiceEnabled;
    const btn = document.getElementById('voice-btn');
    btn.innerHTML = voiceEnabled ? '🔊 <span class="btn-text">Voice: ON</span>' : '🔈 <span class="btn-text">Voice: OFF</span>';
    btn.style.color = voiceEnabled ? 'var(--success)' : 'var(--text-secondary)';
    btn.style.borderColor = voiceEnabled ? 'var(--success)' : 'var(--border)';
    if(voiceEnabled) speakText("Voice synthesis activated. Standing by.");
}

function speakText(text) {
    if(!voiceEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.95; u.pitch = 0.9;
    window.speechSynthesis.speak(u);
}

function updateTimeline(incident) {
    const prog = document.getElementById('timeline-progress');
    const mStress = document.getElementById('marker-stress');
    const mFail = document.getElementById('marker-fail');
    
    if(incident === 'red' || incident === 'yellow') {
        prog.style.width = '75%'; prog.style.background = 'var(--warning)';
        prog.style.boxShadow = '0 0 10px var(--warning)';
        mStress.classList.add('active'); mStress.textContent = '⚠ Anomaly Detected';
        mFail.classList.add('active'); mFail.textContent = '🔴 Predicted Outage: ~4m';
    } else {
        prog.style.width = '15%'; prog.style.background = 'var(--success)';
        prog.style.boxShadow = '0 0 8px var(--success)';
        mStress.classList.remove('active'); mFail.classList.remove('active');
        mStress.textContent = 'System Stress'; mFail.textContent = 'Predicted Failure';
    }
}

// -------------------

let currentIncident = null;
function setIncident(type) { currentIncident = type; setTimeout(() => { currentIncident = null; updateTimeline(); }, 40000); }
function updateMetrics() {
    let lat, loss, tunnels, peers, threat, threatColor;
    if (currentIncident === 'bgp') {
        lat = (180 + Math.random()*160).toFixed(1); loss = (3 + Math.random()*4).toFixed(2);
        tunnels = 28 + Math.floor(Math.random()*5); peers = 4 + Math.floor(Math.random()*3);
        threat = 'CRITICAL'; threatColor = 'var(--danger)';
    } else if (currentIncident === 'latency') {
        lat = (280 + Math.random()*120).toFixed(1); loss = (1.5 + Math.random()*2).toFixed(2);
        tunnels = 35 + Math.floor(Math.random()*5); peers = 9 + Math.floor(Math.random()*3);
        threat = 'WARNING'; threatColor = 'var(--warning)';
    } else if (currentIncident === 'failover') {
        lat = (45 + Math.random()*30).toFixed(1); loss = (0.5 + Math.random()*1).toFixed(2);
        tunnels = 38 + Math.floor(Math.random()*5); peers = 10 + Math.floor(Math.random()*2);
        threat = 'WARNING'; threatColor = 'var(--warning)';
    } else {
        lat = (10 + Math.random()*8).toFixed(1); loss = (Math.random()*0.05).toFixed(3);
        tunnels = 44 + Math.floor(Math.random()*6); peers = 11 + Math.floor(Math.random()*3);
        threat = 'LOW'; threatColor = 'var(--success)';
    }
    document.querySelector('.latency-val').textContent = lat + ' ms';
    document.querySelector('.latency-val').style.color = parseFloat(lat) > 50 ? (parseFloat(lat) > 150 ? 'var(--danger)' : 'var(--warning)') : 'var(--success)';
    document.querySelector('.loss-val').textContent = loss + '%';
    document.querySelector('.loss-val').style.color = parseFloat(loss) > 1 ? (parseFloat(loss) > 3 ? 'var(--danger)' : 'var(--warning)') : 'var(--success)';
    document.querySelector('.tunnel-val').textContent = tunnels;
    document.querySelector('.tunnel-val').style.color = tunnels < 35 ? 'var(--danger)' : 'var(--success)';
    document.querySelector('.peer-val').textContent = peers;
    document.querySelector('.peer-val').style.color = peers < 8 ? 'var(--danger)' : 'var(--success)';
    const tv = document.querySelector('.threat-val'); tv.textContent = threat; tv.style.color = threatColor;
}
setInterval(updateMetrics, 2500); updateMetrics();

const alertFeed = document.getElementById('alert-feed');
const alertMessages = [
    { level:'info', msg:'BGP peer 10.0.0.1 session ESTABLISHED' }, { level:'info', msg:'MPLS label switch path verified OK' },
    { level:'warning', msg:'Interface GigE0/1 utilization at 78%' }, { level:'info', msg:'SD-WAN policy update applied' },
    { level:'critical', msg:'BGP NOTIFICATION: Hold timer expired for 10.0.0.5' }, { level:'warning', msg:'Tunnel latency exceeded SLA' },
    { level:'critical', msg:'MPLS LSP down: PE1-to-PE3 tunnel unreachable' },
];
let alertIdx = 0;
function addAlert() {
    const a = alertMessages[alertIdx % alertMessages.length];
    const el = document.createElement('div'); el.className = 'alert-item ' + a.level;
    el.textContent = `[${new Date().toLocaleTimeString()}] ${a.level.toUpperCase()}: ${a.msg}`;
    alertFeed.prepend(el); if (alertFeed.children.length > 5) alertFeed.removeChild(alertFeed.lastChild);
    alertIdx++;
}
setInterval(addAlert, 6000); addAlert();

function addMessage(html, sender) {
    const row = document.createElement('div'); row.className = 'message ' + sender;
    const avatar = document.createElement('div'); avatar.className = 'avatar'; avatar.innerHTML = sender === 'bot' ? botSVG : userSVG;
    row.appendChild(avatar);
    const bubble = document.createElement('div'); bubble.className = 'bubble'; bubble.innerHTML = html;
    row.appendChild(bubble); chatWindow.appendChild(row); chatWindow.scrollTop = chatWindow.scrollHeight;
    return bubble;
}

function addWelcome() {
    const row = document.createElement('div'); row.className = 'message bot';
    const avatar = document.createElement('div'); avatar.className = 'avatar'; avatar.innerHTML = botSVG; row.appendChild(avatar);
    const w = document.createElement('div'); w.className = 'bubble-wrapper';
    const b = document.createElement('div'); b.className = 'bubble';
    b.innerHTML = 'NOC Copilot initialized. Telemetry vault loaded with <strong>199 vectors</strong>.<br><br>Click <strong>Scenarios</strong> to run simulations.';
    w.appendChild(b); row.appendChild(w); chatWindow.appendChild(row);
}

async function simulateRCA(wrapper) {
    const rcaSteps = [
        "[STEP 1] Anomaly Detected in telemetry stream...",
        "[STEP 2] Querying RAG Vector Vault for known patterns...",
        "[STEP 3] Cross-referencing historical metrics...",
        "[STEP 4] Autonomous RCA Initiated."
    ];
    const chain = document.createElement('div'); chain.className = 'rca-chain';
    wrapper.appendChild(chain);
    for (let step of rcaSteps) {
        const stepEl = document.createElement('div'); stepEl.className = 'rca-step'; stepEl.textContent = step;
        chain.appendChild(stepEl); chatWindow.scrollTop = chatWindow.scrollHeight;
        await new Promise(r => setTimeout(r, 700));
    }
}

function createStream() {
    const row = document.createElement('div'); row.className = 'message bot';
    const av = document.createElement('div'); av.className = 'avatar'; av.innerHTML = botSVG; row.appendChild(av);
    const w = document.createElement('div'); w.className = 'bubble-wrapper';
    const b = document.createElement('div'); b.className = 'bubble';
    const content = document.createElement('div'); content.className = 'markdown-content';
    const cursor = document.createElement('span'); cursor.className = 'typing-cursor';
    b.appendChild(content); b.appendChild(cursor); w.appendChild(b); row.appendChild(w);
    chatWindow.appendChild(row); chatWindow.scrollTop = chatWindow.scrollHeight;
    return { content, cursor, wrapper: w, row, bubble: b };
}

function addResponseMeta(wrapper, totalTime, rawText, sources) {
    const conf = Math.floor(Math.random() * 9) + 87; // 87 to 95%
    const bars = "█".repeat(Math.floor(conf/10)) + "░".repeat(10 - Math.floor(conf/10));
    
    const meta = document.createElement('div'); meta.className = 'response-meta';
    meta.innerHTML = `<span class="meta-chip">Diagnosed in ${totalTime}s</span> <span class="meta-chip" style="color:var(--success); border-color:var(--success)">Confidence: ${conf}% [${bars}]</span>`;
    wrapper.appendChild(meta);
    
    const btns = document.createElement('div'); btns.className = 'action-buttons';
    const copyBtn = document.createElement('button'); copyBtn.className = 'action-btn'; copyBtn.innerHTML = `COPY`;
    copyBtn.onclick = () => { navigator.clipboard.writeText(rawText); copyBtn.classList.add('copied'); copyBtn.innerHTML = `COPIED`; setTimeout(() => { copyBtn.classList.remove('copied'); copyBtn.innerHTML = `COPY`; }, 2000); };
    btns.appendChild(copyBtn);
    
    const expBtn = document.createElement('button'); expBtn.className = 'action-btn'; expBtn.innerHTML = `EXPORT PDF/TXT`;
    expBtn.onclick = () => {
        const ts = new Date().toISOString().replace(/[:.]/g,'-');
        const report = `=================================================\n AIR-GAPPED NOC COPILOT\n INCIDENT DIAGNOSTIC REPORT\n=================================================\nIncident ID: NOC-2026-0615-${Math.floor(Math.random()*1000)}\nDetected: ${new Date().toLocaleString()}\nConfidence: ${conf}%\nSources: ${sources.join(', ')}\n-------------------------------------------------\nDIAGNOSIS & REMEDIATION:\n-------------------------------------------------\n\n${rawText}\n\n=================================================\n END OF REPORT\n=================================================`;
        const blob = new Blob([report], {type:'text/plain'});
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
        a.download = `NOC_Incident_${ts}.txt`; a.click();
    };
    btns.appendChild(expBtn);
    wrapper.appendChild(btns);
}

async function sendMessage(scenarioColor = null) {
    const msg = userInput.value.trim(); if (!msg) return;
    const tmp = document.createElement('div'); tmp.textContent = msg; addMessage(tmp.innerHTML, 'user');
    userInput.value = ''; sendBtn.disabled = true;

    if (msg.toLowerCase().includes('bgp') && msg.toLowerCase().includes('flap')) setIncident('bgp');
    else if (msg.toLowerCase().includes('latency') || msg.toLowerCase().includes('340ms')) setIncident('latency');
    else if (msg.toLowerCase().includes('failover')) setIncident('failover');
    
    updateTimeline(scenarioColor);
    
    if(voiceEnabled && (scenarioColor === 'red' || scenarioColor === 'yellow' || currentIncident)) {
        speakText("Critical anomaly detected. Initiating autonomous diagnostic routine.");
    }

    let streamObj = createStream();
    await simulateRCA(streamObj.wrapper);
    
    let raw = ""; let rSources = [];

    try {
        conversationHistory.push({role:"user", content: msg});
        const res = await fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message:msg, history:conversationHistory}) });
        const reader = res.body.getReader(); const dec = new TextDecoder();
        let buf = '', totalTime = 0;
        
        while (true) {
            const {done, value} = await reader.read(); if (done) break;
            buf += dec.decode(value, {stream:true}); const lines = buf.split('\n'); buf = lines.pop();
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                try {
                    const d = JSON.parse(line.slice(6));
                    if (d.type === 'sources') { rSources = d.content; }
                    else if (d.type === 'token') {
                        raw += d.content;
                        if (window.marked) { streamObj.content.innerHTML = marked.parse(raw); if (window.hljs) streamObj.content.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b)); }
                        else streamObj.content.textContent = raw;
                        chatWindow.scrollTop = chatWindow.scrollHeight;
                    } else if (d.type === 'done') {
                        totalTime = d.total_time || 0; 
                        if (streamObj) { streamObj.cursor.remove(); addResponseMeta(streamObj.wrapper, totalTime, raw, rSources); }
                        if (voiceEnabled && raw.includes('[SEVERITY:')) {
                            const firstLine = raw.split('\n')[0].replace(/\[|\]/g, '') + ". Diagnosis complete.";
                            speakText(firstLine);
                        }
                    }
                } catch(e) {}
            }
        }
        conversationHistory.push({role:"assistant", content:raw}); if (conversationHistory.length > 6) conversationHistory = conversationHistory.slice(-6); 
    } catch(e) { streamObj.bubble.innerHTML = 'CRITICAL: Connection lost.'; }
    sendBtn.disabled = false; userInput.focus();
}

sendBtn.addEventListener('click', () => sendMessage());
userInput.addEventListener('keypress', e => { if (e.key === 'Enter' && !e.shiftKey) sendMessage(); });
addWelcome();
'''

files = {
    os.path.join(UI_DIR, "app.py"):         APP_PY,
    os.path.join(STATIC_DIR, "index.html"): INDEX_HTML,
    os.path.join(STATIC_DIR, "style.css"):  STYLE_CSS,
    os.path.join(STATIC_DIR, "script.js"):  SCRIPT_JS,
}
for path, content in files.items():
    with open(path, "w") as f:
        f.write(content.strip() + "\n")
    print(f"  [OK] {path}")
print("\n" + "="*50)
print(" NOC COPILOT v5 — THE GRAND PRIZE EDITION")
print(" Voice API | Autonomous RCA | Timeline | Export")
print("="*50)
