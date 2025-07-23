#!/usr/bin/env python3

# ─────────────────────────────────────────────────────────────
# © 2025 StatikFintechLLC
# Contact: ascend.gremlin@gmail.com
# ─────────────────────────────────────────────────────────────

# Gremlin Trader Memory Embedder & Vector Store Core

from backend.globals import CFG, logger, resolve_path, DATA_DIR, MEM

try:
    from backend.globals import MEM, CFG
    dashboard_selected_backend = CFG.get('memory', {}).get('dashboard_selected_backend', 'faiss')
except Exception as e:
    logger.error(f"[EMBEDDER] MEM/CFG import or type-check failed: {e}")
    MEM = {}
    dashboard_selected_backend = 'faiss'

try:
    from nlp_engine.transformer_core import encode
except Exception:
    # fallback to a dummy encoder
    def encode(text):
        _ = text  # Access the parameter to avoid unused variable warning
        return np.zeros(MEM.get("embedding", {}).get("dimension", 384), dtype="float32")

# --- Configuration & Paths ---
storage_conf = MEM.get("storage", {})
if not isinstance(storage_conf, dict):
    logger.error("[EMBEDDER] storage config malformed; resetting to empty dict")
    storage_conf = {}

BASE_VECTOR_PATH = storage_conf.get("vector_store_path", "./Gremlin-Trade-Memory/vector_store")
CHROMA_DIR       = os.path.join(BASE_VECTOR_PATH, "chroma")

# Use dashboard-selected backend for toggling
USE_CHROMA  = dashboard_selected_backend == "chromadb"

# --- Ensure directories exist (and log failures) ---
for path in (FAISS_DIR, CHROMA_DIR, LOCAL_INDEX_PATH):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        logger.error(f"[EMBEDDER] Failed to create directory {path}: {e}")

# --- Chroma Client Setup ---
if chromadb:
    try:
        chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        collection = chroma_client.get_or_create_collection(name="gremlin_memory")
    except Exception as e:
        logger.error(f"[EMBEDDER] Failed to initialize Chroma client: {e}")
        collection = None
else:
    collection = None

def add_to_chroma(text, emb_id, vector, meta):
    if not collection:
        logger.warning(f"[CHROMA] Skipping add; collection not available")
        return
    try:
        collection.add(
            documents=[text],
            embeddings=[vector.tolist() if hasattr(vector, "tolist") else list(vector)],
            metadatas=[meta],
            ids=[emb_id]
        )
        logger.info(f"[CHROMA] Added {emb_id}")
    except Exception as e:
        logger.error(f"[CHROMA] Add failed for {emb_id}: {e}")


def get_backend_status():
    """Get status of both FAISS and Chroma backends."""
    status = {
        "chromadb_available": chromadb is not None and collection is not None,
        "chroma_collection_count": 0
    }

    
    # Get Chroma count
    if status["chromadb_available"]:
        try:
            status["chroma_collection_count"] = collection.count()  # type: ignore
        except Exception as e:
            logger.warning(f"[EMBEDDER] Failed to get Chroma count: {e}")
    
    return status

    # Use current backend selection (dynamically determined)
    current_backend = get_current_backend()
    current_backend == "chromadb" and collection is not None:
      add_to_chroma(text, emb_id, vector, meta)
        
    memory_vectors[emb_id] = embedding
    try:
        _write_to_disk(embedding)
        logger.info(f"[EMBEDDER] Stored embedding: {emb_id} using {current_backend}")
    except Exception as e:
        logger.error(f"[EMBEDDER] Disk write failed for {emb_id}: {e}")
    return embedding

def archive_plan(vector_path="backend/Gremlin-Trade-Core/Gremlin-Trader-Strategies/Past-Strategies.jsonl"):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    archive = os.path.join("GremlinGPT", "docs", f"planlog_{stamp}.jsonl")
    try:
        shutil.copyfile(vector_path, archive)
        logger.info(f"[EMBEDDER] Plan archived: {archive}")
        return archive
    except Exception as e:
        logger.error(f"[EMBEDDER] Archive failed: {e}")
        return None

def auto_commit(file_path):
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"[EMBEDDER] auto_commit: invalid path {file_path}")
        return
    try:
        os.system(f"git add {file_path}")
        os.system(f'git commit -m "[autocommit] Updated: {file_path}"')
        logger.info(f"[EMBEDDER] auto_commit succeeded for {file_path}")
    except Exception as e:
        logger.error(f"[EMBEDDER] Git commit failed: {e}")

def get_all_embeddings(limit=50):
    if not memory_vectors:
        _load_from_disk()
    return list(memory_vectors.values())[:limit]

def get_embedding_by_id(emb_id):
    if emb_id not in memory_vectors:
        _load_from_disk()
    return memory_vectors.get(emb_id)

def _write_to_disk(embedding):
    try:
        path = os.path.join(LOCAL_INDEX_PATH, f"{embedding['id']}.json")
        with open(path, "w") as f:
            json.dump(embedding, f, indent=2)
    except Exception as e:
        logger.error(f"[EMBEDDER] Failed to write {embedding['id']} to disk: {e}")

def _load_from_disk():
    if not os.path.isdir(LOCAL_INDEX_PATH):
        logger.warning(f"[EMBEDDER] Local index missing: {LOCAL_INDEX_PATH}")
        return
    for fname in os.listdir(LOCAL_INDEX_PATH):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(LOCAL_INDEX_PATH, fname)
        try:
            with open(fpath, "r") as f:
                emb = json.load(f)
            memory_vectors[emb["id"]] = emb
        except Exception as e:
            logger.warning(f"[EMBEDDER] Failed to load {fname}: {e}")

def get_memory_graph():
    if not memory_vectors:
        _load_from_disk()
    nodes, edges = [], []
    for emb in memory_vectors.values():
        nodes.append({
            "id": emb["id"],
            "label": emb["meta"].get("label", emb["text"][:24] + "..."),
            "group": emb["meta"].get("source", "system"),
        })
        if "source_id" in emb["meta"]:
            edges.append({"from": emb["meta"]["source_id"], "to": emb["id"]})
    return {"nodes": nodes, "edges": edges}

def repair_index():
    memory_vectors.clear()
    _load_from_disk()
    logger.info("[EMBEDDER] Index repaired")

def inject_watermark(origin="unknown"):
    text = f"Watermark from {origin} @ {datetime.now(timezone.utc).isoformat()}"
    vector = encode(text)
    meta = {"origin": origin, "timestamp": datetime.now(timezone.utc).isoformat()}
    return package_embedding(text, vector, meta)

# --- Initial Load ---
try:
    _load_from_disk()
    logger.info("[EMBEDDER] Initial disk load complete")
except Exception as e:
    logger.error(f"[EMBEDDER] Initial load failed: {e}")
