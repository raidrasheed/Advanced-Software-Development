from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from models.doctors import Doctor
from models.clinics import Clinic
from passlib.hash import bcrypt
from models.appointments import Appointment
from models.bookings import Booking
from utils.func import week_dates, render_template, requires_roles  
from utils.func import MANAGER, ADMIN,CUSTOMER


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

admin_router = APIRouter()

@admin_router.get("/admin")
def dashboard(request: Request):
    user = request.session.get("user") 
    if user and user['role'] == 'CUSTOMER':
        return RedirectResponse("/")
    # if not user:
    #     return RedirectResponse("/login")
    return render_template(request, "admin/dashboard.html", {"request": request, "user": user})

@admin_router.get("/admin/doctors")
def doctors(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user") 
    if user and user['role'] == 'CUSTOMER':
        return RedirectResponse("/")
    

    if user and user['role'] == 'DOCTOR':
        doctors = db.query(Doctor).filter(Doctor.user_id == user['id']).all()
    else:
        doctors = db.query(Doctor).all()
    clinics = db.query(Clinic).all()
    if not user:
        return RedirectResponse("/login")
    return render_template(request, "admin/doctors.html", {"request": request, "user": user, "doctors": doctors, "clinics": clinics})


@admin_router.get("/admin/appointments")
def appointments(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    appointments = []

    if user and user['role'] == 'CUSTOMER':
        return RedirectResponse("/")

    if not user:
        return RedirectResponse("/login")
    
    if user and user['role'] == 'CUSTOMER':
        appointments = db.query(Appointment).filter(
        Appointment.patient_id == user.get("id")
    ).all()
    elif user and user['role'] == 'ADMIN':
        appointments = db.query(Appointment).all()
    elif user and user['role'] == 'DOCTOR':
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == user['doctor_id']
        ).all()
    
    
    return render_template(request, "admin/appointments.html", {"request": request, "user": user, "appointments": appointments})    

@admin_router.get("/admin/rooms")
def rooms(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    # Query rooms and join with clinics to group by clinic
    clinics_with_rooms = db.query(Clinic).join(Clinic.rooms).all()

    return render_template(request, "admin/rooms.html", {"request": request, "user": user, "clinics": clinics_with_rooms})

@admin_router.get("/admin/duty_roster")
def duty_roster(request: Request, db: Session = Depends(get_db), clinic_id: str = None):
    user = request.session.get("user")

    ##access only managers and admins
    if user['role'] != 'MANAGER' and user['role'] != 'ADMIN' and user['role'] != 'DOCTOR':
        return RedirectResponse("/admin")

    if user['role'] == 'DOCTOR':
        doctor = db.query(Doctor).filter(Doctor.user_id == user['id']).first()
        doctors = [{"id": doctor.id, "full_name": doctor.full_name}]
    else:
        doctors = [{"id": doctor.id, "full_name": doctor.full_name} for doctor in db.query(Doctor).filter(Doctor.clinic_id == clinic_id).all()]
    
    clinics = db.query(Clinic).all()
    
    
    if not user:
        return RedirectResponse("/login")
    return render_template(request, "admin/duty_roster.html", {"request": request, "user": user, "doctors": doctors, "clinics": clinics, "clinic_id": clinic_id, "week_dates": week_dates})

@admin_router.get("/admin/manage")
def manage(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    
    users = db.query(User).all()
    doctors = db.query(Doctor).all()
    return render_template(request, "admin/manage.html", {"request": request, "user": user, "users": users, "doctors": doctors  })


@admin_router.get("/admin/bookings")
def bookings(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    
    bookings = db.query(Booking).all()
    return render_template(request, "admin/bookings.html", {"request": request, "user": user, "bookings": bookings})

@admin_router.get("/admin/clinics")
@requires_roles(MANAGER,ADMIN)
def clinics(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    clinics = db.query(Clinic).all()
    return render_template(request, "admin/clinics.html", {"request": request, "user": user, "clinics": clinics })
