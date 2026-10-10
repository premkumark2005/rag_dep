import sys
sys.path.insert(0, ".")

print("Loading sentence-transformers...")
from sentence_transformers import SentenceTransformer
try:
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("SentenceTransformer loaded successfully!")
except Exception as e:
    print(f"Failed to load SentenceTransformer: {e}")

print("Loading cross-encoder...")
from sentence_transformers import CrossEncoder
try:
    model_ce = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    print("CrossEncoder loaded successfully!")
except Exception as e:
    print(f"Failed to load CrossEncoder: {e}")
