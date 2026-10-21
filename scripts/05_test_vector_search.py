from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from src.database.connection import build_database_url

def test_vector_search():
    load_dotenv()
    engine = create_engine(build_database_url())

    print("⏳ Loading local BioClinical ModernBERT model...")
    model = SentenceTransformer('NeuML/bioclinical-modernbert-base-embeddings')

    # 1. Define a complex, natural language medical query
    query_text = "Patient presenting with severe liver disease and fluid retention needing diuretics"
    print(f"\n🔍 Semantic Query: '{query_text}'")

    # 2. Vectorize the query locally
    query_vector = model.encode(query_text).tolist()

    # 3. Search with pgvector's cosine distance operator (<=>)
    search_sql = text("""
        SELECT
            clinical_embedding <=> CAST(:query_vector AS vector(768)) AS cosine_distance
        FROM patient_encounters
        WHERE clinical_embedding IS NOT NULL
        ORDER BY cosine_distance ASC
        LIMIT 3;
    """)

    with engine.connect() as conn:
        # Pass the vector as a string-formatted array
        results = conn.execute(search_sql, {"query_vector": str(query_vector)}).mappings().fetchall()

        print(f"\nRetrieved {len(results)} nearest matches; record values were not printed.")
        for rank, row in enumerate(results, 1):
            print(f"Rank {rank} (distance: {row['cosine_distance']:.4f})")

if __name__ == "__main__":
    test_vector_search()