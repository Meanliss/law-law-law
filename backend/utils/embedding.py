from sentence_transformers import SentenceTransformer, models
from config import EMBEDDING_MODEL

def load_embedding_model():
    """
    Load the embedding model explicitly to avoid warnings about missing configuration.
    Uses Mean Pooling by default for VoVanPhuc/sup-SimCSE-VietNamese-phobert-base.
    """
    print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL}...", flush=True)
    try:
        # Try loading normally first
        # If it's the specific model that causes warnings, we construct it explicitly
        if 'VoVanPhuc/sup-SimCSE-VietNamese-phobert-base' in EMBEDDING_MODEL:
            word_embedding_model = models.Transformer(EMBEDDING_MODEL)
            pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension(), pooling_mode='mean')
            model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
        else:
            model = SentenceTransformer(EMBEDDING_MODEL)
            
        return model
    except Exception as e:
        print(f"[WARN] Failed to load explicitly, falling back to default: {e}", flush=True)
        return SentenceTransformer(EMBEDDING_MODEL)
