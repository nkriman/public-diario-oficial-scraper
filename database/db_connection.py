import json
from sqlalchemy import create_engine, MetaData, Column, Integer, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from urllib.parse import quote
from urllib.parse import quote_plus
from sqlalchemy import URL




def get_connection(user, password, host):
    url_object = URL.create(
    "postgresql",
    username=user,
    password=password,  # plain (unescaped) text
    host=host,
    database="postgres",
)
    #password = quote(password)
    #DATABASE_URL = f"postgresql://{user}:%s@{host}/postgres?sslmode=require" % quote_plus(password)  # azure
    #print(DATABASE_URL)
    engine = create_engine(url_object)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return engine


# Table class definition
class Base(DeclarativeBase):
    pass


class CompanyRecord(Base):
    __tablename__ = "dof_2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    json_payload: Mapped[dict] = mapped_column(JSON)
    batch_id: str = Column(String)
