import os

from sqlalchemy.engine import URL


def build_database_url() -> URL | str:
    host = os.getenv("DB_HOST")
    if host:
        required = ("DB_USER", "DB_PASSWORD", "DB_NAME")
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError(
                f"Missing required database settings: {', '.join(missing)}"
            )

        return URL.create(
            "postgresql+psycopg",
            username=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=host,
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.environ["DB_NAME"],
        )

    configured_url = os.getenv("POSTGRES_URL")
    if configured_url:
        return configured_url

    raise RuntimeError(
        "Set DB_HOST, DB_USER, DB_PASSWORD, and DB_NAME, or set POSTGRES_URL."
    )
