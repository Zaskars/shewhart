from sqlalchemy import Column, Integer, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class Measurement(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True, autoincrement=True)  # связать с Competition, добавить on delete cascade
    proportion = Column(Float)
    sample_size = Column(Integer)
    measurement_time = Column(DateTime, default=datetime.datetime.utcnow)


