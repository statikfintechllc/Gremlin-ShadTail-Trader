#!/usr/bin/env python3

# ─────────────────────────────────────────────────────────────
# © 2025 StatikFintechLLC
# Contact: ascend.gremlin@gmail.com
# ─────────────────────────────────────────────────────────────

# Gremlin Trader Memory Embedder & Vector Store Core

import os
import json
import sqlite3
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Dict, List, Any, Optional

# Import from centralized globals
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.Gremlin_Trade_Core.globals import (
    CFG, MEM, logger, setup_module_logger, resolve_path, DATA_DIR,
    METADATA_DB_PATH, CHROMA_DB_PATH, VECTOR_STORE_DIR
)

# Module logger
embedder_logger = setup_module_logger("memory", "embedder")

# Initialize chromadb if available
try:
    import chromadb
    CHROMA_AVAILABLE = True
    embedder_logger.info("ChromaDB available")
except ImportError:
    chromadb = None
    CHROMA_AVAILABLE = False
    embedder_logger.warning("ChromaDB not available - using fallback storage")

# Initialize sentence transformers if available
try:
    from sentence_transformers import SentenceTransformer
    ML_AVAILABLE = True
    embedder_logger.info("SentenceTransformers available")
except ImportError:
    SentenceTransformer = None
    ML_AVAILABLE = False
    embedder_logger.warning("SentenceTransformers not available - using dummy encoder")

# Fallback encoder
def dummy_encode(text):
    """Dummy encoder when sentence_transformers not available"""
    dimension = MEM.get("embedding", {}).get("dimension", 384)
    # Create a simple hash-based encoding for consistency
    hash_val = hash(text) % (2**31)
    np.random.seed(hash_val)
    return np.random.rand(dimension).astype(np.float32)

# Configuration & Paths
storage_conf = MEM.get("storage", {})
if not isinstance(storage_conf, dict):
    embedder_logger.error("[EMBEDDER] storage config malformed; resetting to empty dict")
    storage_conf = {}

BASE_VECTOR_PATH = storage_conf.get("vector_store_path", str(VECTOR_STORE_DIR))
CHROMA_DIR = Path(BASE_VECTOR_PATH) / "chroma"
LOCAL_INDEX_PATH = Path(BASE_VECTOR_PATH) / "local_index"

# Use dashboard-selected backend for toggling
dashboard_selected_backend = MEM.get('dashboard_selected_backend', 'chromadb')
USE_CHROMA = dashboard_selected_backend == "chromadb" and CHROMA_AVAILABLE

# Ensure directories exist
for path in [CHROMA_DIR, LOCAL_INDEX_PATH]:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        embedder_logger.error(f"[EMBEDDER] Failed to create directory {path}: {e}")

# Memory storage
memory_vectors = {}

# Initialize transformer model
_model = None

def get_model():
    """Get or initialize the sentence transformer model"""
    global _model
    if _model is None and ML_AVAILABLE:
        try:
            model_name = MEM.get("embedding", {}).get("model", "all-MiniLM-L6-v2")
            _model = SentenceTransformer(model_name)
            embedder_logger.info(f"Initialized SentenceTransformer model: {model_name}")
        except Exception as e:
            embedder_logger.error(f"Error initializing model: {e}")
            _model = None
    return _model

def encode(text: str) -> np.ndarray:
    """Encode text to vector embedding"""
    try:
        model = get_model()
        if model is not None:
            return model.encode(text)
        else:
            return dummy_encode(text)
    except Exception as e:
        embedder_logger.error(f"Error encoding text: {e}")
        return dummy_encode(text)

# Chroma Client Setup
_chroma_client = None
_collection = None

def get_chroma_client():
    """Get or initialize ChromaDB client"""
    global _chroma_client, _collection
    
    if not CHROMA_AVAILABLE or not USE_CHROMA:
        return None, None
        
    if _chroma_client is None:
        try:
            _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            _collection = _chroma_client.get_or_create_collection(name="gremlin_memory")
            embedder_logger.info("ChromaDB client initialized")
        except Exception as e:
            embedder_logger.error(f"Failed to initialize Chroma client: {e}")
            _chroma_client = None
            _collection = None
            
    return _chroma_client, _collection

def add_to_chroma(text: str, emb_id: str, vector: np.ndarray, meta: Dict[str, Any]):
    """Add embedding to ChromaDB"""
    try:
        client, collection = get_chroma_client()
        if collection is None:
            embedder_logger.warning("ChromaDB not available for storage")
            return False
            
        collection.add(
            documents=[text],
            embeddings=[vector.tolist() if hasattr(vector, "tolist") else list(vector)],
            metadatas=[meta],
            ids=[emb_id]
        )
        embedder_logger.debug(f"Added to ChromaDB: {emb_id}")
        return True
        
    except Exception as e:
        embedder_logger.error(f"ChromaDB add failed for {emb_id}: {e}")
        return False

def get_backend_status():
    """Get status of both FAISS and Chroma backends."""
    status = {
        "chromadb_available": CHROMA_AVAILABLE,
        "chroma_collection_count": 0,
        "local_index_count": len(memory_vectors),
        "current_backend": dashboard_selected_backend
    }

    # Get Chroma count
    if CHROMA_AVAILABLE and USE_CHROMA:
        try:
            client, collection = get_chroma_client()
            if collection is not None:
                status["chroma_collection_count"] = collection.count()
        except Exception as e:
            embedder_logger.warning(f"Failed to get Chroma count: {e}")
    
    return status

def get_current_backend():
    """Get current selected backend"""
    return dashboard_selected_backend

