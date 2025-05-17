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
from models.room import Room



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


def render_template(request: Request, template_name: str, context: dict = None):
    context = context.copy() if context else {}
    context["request"] = request
    context["user"] = request.session.get("user")
    return templates.TemplateResponse(template_name, context)
# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def getTimeSlot(time: str):
    if time >= "00:00" and time <= "12:00":
        return "morning"
    elif time >= "12:00" and time <= "16:00":
        return "afternoon"
    else:
        return "evening"
# Auth logic
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if user and bcrypt.verify(password, user.hashed_password):
        return user
    return None


# templates = Jinja2Templates(directory="templates")
def get_current_user(request: Request):
    return request.session.get("user")





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


    selected_date = request.query_params.get("date")
    if not selected_date:
        return JSONResponse({"message": "Date parameter is required."})

    schedules = db.query(Schedule).filter(
            Schedule.doctor_id == doctor_id,
            func.date(Schedule.date) == selected_date,
            Schedule.clinic_id == user.get("clinic_id"),  # Assuming clinic_id is 1 for this example should be dynamic ... @todo
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
    
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    doctors = db.query(Doctor).all()
    services = db.query(Services).all()
    user = request.session.get("user")

    future_schedules = db.query(Schedule).filter(
        Schedule.doctor_id == doctor.id,
        Schedule.date >= date.today()
    ).all()
    
    return render_template(request, "doctor_detail.html", {"request": request, "doctor": doctor, "doctors": doctors, "schedules": future_schedules, "services": services, "user": user})

@app.get('/find-a-doctor')
def find_a_doctor(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user") 
    clinics = db.query(Clinic).all()
    doctors = db.query(Doctor).all()
    return render_template(request, "find-a-doctor.html", {"request": request, "user": user, "clinics": clinics, "doctors": doctors})



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
    user = authenticate_user(db, email, password)
    if not user:
        return render_template(request, "login.html", {"request": request, "error": "Invalid credentials"})
    request.session['user'] = {
        'id': user.id,
        'full_name': user.full_name,
        'email': user.email,
        'contact': user.contact,
        'identifier': user.identifier,
        'role': user.role,
        'clinic_id': 1,
        'location': "Male CIty"
    }
    if user.role == "CUSTOMER":
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse("/admin", status_code=status.HTTP_302_FOUND)


@app.get('/api/clinics')
def get_clinics(request: Request, db: Session = Depends(get_db)):
    clinics = db.query(Clinic).all()
    return JSONResponse([{"id": clinic.id, "name": clinic.location} for clinic in clinics])

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

    ## lets set time slot depending on the time if its morning 0-12 morining and 12-16 afternoon and 16-22 evening
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
    
    

@app.post("/api/setlocation")
async def set_location(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "User not logged in"}, status_code=status.HTTP_401_UNAUTHORIZED)
    
    body = await request.json()
    clinic_id = body.get("clinic_id")
    location = body.get("location")

    if not clinic_id:
        return JSONResponse({"error": "Clinic ID is required"}, status_code=status.HTTP_400_BAD_REQUEST)
    
    user['clinic_id'] = clinic_id
    user['location'] = location
    request.session['user'] = user
    
    return JSONResponse({"message": "Location updated successfully", "clinic_id": clinic_id})

@app.post("/book-appointment")
async def book_appointment(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "User not logged in"}, status_code=status.HTTP_401_UNAUTHORIZED)
    
    body = await request.json()
    service = body.get("service")
    date = body.get("date")
    time = body.get("time")
    doctor_id = body.get("doctor_id")

    print(service, date, time, doctor_id)

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

    ## block any appointments that conflict with the new appointment
    conflicting_appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.clinic_id == user.get("clinic_id"),
        Appointment.appointment_date == sql_date,
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
        clinic_id=user.get("clinic_id"),
        time_slot=getTimeSlot(time),
        appointment_date=sql_date,
        price=pricing.price,
        status="pending",
        created_at=datetime.now()
    )
    db.add(new_appointment)
    db.commit()
    return JSONResponse({
        "data": "Appointment booked successfully",
        "status": "success"
    })



