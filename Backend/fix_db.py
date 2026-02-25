import asyncio
from sqlalchemy import text
from app.database.connection import engine

def main():
    print("Connecting to database...")
    with engine.begin() as conn:
        print("Adding pattern_hash...")
        conn.execute(text("ALTER TABLE generated_papers ADD COLUMN IF NOT EXISTS pattern_hash VARCHAR(64);"))
        print("Adding validation_result...")
        conn.execute(text("ALTER TABLE generated_papers ADD COLUMN IF NOT EXISTS validation_result JSONB;"))
        print("Adding question_count...")
        conn.execute(text("ALTER TABLE generated_papers ADD COLUMN IF NOT EXISTS question_count INTEGER;"))
    print("Success! Database schema updated.")

if __name__ == "__main__":
    main()