def store_embedding(embedding: Dict[str, Any]) -> Dict[str, Any]:
    """Store embedding in selected backend"""
    try:
        emb_id = embedding["id"]
        text = embedding["text"]
        vector = np.array(embedding["vector"])
        meta = embedding["meta"]
        
        # Store in memory
        memory_vectors[emb_id] = embedding
        
        # Store in ChromaDB if enabled
        current_backend = get_current_backend()
        if current_backend == "chromadb" and USE_CHROMA:
            add_to_chroma(text, emb_id, vector, meta)
        
        # Always store locally as backup
        _write_to_disk(embedding)
        
        embedder_logger.info(f"Stored embedding: {emb_id} using {current_backend}")
        return embedding
        
    except Exception as e:
        embedder_logger.error(f"Error storing embedding: {e}")
        return embedding

def package_embedding(text: str, vector: np.ndarray, meta: Dict[str, Any]) -> Dict[str, Any]:
    """Package embedding with metadata and store it"""
    try:
        import uuid
        embedding_id = str(uuid.uuid4())
        
        embedding = {
            "id": embedding_id,
            "text": text,
            "vector": vector.tolist() if hasattr(vector, 'tolist') else list(vector),
            "meta": {
                **meta,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "id": embedding_id
            }
        }
        
        # Store the embedding
        return store_embedding(embedding)
        
    except Exception as e:
        embedder_logger.error(f"Error packaging embedding: {e}")
        return {}

def archive_plan(vector_path="backend/Gremlin-Trade-Core/Gremlin-Trader-Strategies/Past-Strategies.jsonl"):
    """Archive strategy plan"""
    try:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        archive_dir = Path("GremlinGPT") / "docs"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive = archive_dir / f"planlog_{stamp}.jsonl"
        
        if Path(vector_path).exists():
            shutil.copyfile(vector_path, archive)
            embedder_logger.info(f"Plan archived: {archive}")
            return str(archive)
        else:
            embedder_logger.warning(f"Source file not found: {vector_path}")
            return None
            
    except Exception as e:
        embedder_logger.error(f"Archive failed: {e}")
        return None

def auto_commit(file_path: str):
    """Auto-commit file changes to git"""
    if not file_path or not os.path.exists(file_path):
        embedder_logger.warning(f"auto_commit: invalid path {file_path}")
        return
        
    try:
        os.system(f"git add {file_path}")
        os.system(f'git commit -m "[autocommit] Updated: {file_path}"')
        embedder_logger.info(f"auto_commit succeeded for {file_path}")
    except Exception as e:
        embedder_logger.error(f"Git commit failed: {e}")

def get_all_embeddings(limit=50):
    """Get all embeddings from memory"""
    if not memory_vectors:
        _load_from_disk()
    return list(memory_vectors.values())[:limit]

def get_embedding_by_id(emb_id: str):
    """Get specific embedding by ID"""
    if emb_id not in memory_vectors:
        _load_from_disk()
    return memory_vectors.get(emb_id)

def query_embeddings(query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Query embeddings by similarity"""
    try:
        # Generate query embedding
        query_vector = encode(query_text)
        
        # Get all embeddings
        all_embeddings = get_all_embeddings()
        
        # Calculate similarities
        similarities = []
        for emb in all_embeddings:
            try:
                emb_vector = np.array(emb["vector"])
                similarity = np.dot(query_vector, emb_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(emb_vector)
                )
                similarities.append((similarity, emb))
            except Exception as e:
                embedder_logger.error(f"Error calculating similarity: {e}")
                continue
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [emb for _, emb in similarities[:limit]]
        
    except Exception as e:
        embedder_logger.error(f"Error querying embeddings: {e}")
        return []

def _write_to_disk(embedding: Dict[str, Any]):
    """Write embedding to local disk storage"""
    try:
        path = LOCAL_INDEX_PATH / f"{embedding['id']}.json"
        with open(path, "w") as f:
            json.dump(embedding, f, indent=2)
    except Exception as e:
        embedder_logger.error(f"Failed to write {embedding['id']} to disk: {e}")

def _load_from_disk():
    """Load embeddings from local disk storage"""
    if not LOCAL_INDEX_PATH.exists():
        embedder_logger.warning(f"Local index missing: {LOCAL_INDEX_PATH}")
        return
        
    for fname in LOCAL_INDEX_PATH.iterdir():
        if not fname.name.endswith(".json"):
            continue
            
        try:
            with open(fname, "r") as f:
                emb = json.load(f)
            memory_vectors[emb["id"]] = emb
        except Exception as e:
            embedder_logger.warning(f"Failed to load {fname}: {e}")

def get_memory_graph():
    """Get memory graph for visualization"""
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
    """Repair the memory index"""
    memory_vectors.clear()
    _load_from_disk()
    embedder_logger.info("Index repaired")

def inject_watermark(origin="unknown"):
    """Inject watermark for tracking"""
    text = f"Watermark from {origin} @ {datetime.now(timezone.utc).isoformat()}"
    vector = encode(text)
    meta = {"origin": origin, "timestamp": datetime.now(timezone.utc).isoformat()}
    return package_embedding(text, vector, meta)

# Initialize databases
def init_vector_databases():
    """Initialize vector databases"""
    try:
        # Initialize ChromaDB
        if CHROMA_AVAILABLE and USE_CHROMA:
            client, collection = get_chroma_client()
            if collection is not None:
                embedder_logger.info("ChromaDB initialized successfully")
        
        # Initialize local storage
        LOCAL_INDEX_PATH.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        _load_from_disk()
        
        embedder_logger.info("Vector databases initialized")
        
    except Exception as e:
        embedder_logger.error(f"Error initializing vector databases: {e}")

# Initialize on import
try:
    init_vector_databases()
    embedder_logger.info("Embedder initialization complete")
except Exception as e:
    embedder_logger.error(f"Embedder initialization failed: {e}")
