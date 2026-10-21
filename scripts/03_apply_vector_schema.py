from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.database.connection import build_database_url

def apply_pgvector():
    load_dotenv()

    engine = create_engine(build_database_url())

    print("Applying pgvector schema upgrade...")

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text(
            "ALTER TABLE patient_encounters "
            "ADD COLUMN IF NOT EXISTS clinical_embedding vector(768);"
        ))
        verify = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'patient_encounters'
              AND column_name = 'clinical_embedding';
        """)).fetchone()
        if verify is None:
            raise RuntimeError("The clinical_embedding column was not created.")
        print(f"Schema upgrade complete. Confirmed column: {verify[0]}")

if __name__ == "__main__":
    apply_pgvector()