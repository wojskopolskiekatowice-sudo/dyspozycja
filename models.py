from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Zastep(Base):
    __tablename__ = "zastepy"

    id = Column(Integer, primary_key=True, index=True)
    nazwa = Column(String, unique=True, index=True)
    aktywny = Column(Boolean, default=True)

    zlecenia = relationship("Zlecenie", back_populates="zastep")


class Zlecenie(Base):
    __tablename__ = "zlecenia"

    id = Column(Integer, primary_key=True, index=True)
    numer = Column(String, index=True)
    adres = Column(String)
    opis = Column(Text, nullable=True)
    czas_dyspozycji = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Nowe")
    zastep_id = Column(Integer, ForeignKey("zastepy.id"), nullable=True)

    zastep = relationship("Zastep", back_populates="zlecenia")
    historia = relationship("StatusHistoria", back_populates="zlecenie", order_by="StatusHistoria.czas")


class StatusHistoria(Base):
    __tablename__ = "status_historia"

    id = Column(Integer, primary_key=True, index=True)
    zlecenie_id = Column(Integer, ForeignKey("zlecenia.id"))
    status = Column(String)
    czas = Column(DateTime, default=datetime.utcnow)
    uwagi = Column(Text, nullable=True)
    zmienil = Column(String, nullable=True)

    zlecenie = relationship("Zlecenie", back_populates="historia")


class Komunikat(Base):
    __tablename__ = "komunikaty"

    id = Column(Integer, primary_key=True, index=True)
    tresc = Column(Text)
    nadawca = Column(String, default="Stanowisko Kierowania")
    czas = Column(DateTime, default=datetime.utcnow)
    przeczytany = Column(Boolean, default=False)


class Zdjecie(Base):
    __tablename__ = "zdjecia"

    id = Column(Integer, primary_key=True, index=True)
    zlecenie_id = Column(Integer, ForeignKey("zlecenia.id"))
    dane = Column(Text)  # base64
    opis = Column(String, nullable=True)
    czas = Column(DateTime, default=datetime.utcnow)

    zlecenie = relationship("Zlecenie", backref="zdjecia")