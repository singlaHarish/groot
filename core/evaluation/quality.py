from core.vectorstore.embeddings import get_embedding_model

def compute_response_quality(full_response: str, optimized_response: str) -> dict:
    """
    Computes semantic similarity between two LLM responses using sentence embeddings.
    """
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        
        full_resp_clean = full_response.strip()
        opt_resp_clean = optimized_response.strip()
        
        if not full_resp_clean or not opt_resp_clean:
            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "quality_label": "Error",
                "description": "One or both responses are empty"
            }
        
        embedding_model = get_embedding_model()
        if embedding_model is None:
            raise RuntimeError("Could not load embedding model")
        
        full_emb = embedding_model.encode(full_resp_clean, normalize_embeddings=True)
        opt_emb = embedding_model.encode(opt_resp_clean, normalize_embeddings=True)
        
        similarity = cosine_similarity([opt_emb], [full_emb])[0][0]
        
        full_sentences = [s.strip() for s in full_resp_clean.split('.') if s.strip()]
        opt_sentences = [s.strip() for s in opt_resp_clean.split('.') if s.strip()]
        
        if full_sentences and opt_sentences:
            full_sent_embs = embedding_model.encode(full_sentences, normalize_embeddings=True)
            opt_sent_embs = embedding_model.encode(opt_sentences, normalize_embeddings=True)
            
            matches = 0
            for full_sent_emb in full_sent_embs:
                best_match = cosine_similarity([full_sent_emb], opt_sent_embs).max()
                if best_match > 0.6:
                    matches += 1
            
            recall = matches / len(full_sent_embs) if full_sent_embs.size > 0 else 0
        else:
            recall = similarity
        
        precision = similarity
        
        if precision + recall > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0
        
        if f1 >= 0.75:
            quality_label = "High Quality"
            description = f"Excellent semantic alignment ({f1:.1%})"
        elif f1 >= 0.60:
            quality_label = "Good Quality"
            description = f"Good semantic coverage ({f1:.1%})"
        elif f1 >= 0.45:
            quality_label = "Moderate Quality"
            description = f"Moderate quality retention ({f1:.1%})"
        else:
            quality_label = "Low Quality"
            description = f"Significant quality loss ({f1:.1%})"
        
        return {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "quality_label": quality_label,
            "description": description
        }
        
    except ImportError as e:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "quality_label": "Unavailable",
            "description": f"Quality metrics unavailable: {str(e)}"
        }
    except Exception as e:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "quality_label": "Error",
            "description": f"Quality computation failed: {str(e)}"
        }
