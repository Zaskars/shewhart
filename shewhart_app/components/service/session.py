from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import shewhart_app.components.content as content

DB_URL = (
    f"postgresql://{content.DB_USER}:{content.DB_PASS}@localhost:1337/{content.DB_NAME}"
)

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
