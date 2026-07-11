from sqlalchemy import Column, BigInteger, String, DECIMAL, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
Base = declarative_base()


class DrugSpecification(Base):
    __tablename__ = "drug_specification"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("drug.id"))
    name: Mapped[str] = mapped_column(String(100))
    value: Mapped[dict] = mapped_column(JSON, nullable=True)

class Drug(Base):
    __tablename__ = "drug"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category_id = Column(BigInteger)
    price = Column(DECIMAL(10, 2))
    image = Column(String(255))
    description = Column(Text)
    approval_number = Column(String(50))
    manufacturer = Column(String(200))
    status = Column(Integer, default=1)
    # ... 其他字段
    specifications = relationship("DrugSpecification",
                                  backref="drug",
                                  cascade="all, delete-orphan")


class DrugUsage(Base):
    __tablename__ = "drug_usage"
    id = Column(BigInteger, primary_key=True)
    name = Column(String(50))

class DrugUsageRelation(Base):
    __tablename__ = "drug_usage_relation"
    id = Column(BigInteger, primary_key=True)
    drug_id = Column(BigInteger, ForeignKey("drug.id"))
    usage_id = Column(BigInteger, ForeignKey("drug_usage.id"))

class DrugUsageSynonym(Base):
    __tablename__ = "drug_usage_synonym"
    id = Column(BigInteger, primary_key=True)
    usage_id = Column(BigInteger, ForeignKey("drug_usage.id"))
    synonym = Column(String(50))

