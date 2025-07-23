import random
from sqlalchemy import (
    Column, Integer, String, ForeignKey, JSON, create_engine
)
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker, relationship

Base = declarative_base()

class Comprador(Base):
    __tablename__ = 'comprador'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=False)
    endereco = Column(String, nullable=False)

    cartelas = relationship('Cartela', back_populates='comprador')

    def __init__(self, nome: str, telefone: str, endereco: str):
        self.nome = nome
        self.telefone = telefone
        self.endereco = endereco

class Cartela(Base):
    __tablename__ = 'cartela'
    id = Column(Integer, primary_key=True, default=lambda: random.randint(100000, 999999))
    id_comprador = Column(Integer, ForeignKey('comprador.id'), nullable=False)
    numbers = Column(JSON, nullable=False)
    pdf_path = Column(String, nullable=False)

    comprador = relationship('Comprador', back_populates='cartelas')

    def __init__(self, id_comprador: int, numbers: list, pdf_path: str):
        self.id_comprador = id_comprador
        self.numbers = numbers
        self.pdf_path = pdf_path

# Configura engine e sessão
engine = create_engine(
    'sqlite:///bingo.db',
    connect_args={"check_same_thread": False},
    echo=False
)
Session = scoped_session(sessionmaker(bind=engine))
Base.metadata.create_all(engine)  # type: ignore  # metadata warning silenciado
