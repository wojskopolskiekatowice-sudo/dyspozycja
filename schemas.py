from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ZastepBase(BaseModel):
    nazwa: str
    aktywny: bool = True


class ZastepCreate(ZastepBase):
    pass


class Zastep(ZastepBase):
    id: int

    class Config:
        from_attributes = True


class ZlecenieBase(BaseModel):
    numer: str
    adres: str
    opis: Optional[str] = None
    zastep_id: Optional[int] = None


class ZlecenieCreate(ZlecenieBase):
    pass


class Zlecenie(ZlecenieBase):
    id: int
    status: str
    czas_dyspozycji: datetime
    zastep: Optional[Zastep] = None

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    status: str
    uwagi: Optional[str] = None
    zmienil: Optional[str] = None


class StatusHistoria(BaseModel):
    id: int
    status: str
    czas: datetime
    uwagi: Optional[str] = None
    zmienil: Optional[str] = None

    class Config:
        from_attributes = True


class KomunikatBase(BaseModel):
    tresc: str
    nadawca: Optional[str] = "Stanowisko Kierowania"


class KomunikatCreate(KomunikatBase):
    pass


class Komunikat(KomunikatBase):
    id: int
    czas: datetime
    przeczytany: bool

    class Config:
        from_attributes = True


class ZdjecieBase(BaseModel):
    opis: Optional[str] = None


class ZdjecieCreate(ZdjecieBase):
    dane: str


class Zdjecie(ZdjecieBase):
    id: int
    zlecenie_id: int
    czas: datetime
    dane: str

    class Config:
        from_attributes = True