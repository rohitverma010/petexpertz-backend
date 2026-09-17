import json
import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PetExpertz Clinic API",
    description="Backend API for PetExpertz Veterinary Clinic — Zirakpur, Punjab",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"


def load_json(filename: str):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Root — friendly landing response instead of a bare 404 at "/"
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "PetExpertz Clinic API",
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "PetExpertz Clinic API"}


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

@app.get("/api/services", tags=["Services"])
def get_services():
    return load_json("services.json")


# ---------------------------------------------------------------------------
# Doctors
# ---------------------------------------------------------------------------

@app.get("/api/doctors", tags=["Doctors"])
def get_doctors():
    return load_json("doctors.json")


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@app.get("/api/products", tags=["Products"])
def get_all_products():
    return load_json("products.json")


@app.get("/api/products/food", tags=["Products"])
def get_food_products():
    return load_json("products.json")["food"]


@app.get("/api/products/essentials", tags=["Products"])
def get_essentials():
    return load_json("products.json")["essentials"]


@app.get("/api/products/medicines", tags=["Products"])
def get_medicines():
    return load_json("products.json")["medicines"]


# ---------------------------------------------------------------------------
# Testimonials
# ---------------------------------------------------------------------------

@app.get("/api/testimonials", tags=["Testimonials"])
def get_testimonials():
    return load_json("testimonials.json")


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------

@app.post("/api/appointments", response_model=schemas.AppointmentResponse, status_code=201, tags=["Appointments"])
def book_appointment(payload: schemas.AppointmentCreate, db: Session = Depends(get_db)):
    # Enforce one booking per date+time slot so two owners can't be given the
    # same appointment. "Emergency (ASAP)" isn't a fixed slot, so it's exempt.
    if payload.preferred_time != "Emergency (ASAP)":
        clash = (
            db.query(models.Appointment)
            .filter(
                models.Appointment.preferred_date == payload.preferred_date,
                models.Appointment.preferred_time == payload.preferred_time,
                models.Appointment.status != "Cancelled",
            )
            .first()
        )
        if clash:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"The {payload.preferred_time} slot on {payload.preferred_date} "
                    "is already booked. Please choose a different time."
                ),
            )

    appointment = models.Appointment(**payload.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@app.get("/api/appointments", response_model=List[schemas.AppointmentResponse], tags=["Appointments"])
def list_appointments(
    status: Optional[str] = Query(None, description="Filter by status: Pending, Confirmed, Completed, Cancelled"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Appointment).order_by(models.Appointment.submitted_at.desc())
    if status:
        query = query.filter(models.Appointment.status == status)
    return query.all()


@app.get("/api/appointments/{appointment_id}", response_model=schemas.AppointmentResponse, tags=["Appointments"])
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@app.patch("/api/appointments/{appointment_id}/status", response_model=schemas.AppointmentResponse, tags=["Appointments"])
def update_appointment_status(
    appointment_id: int,
    payload: schemas.AppointmentStatusUpdate,
    db: Session = Depends(get_db),
):
    valid_statuses = {"Pending", "Confirmed", "Completed", "Cancelled"}
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid_statuses)}")

    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = payload.status
    db.commit()
    db.refresh(appointment)
    return appointment


@app.delete("/api/appointments/{appointment_id}", status_code=204, tags=["Appointments"])
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    db.delete(appointment)
    db.commit()


# ---------------------------------------------------------------------------
# Orders (cart checkout)
# ---------------------------------------------------------------------------

@app.post("/api/orders", response_model=schemas.OrderResponse, status_code=201, tags=["Orders"])
def place_order(payload: schemas.OrderCreate, db: Session = Depends(get_db)):
    order = models.Order(**payload.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    # order_number depends on the id assigned by the insert above, so it's
    # backfilled in a second write rather than computed beforehand.
    order.order_number = f"PEX{order.id:04d}"
    db.commit()
    db.refresh(order)
    return order


@app.get("/api/orders", response_model=List[schemas.OrderResponse], tags=["Orders"])
def list_orders(db: Session = Depends(get_db)):
    return db.query(models.Order).order_by(models.Order.placed_at.desc()).all()


@app.get("/api/orders/{order_id}", response_model=schemas.OrderResponse, tags=["Orders"])
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
