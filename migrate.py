
import sqlite3
import os

from settings import Settings


def add_missing_columns(cursor, table_name, required_columns):

    print(f"\nChecking {table_name} table...")

    # Check whether the table exists.
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,)
    )

    if cursor.fetchone() is None:
        raise sqlite3.OperationalError(
            f"Table '{table_name}' does not exist."
        )

    # Get existing columns.
    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    existing_columns = [
        column[1] for column in cursor.fetchall()
    ]

    # Add missing columns.
    for column_name, column_type in required_columns.items():

        if column_name not in existing_columns:

            sql = (
                f"ALTER TABLE {table_name} "
                f"ADD COLUMN {column_name} {column_type}"
            )

            cursor.execute(sql)

            print(f"Added column: {column_name}")

        else:

            print(f"Column already exists: {column_name}")


def migrate_database():

    database_uri = Settings.SQLALCHEMY_DATABASE_URI

    # Convert SQLite URI into a database file path.
    database_path = database_uri.replace(
        "sqlite:///", "", 1
    )

    if not os.path.exists(database_path):

        print("Database file does not exist.")
        print("Please run app.py first to create the database.")

        return

    connection = None

    try:

        connection = sqlite3.connect(database_path)

        cursor = connection.cursor()

        # ====================================================
        # 1. JOB SEEKER PROFILE MIGRATION
        # ====================================================

        profile_columns = {

            "resume_filename": "VARCHAR(255)",

            "parsed_resume_json": "JSON",

            "resume_parsed_at": "DATETIME",

            "resume_parse_status": "VARCHAR(20)"

        }

        add_missing_columns(
            cursor,
            "job_seeker_profiles",
            profile_columns
        )

        # ====================================================
        # 2. JOB EMBEDDING MIGRATION
        # ====================================================

        job_columns = {

            "job_embedding": "JSON",

            "embedding_model": "VARCHAR(150)",

            "embedding_generated_at": "DATETIME"

        }

        add_missing_columns(
            cursor,
            "jobs",
            job_columns
        )

        # Commit all changes.
        connection.commit()

        print("\n======================================")
        print("Database migration completed successfully.")
        print("======================================")

    except sqlite3.Error as error:

        if connection:
            connection.rollback()

        print("\nDatabase migration failed:")
        print(error)

    finally:

        if connection:
            connection.close()


if __name__ == "__main__":

    migrate_database()
