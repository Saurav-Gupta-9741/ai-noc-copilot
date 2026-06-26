import sys, os, json, time, asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()
UI_DIR = Path(__file__).parent / "ui"
STATIC_DIR = UI_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    user_msg = data.get("message", "")
    
    start_time = time.time()
    await asyncio.sleep(1.5) # Simulate RAG retrieval delay
    
    sources = ["ISRO_NOC_Runbook_v4.pdf (Page 112)", "Cisco_BGP_Troubleshooting.pdf (Page 45)"]
    elapsed = 1.5

    async def sse():
        yield f"data: {json.dumps({'type':'sources','content': sources})}\n\n"
        yield f"data: {json.dumps({'type':'meta','retrieval_time': elapsed})}\n\n"
        
        # Highly realistic, deterministic mock response based on the user's input
        if "latency" in user_msg.lower() or "alert" in user_msg.lower() or "scenario" in user_msg.lower():
            fake_response = """[SEVERITY: CRITICAL]

**Autonomous Root Cause Analysis (RCA):**
The sudden spike in interface latency combined with consecutive dropped keepalive packets indicates a **Route Flap Damping** event on the primary Ground Station uplink (Interface `Tunnel-0`).

**Automated Mitigation Strategy:**
1. DO NOT restart the BGP process (this will cause a cascading failure across the MPLS underlay).
2. Soft-clear the BGP peering session locally.
3. Reroute traffic temporarily to Satellite-Link-2 via static metric adjustment.

**Generated Remediation Script:**
```bash
configure terminal
router bgp 65001
neighbor 10.45.0.2 soft-reconfiguration inbound
clear ip bgp 10.45.0.2 soft
exit
```
*Awaiting Operator Approval to execute commands on edge router...*"""
        else:
             fake_response = f"""[SEVERITY: INFO]

**Diagnostic Report:**
I have cross-referenced your query regarding "{user_msg}" against the local, air-gapped runbooks. The system telemetry currently indicates normal operations. 

If you are experiencing anomalies, please trigger a scenario simulation or paste the raw Syslog output here for autonomous analysis."""

        # Stream tokens realistically
        import re
        tokens = re.split(r'(\s+)', fake_response)
        for tok in tokens:
            if tok:
                yield f"data: {json.dumps({'type':'token','content': tok})}\n\n"
                await asyncio.sleep(0.03) # Realistic typing speed
            
        total = round(time.time() - start_time, 1)
        yield f"data: {json.dumps({'type':'done','total_time': total})}\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")

if __name__ == "__main__":
    print("======================================================")
    print(">>> AI NOC COPILOT - VIDEO RECORDING MODE <<<")
    print("Backend LLM replaced with rapid mock streaming.")
    print("Ready to record! Open http://localhost:8529")
    print("======================================================")
    uvicorn.run(app, host="0.0.0.0", port=8529)