@app.get("/api/appointments/{appointment_id}")
async def get_appointment(appointment_id: int, request: Request, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        return JSONResponse({"error": "Appointment not found"}, status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse({
        "id": appointment.id,
        "booking_reference": appointment.booking_reference,
        "service_type": appointment.service_type.value,
        "patient_name": appointment.patient.full_name,
        "appointment_date": appointment.appointment_date.strftime("%Y-%m-%d"),
        "time_slot": appointment.time_slot.value,
        "clinic": appointment.clinic.location,
        "doctor": appointment.doctor.full_name,
        "price": appointment.price,
        "status": appointment.status,
        "time": appointment.appointment_date.strftime("%H:%M")
    })


@app.put("/update-doctor/{doctor_id}")
async def update_doctor(doctor_id: int, request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    ## if user role is admin or manager
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "User not logged in"}, status_code=status.HTTP_401_UNAUTHORIZED)
    if user['role'] != 'ADMIN' and user['role'] != 'MANAGER':
        return JSONResponse({"error": "You are not authorized to update this doctor"}, status_code=status.HTTP_403_FORBIDDEN)
    
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        return JSONResponse({"error": "Doctor not found"}, status_code=status.HTTP_404_NOT_FOUND)
    doctor.full_name = data.get("name")
    doctor.speciality = data.get("speciality")
    doctor.experience = data.get("experience")
    doctor.clinic_id = data.get("clinic_id")
    db.commit()
    return JSONResponse({"message": "Doctor updated successfully"})


@app.get("/api/doctors/{doctor_id}")
async def get_doctor(doctor_id: int, request: Request, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        return JSONResponse({"error": "Doctor not found"}, status_code=status.HTTP_404_NOT_FOUND)
    return doctor

@app.post("/api/doctors/add")
async def add_doctor(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "User not logged in"}, status_code=status.HTTP_401_UNAUTHORIZED)
    if user['role'] != 'ADMIN' and user['role'] != 'MANAGER':
        return JSONResponse({"error": "You are not authorized to add this doctor"}, status_code=status.HTTP_403_FORBIDDEN)
    
    data = await request.json()
    name = data.get("name")
    speciality = data.get("speciality")
    experience = data.get("experience")
    clinic_id = data.get("clinic_id")

    new_doctor = Doctor(
        full_name=name,
        speciality=speciality,
        experience=experience,
        clinic_id=clinic_id
    )
    db.add(new_doctor)
    db.commit() 
    db.refresh(new_doctor)
    return JSONResponse({"message": "Doctor added successfully", "doctor": new_doctor})


@app.delete("/api/doctors/{doctor_id}")
async def delete_doctor(doctor_id: int, request: Request, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        return JSONResponse({"error": "Doctor not found"}, status_code=status.HTTP_404_NOT_FOUND)
    db.delete(doctor)
    db.commit()
    return JSONResponse({"message": "Doctor deleted successfully"})


@app.get("/about-us")
def about(request: Request):
    return render_template(request, "aboutus.html", {"request": request})

### ALL ADMIN ROUTES

@app.get("/admin")
def dashboard(request: Request):
    user = request.session.get("user") 
    # if user and user['role'] == 'CUSTOMER':
    #     return RedirectResponse("/")
    # if not user:
    #     return RedirectResponse("/login")
    return render_template(request, "admin/dashboard.html", {"request": request, "user": user})

@app.get("/admin/doctors")
def doctors(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user") 
    doctors = db.query(Doctor).all()
    clinics = db.query(Clinic).all()
    if not user:
        return RedirectResponse("/login")
    return render_template(request, "admin/doctors.html", {"request": request, "user": user, "doctors": doctors, "clinics": clinics})


@app.get("/admin/appointments")
def appointments(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")

    if not user:
        return RedirectResponse("/login")
    
    if user and user['role'] == 'CUSTOMER':
        appointments = db.query(Appointment).filter(
        Appointment.patient_id == user.get("id")
    ).all()
    elif user and user['role'] == 'ADMIN':
        appointments = db.query(Appointment).all()
    
    
    return render_template(request, "admin/appointments.html", {"request": request, "user": user, "appointments": appointments})    

@app.get("/admin/rooms")
def rooms(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    # Query rooms and join with clinics to group by clinic
    clinics_with_rooms = db.query(Clinic).join(Clinic.rooms).all()

    return render_template(request, "admin/rooms.html", {"request": request, "user": user, "clinics": clinics_with_rooms})


### API ROUTES
@app.post("/api/appointments/{appointment_id}")
async def confirm_appointment(appointment_id: int, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    status = data.get("status")
    if not status:
        return JSONResponse({"error": "Status is required"}, status_code=status.HTTP_400_BAD_REQUEST)
        
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        return JSONResponse({"error": "Appointment not found"}, status_code=status.HTTP_404_NOT_FOUND)
        
    appointment.status = status
    db.commit()
    return JSONResponse({"message": "Appointment status updated successfully"})

