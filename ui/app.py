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
