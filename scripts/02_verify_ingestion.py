from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.database.connection import build_database_url

def verify_ingestion():
    # Load environment variables
    load_dotenv()

    engine = create_engine(build_database_url())

    print("Verifying database ingestion...")

    with engine.connect() as conn:
        # 1. Check Total Row Count
        count_result = conn.execute(text("SELECT COUNT(*) FROM patient_encounters")).scalar()
        print(f"Total records found: {count_result}")

        if count_result == 0:
            print("⚠️ Warning: Table is empty. Ingestion may have failed.")
            return

        print("\nVerification complete. Record values were not printed.")

if __name__ == "__main__":
    verify_ingestion()