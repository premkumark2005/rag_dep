import sys
sys.path.insert(0, ".")

import traceback
from backend.config import settings
from backend.services.rag_service import RAGService

def main():
    print("Initializing RAGService...")
    print(f"LLM_PROVIDER: {settings.llm_provider}")
    print(f"LLM_MODEL: {settings.llm_model}")
    print(f"LLM_API_KEY present: {bool(settings.llm_api_key)}")
    
    rag_service = RAGService(settings)
    rag_service.ensure_index_loaded()
    
    question = "Who created Python and when was it first released?"
    print(f"\nRunning Phase 2 query: '{question}'")
    try:
        response = rag_service.query_phase2(question)
        print("SUCCESS!")
        print(f"Request ID: {response.request_id}")
        print(f"Final Answer: {response.final_answer}")
    except Exception as e:
        print("\n--- ERROR DETECTED ---")
        traceback.print_exc()

if __name__ == "__main__":
    main()
