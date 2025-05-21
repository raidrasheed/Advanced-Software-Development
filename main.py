from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from fastapi.responses import JSONResponse
from sqlalchemy import func
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from utils.func import render_template
from api.api import api_router
from admin.admin import admin_router

from datetime import date, datetime 

from database import SessionLocal, engine
from database import Base
from models import User
from models.doctors import Doctor
from models.services import Services
from models.clinics import Clinic
from models.schedule import Schedule
from models.appointments import Appointment
from models.pricing import Pricing

from utils.func import get_db, get_current_user, getTimeSlot, authenticate_user



# App and templates setup



app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_super_secret_key")
# templates = Jinja2Templates(directory="templates")

templates = Jinja2Templates(directory="templates")


app.mount("/static", StaticFiles(directory="static"), name="static")

# Create tables
Base.metadata.create_all(bind=engine)



@app.get("/")
def home(request: Request, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    services = db.query(Services).all()
    doctors = db.query(Doctor).all()

    return render_template(request, "home.html", {"request": request, "services": services, "doctors": doctors, "user": user})

@app.get("/services",response_class=HTMLResponse)
def services(request: Request, db: Session = Depends(get_db)):
    services = db.query(Services).all()
    return render_template(request, "services.html", {"services": services})

@app.get("/services")
def show_services(request: Request, db: Session = Depends(get_db)):
    services = db.query(Services).all()
    return render_template (request,"services.html", {
        "request": request,
        "services": services
    })

@app.get("/register")
def register_get(request: Request):
    return render_template(request,"register.html", {"request": request, "errors": None})


@app.get('/check-schedule/{doctor_id}')
def check_schedule(request: Request, doctor_id: int, db: Session = Depends(get_db)):
    user = request.session.get("user")
    location = request.session.get("location")
    clinic = db.query(Clinic).filter(Clinic.location == location).first()


    selected_date = request.query_params.get("date")
    if not selected_date:
        return JSONResponse({"message": "Date parameter is required."})

    schedules = db.query(Schedule).filter(
            Schedule.doctor_id == doctor_id,
            func.date(Schedule.date) == selected_date,
            Schedule.clinic_id == clinic.id,  # Assuming clinic_id is 1 for this example should be dynamic ... @todo
        ).first()
    

    if schedules:
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == schedules.doctor_id,
            Appointment.clinic_id == schedules.clinic_id,
            # func.date(Appointment.appointment_date) == selected_date
        ).all()
        schedules.appointments = appointments


    if not schedules:
        return JSONResponse({"message": "No schedules available for this doctor."})

    return JSONResponse({
        "doctor_id": doctor_id,
        "date": selected_date,
        "time_slot": schedules.time_slot,
        "is_available": schedules.is_available,
        "appointments": [
            {
                "id": appointment.id,
                "time": appointment.appointment_date.strftime("%H:%M"),
            } for appointment in schedules.appointments
        ] if schedules.appointments else []
    })

@app.get('/doctor/{doctor_id}')
def doctor_detail(request: Request, doctor_id: int, db: Session = Depends(get_db)):

    ## get location 
    location = request.session.get('location')
    
    clinic = db.query(Clinic).filter(Clinic.location == location).first()
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.clinic_id == clinic.id).first()

    if not doctor:
        return RedirectResponse('/')
    
    doctors = db.query(Doctor).all()
    services = db.query(Services).all()
    user = request.session.get("user")

    future_schedules = db.query(Schedule).filter(
        Schedule.doctor_id == doctor.id,
        Schedule.clinic_id == clinic.id,
        Schedule.date >= date.today()
    ).all()
    
    return render_template(request, "doctor_detail.html", {"request": request, "doctor": doctor, "doctors": doctors, "schedules": future_schedules, "services": services, "user": user})

@app.get('/find-a-doctor')
def find_a_doctor(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user") 
    location = request.session.get('location', "Male City")
    clinics = db.query(Clinic).filter(Clinic.location == location).first()
    doctors = db.query(Doctor).filter(Doctor.clinic_id == clinics.id).all()
    all_doctors = db.query(Doctor).filter(Doctor.clinic_id != clinics.id).all()
    return render_template(request, "find-a-doctor.html", {"request": request, "user": user, "clinics": clinics, "doctors": doctors, "all_doctors": all_doctors})

    

@app.post("/register")
def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    contact: str = Form(...),
    identifier: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.email == email).first()
    
    if existing_user:
        return render_template(request, "register.html", {"request": request, "errors": { "email": "This user is already registered, try login instead"} })
    
    hashed_password = bcrypt.hash(password)
    new_user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        contact=contact,
        identifier=identifier,
        role="CUSTOMER"
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

