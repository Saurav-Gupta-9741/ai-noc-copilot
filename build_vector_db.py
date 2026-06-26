import os
import chromadb

BASE = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE, "chroma_db")
os.makedirs(DB_DIR, exist_ok=True)

print("==================================================")
print("🗄️ INITIATING AIR-GAPPED VECTOR DATABASE 🗄️")
print("==================================================")

# Initialize ChromaDB client
client = chromadb.PersistentClient(path=DB_DIR)

# Create collection
collection_name = "secure_docs"
try:
    client.delete_collection(collection_name)
except:
    pass
collection = client.create_collection(collection_name)

# Hardcoded runbook text for the demonstration
runbook_data = [
    {
        "id": "doc_1",
        "text": """[ISRO_NOC_Runbook_v4.pdf - Page 112]
Symptom: Sudden spike in interface latency combined with consecutive dropped keepalive packets on Tunnel-0.
Diagnosis: This indicates a Route Flap Damping event on the primary Ground Station uplink.
Mitigation Strategy:
1. DO NOT restart the BGP process (this will cause a cascading failure across the MPLS underlay).
2. Soft-clear the BGP peering session locally.
3. Reroute traffic temporarily to Satellite-Link-2 via static metric adjustment.
Remediation Script:
configure terminal
router bgp 65001
neighbor 10.45.0.2 soft-reconfiguration inbound
clear ip bgp 10.45.0.2 soft
exit""",
        "source": "ISRO_NOC_Runbook_v4.pdf (Page 112)"
    },
    {
        "id": "doc_2",
        "text": """[Cisco_BGP_Troubleshooting.pdf - Page 45]
Symptom: High jitter on IPSec tunnels with BGP over SD-WAN.
Diagnosis: Typically caused by MTU mismatch or fragmentation.
Mitigation: Verify MTU settings and adjust TCP MSS to 1360.
Remediation Script:
interface Tunnel0
 ip tcp adjust-mss 1360
 end""",
        "source": "Cisco_BGP_Troubleshooting.pdf (Page 45)"
    }
]

# We don't embed manually here. ChromaDB uses its default embedding function or we can use the local SentenceTransformer
# BUT since this script runs *before* we run the app, we can just let ChromaDB use its default embedder (which downloads a small all-MiniLM-L6-v2 model).
# To keep it completely air-gapped matching the main app, we will use the local downloaded model.

print("Loading local Embedder (sentence-transformers/all-MiniLM-L6-v2)...")
from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer(os.path.join(BASE, "models", "embeddings"))

print("Embedding and inserting enterprise runbooks into ChromaDB...")
texts = [d["text"] for d in runbook_data]
metadatas = [{"source": d["source"]} for d in runbook_data]
ids = [d["id"] for d in runbook_data]

embeddings = embedder.encode(texts).tolist()

collection.add(
    embeddings=embeddings,
    documents=texts,
    metadatas=metadatas,
    ids=ids
)

print(f"✅ Vault secured. {collection.count()} vectors locked in offline database.")
print(f"Directory: {DB_DIR}")
