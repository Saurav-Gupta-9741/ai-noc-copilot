import os
from huggingface_hub import snapshot_download

BASE = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

LLM_DIR = os.path.join(MODELS_DIR, "qwen2")
EMBED_DIR = os.path.join(MODELS_DIR, "embeddings")

print("==================================================")
print("📥 INITIATING AIR-GAPPED MODEL DOWNLOADS 📥")
print("==================================================")

print("\n1. Downloading SentenceTransformer (Embeddings)...")
snapshot_download(
    repo_id="sentence-transformers/all-MiniLM-L6-v2",
    local_dir=EMBED_DIR,
    ignore_patterns=["*.msgpack", "*.h5", "*.ot"]
)
print("✅ Embedder Downloaded.")

print("\n2. Downloading LLM (Qwen2-7B-Instruct)...")
print("WARNING: This is ~15GB. It will take some time depending on your internet speed.")
snapshot_download(
    repo_id="Qwen/Qwen2-7B-Instruct",
    local_dir=LLM_DIR,
    ignore_patterns=["*.msgpack", "*.h5", "*.ot"]
)
print("✅ LLM Downloaded.")

print("\n🎉 All models have been securely downloaded to your local drive!")
print(f"Directory: {MODELS_DIR}")
