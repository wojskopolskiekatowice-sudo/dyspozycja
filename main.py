from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
from twilio.rest import Client
import base64

import models, schemas
from database import engine, get_db, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="System Dyspozycji")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ========== TWILIO - UZUPEŁNIJ ==========
TWILIO_ACCOUNT_SID = "WKL EJ_SWOJE_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "WKL EJ_SWOJ_AUTH_TOKEN"
TWILIO_NUMBER = "+48XXXXXXXXX"
NUMER_DO_DZWORNIENIA = "+48XXXXXXXXX"

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
# =======================================


@app.get("/")
def read_root():
    return FileResponse("index.html")


@app.get("/mobile")
def mobile():
    return FileResponse("mobile.html")


@app.get("/remiza")
def remiza():
    return FileResponse("remiza.html")


# ========== ZASTĘPY ==========
@app.post("/zastepy/", response_model=schemas.Zastep)
def create_zastep(zastep: schemas.ZastepCreate, db: Session = Depends(get_db)):
    db_zastep = models.Zastep(**zastep.dict())
    db.add(db_zastep)
    db.commit()
    db.refresh(db_zastep)
    return db_zastep


@app.get("/zastepy/", response_model=List[schemas.Zastep])
def get_zastepy(db: Session = Depends(get_db)):
    return db.query(models.Zastep).filter(models.Zastep.aktywny == True).all()


# ========== ZLECENIA ==========
@app.post("/zlecenia/", response_model=schemas.Zlecenie)
def create_zlecenie(zlecenie: schemas.ZlecenieCreate, db: Session = Depends(get_db)):
    db_zlecenie = models.Zlecenie(**zlecenie.dict())
    db.add(db_zlecenie)
    db.commit()
    db.refresh(db_zlecenie)

    historia = models.StatusHistoria(
        zlecenie_id=db_zlecenie.id,
        status="Nowe",
        uwagi="Zlecenie utworzone"
    )
    db.add(historia)
    db.commit()

    try:
        call = twilio_client.calls.create(
            to=NUMER_DO_DZWORNIENIA,
            from_=TWILIO_NUMBER,
            twiml='<Response><Say language="pl-PL">Uwaga. Nowe zgłoszenie. Sprawdź terminal.</Say></Response>'
        )
        print(f"Połączenie: {call.sid}")
    except Exception as e:
        print(f"Błąd Twilio: {e}")

    return db_zlecenie


@app.get("/zlecenia/", response_model=List[schemas.Zlecenie])
def get_zlecenia(db: Session = Depends(get_db)):
    return db.query(models.Zlecenie).order_by(models.Zlecenie.id.desc()).all()


@app.get("/zlecenia/{zlecenie_id}", response_model=schemas.Zlecenie)
def get_zlecenie(zlecenie_id: int, db: Session = Depends(get_db)):
    zlecenie = db.query(models.Zlecenie).filter(models.Zlecenie.id == zlecenie_id).first()
    if not zlecenie:
        raise HTTPException(status_code=404, detail="Zlecenie nie znalezione")
    return zlecenie


@app.get("/zlecenia/{zlecenie_id}/historia", response_model=List[schemas.StatusHistoria])
def get_historia(zlecenie_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.StatusHistoria)
        .filter(models.StatusHistoria.zlecenie_id == zlecenie_id)
        .order_by(models.StatusHistoria.czas)
        .all()
    )


@app.put("/zlecenia/{zlecenie_id}/status", response_model=schemas.Zlecenie)
def update_status(zlecenie_id: int, status_update: schemas.StatusUpdate, db: Session = Depends(get_db)):
    zlecenie = db.query(models.Zlecenie).filter(models.Zlecenie.id == zlecenie_id).first()
    if not zlecenie:
        raise HTTPException(status_code=404, detail="Zlecenie nie znalezione")

    zlecenie.status = status_update.status
    db.commit()

    historia = models.StatusHistoria(
        zlecenie_id=zlecenie_id,
        status=status_update.status,
        uwagi=status_update.uwagi,
        zmienil=status_update.zmienil
    )
    db.add(historia)
    db.commit()
    db.refresh(zlecenie)
    return zlecenie


@app.put("/zlecenia/{zlecenie_id}/zastep/{zastep_id}", response_model=schemas.Zlecenie)
def przypisz_zastep(zlecenie_id: int, zastep_id: int, db: Session = Depends(get_db)):
    zlecenie = db.query(models.Zlecenie).filter(models.Zlecenie.id == zlecenie_id).first()
    if not zlecenie:
        raise HTTPException(status_code=404, detail="Zlecenie nie znalezione")

    zastep = db.query(models.Zastep).filter(models.Zastep.id == zastep_id).first()
    if not zastep:
        raise HTTPException(status_code=404, detail="Zastęp nie znaleziony")

    zlecenie.zastep_id = zastep_id
    db.commit()
    db.refresh(zlecenie)
    return zlecenie


# ========== ZDJĘCIA ==========
@app.post("/zlecenia/{zlecenie_id}/zdjecie", response_model=schemas.Zdjecie)
async def dodaj_zdjecie(zlecenie_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    zlecenie = db.query(models.Zlecenie).filter(models.Zlecenie.id == zlecenie_id).first()
    if not zlecenie:
        raise HTTPException(status_code=404, detail="Zlecenie nie znalezione")

    tresc = await file.read()
    dane_b64 = base64.b64encode(tresc).decode("utf-8")

    zdjecie = models.Zdjecie(
        zlecenie_id=zlecenie_id,
        dane=dane_b64,
        opis=file.filename
    )
    db.add(zdjecie)
    db.commit()
    db.refresh(zdjecie)
    return zdjecie


@app.get("/zlecenia/{zlecenie_id}/zdjecia", response_model=List[schemas.Zdjecie])
def get_zdjecia(zlecenie_id: int, db: Session = Depends(get_db)):
    return db.query(models.Zdjecie).filter(models.Zdjecie.zlecenie_id == zlecenie_id).all()


# ========== KOMUNIKATY ==========
@app.post("/komunikaty/", response_model=schemas.Komunikat)
def create_komunikat(komunikat: schemas.KomunikatCreate, db: Session = Depends(get_db)):
    db_komunikat = models.Komunikat(**komunikat.dict())
    db.add(db_komunikat)
    db.commit()
    db.refresh(db_komunikat)
    return db_komunikat


@app.get("/komunikaty/", response_model=List[schemas.Komunikat])
def get_komunikaty(db: Session = Depends(get_db)):
    return db.query(models.Komunikat).order_by(models.Komunikat.czas.desc()).all()


@app.put("/komunikaty/{komunikat_id}/przeczytany")
def oznacz_przeczytany(komunikat_id: int, db: Session = Depends(get_db)):
    komunikat = db.query(models.Komunikat).filter(models.Komunikat.id == komunikat_id).first()
    if not komunikat:
        raise HTTPException(status_code=404, detail="Komunikat nie znaleziony")
    komunikat.przeczytany = True
    db.commit()
    return {"ok": True}