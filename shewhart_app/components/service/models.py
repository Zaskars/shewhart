from sqlalchemy import Column, Integer, DateTime, Float, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()


class Measurement(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proportion = Column(Float)
    sample_size = Column(Integer)
    measurement_time = Column(DateTime, default=datetime.datetime.utcnow)
    binding_id = Column(Integer, ForeignKey("bindings.id"))
    binding = relationship("Binding", back_populates="measurements")


# class XData(Base):
#     __tablename__ = 'x_data'
#     id = Column(Integer, primary_key=True)
#     value = Column(Float)
#     sample_size = Column(Integer)
#     binding_id = Column(Integer, ForeignKey('bindings.id'))
#     binding = relationship("Binding", back_populates="x_data")
#
#
# class RData(Base):
#     __tablename__ = 'r_data'
#     id = Column(Integer, primary_key=True)
#     value = Column(Float)
#     sample_size = Column(Integer)
#     binding_id = Column(Integer, ForeignKey('bindings.id'))
#     binding = relationship("Binding", back_populates="r_data")


class IndividualMeasurement(Base):
    __tablename__ = "individual_measurements"
    id = Column(Integer, primary_key=True)
    value = Column(Float, nullable=False)
    binding_id = Column(Integer, ForeignKey("bindings.id"))
    binding = relationship("Binding", back_populates="i_measurements")
    chart_id = Column(Integer, ForeignKey("charts.id"))
    chart = relationship("Chart", back_populates="measurements")


class Chart(Base):
    __tablename__ = "charts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    binding_id = Column(Integer, ForeignKey("bindings.id"))
    binding = relationship("Binding", back_populates="charts")
    measurements = relationship(
        "IndividualMeasurement",
        order_by=IndividualMeasurement.id,
        back_populates="chart",
    )


class Binding(Base):
    __tablename__ = "bindings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    measurements = relationship(
        "Measurement", order_by=Measurement.id, back_populates="binding"
    )
    i_measurements = relationship(
        "IndividualMeasurement",
        order_by=IndividualMeasurement.id,
        back_populates="binding",
    )
    charts = relationship("Chart", order_by=Chart.id, back_populates="binding")