@app.get("/login")
def login_get(request: Request):
    return render_template(request, "login.html", {"request": request})

@app.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    authorisation = authenticate_user(db, email, password)
    if not authorisation:
        return render_template(request, "login.html", {"request": request, "error": "Invalid credentials"})
    
    user = db.query(User).filter(User.id == authorisation.id).first()



    request.session['user'] = {
        'id': user.id,
        'full_name': user.full_name,
        'email': user.email,
        'contact': user.contact,
        'identifier': user.identifier,
        'role': user.role,
        'clinic_id': 1,
        'doctor_id': user.doctor.id if user.doctor else None,
        'location': "Male CIty"
    }
    if user.role == "CUSTOMER":
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse("/admin", status_code=status.HTTP_302_FOUND)



@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")

@app.get("/check-pricing")
def check_pricing(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "User not logged in"}, status_code=status.HTTP_401_UNAUTHORIZED)
    
    time = request.query_params.get("time")
    date = request.query_params.get("date")
    service = request.query_params.get("service")

    ## set time slot depending on the time if its morning 0-12 morining and 12-16 afternoon and 16-22 evening
    if time >= "00:00" and time <= "12:00":
        time_slot = "morning"
    elif time >= "12:00" and time <= "16:00":
        time_slot = "afternoon"
    else:
        time_slot = "evening"

    pricing = db.query(Pricing).filter(
        Pricing.shift == time_slot,
        Pricing.service_id == service
    ).first()

    print(service,time_slot)

    if not pricing:
        return JSONResponse({"error": "Pricing not found"}, status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse({"price": pricing.price})
    
    



@app.post("/book-appointment")
async def book_appointment(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    location = request.session.get("location")

    clinic = db.query(Clinic).filter(Clinic.location == location).first()
    if not user:
        return JSONResponse({"error": "User not logged in"}, status_code=status.HTTP_401_UNAUTHORIZED)
    
    body = await request.json()
    service = body.get("service")
    date = body.get("date")
    time = body.get("time")
    doctor_id = body.get("doctor_id")

    ## get price from pricing table
    pricing = db.query(Pricing).filter(
        Pricing.service_id == service,
        Pricing.shift == getTimeSlot(time)
    ).first()



    if not pricing:
        return JSONResponse({"error": "Pricing not found"}, status_code=status.HTTP_404_NOT_FOUND)
    

    ## generate booking reference   
    booking_reference = f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
    ## convert date to sql format YYYY-MM-DD
    sql_date = datetime.strptime(f"{date} {time}", "%m/%d/%Y %H:%M")

    ## block any appointments that conflict with the new appointment also add max 10 appointments per doctor per date   

    appointments = db.query(Appointment).filter(Appointment.doctor_id == doctor_id, Appointment.appointment_date == sql_date).count()
    if appointments >= 10:
        return JSONResponse({"error": "Doctor has reached the maximum number of appointments"}, status_code=status.HTTP_400_BAD_REQUEST)
    
    conflicting_appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.clinic_id == user.get("clinic_id"),
        Appointment.appointment_date == sql_date,
        Appointment.clinic_id == clinic.id,

        Appointment.time_slot == getTimeSlot(time)
    ).all()

    if conflicting_appointments:
        return JSONResponse({"error": "there is already an appointment at this time"}, status_code=status.HTTP_400_BAD_REQUEST)

    new_appointment = Appointment(
        booking_reference=booking_reference,
        patient_id=user.get("id"),
        doctor_id=doctor_id,
        room_id=1,
        service_type=service,
        clinic_id=clinic.id,
        time_slot=getTimeSlot(time),
        appointment_date=sql_date,
        price=pricing.price,
        status="PENDING",
        created_at=datetime.now()
    )
    db.add(new_appointment)
    db.commit()

    return JSONResponse({
        "data": "Appointment booked successfully",
        "status": "success"
    })



@app.get("/about-us")
def about(request: Request):
    return render_template(request, "aboutus.html", {"request": request})


@app.get("/myaccount")
def myaccount(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    
    date = datetime.now()

    profile = db.query(User).filter(User.id == user.get("id")).first()
    appointments = db.query(Appointment).filter(Appointment.patient_id == user.get("id")).order_by(Appointment.id.desc()).all()

    return render_template(request, "myaccount.html", {"request": request, "user": user, "appointments": appointments, "profile": profile, "date": date})


app.include_router(api_router)
app.include_router(admin_router)