from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import status
from sqlalchemy.orm import Session
from database import SessionLocal
from models.appointments import Appointment
from models.doctors import Doctor
from passlib.hash import bcrypt
from datetime import datetime
from models.clinics import Clinic
from models.bookings import Booking
from models.room import Room
from models.schedule import Schedule
from models.user import User
from utils.func import get_db, requires_roles, ADMIN, MANAGER, CUSTOMER
api_router = APIRouter()

# Add /api routes here 
@api_router.get("/api/appointments/{appointment_id}")
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

@api_router.get('/api/clinics')
def get_clinics(request: Request, db: Session = Depends(get_db)):
    clinics = db.query(Clinic).all()
    return JSONResponse([{"id": clinic.id, "name": clinic.location} for clinic in clinics])


@api_router.post("/api/setlocation")
async def set_location(request: Request, db: Session = Depends(get_db)):
    location = request.session.get("location")
        
    body = await request.json()
    clinic_id = body.get("clinic_id")
    location = body.get("location")

    if not clinic_id:
        return JSONResponse({"error": "Clinic ID is required"}, status_code=status.HTTP_400_BAD_REQUEST)
    
    request.session['location'] = location
    
    return JSONResponse({"message": "Location updated successfully", "clinic_id": clinic_id})


###  DOCTOR ROUTES
@api_router.get("/api/doctors/{doctor_id}")
async def get_doctor(doctor_id: int, request: Request, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        return JSONResponse({"error": "Doctor not found"}, status_code=status.HTTP_404_NOT_FOUND)
    return doctor

@api_router.post("/api/doctors/add")
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


@api_router.delete("/api/doctors/{doctor_id}")
async def delete_doctor(doctor_id: int, request: Request, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        return JSONResponse({"error": "Doctor not found"}, status_code=status.HTTP_404_NOT_FOUND)
    db.delete(doctor)
    db.commit()
    return JSONResponse({"message": "Doctor deleted successfully"})


@api_router.put("/api/doctor/{doctor_id}")
async def update_doctor(doctor_id: int, request: Request, db: Session = Depends(get_db)):
    data = await request.json()


    ## if user role is admin or manager
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "User not logged in"}, status_code=status.HTTP_401_UNAUTHORIZED)
    
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        return JSONResponse({"error": "Doctor not found"}, status_code=status.HTTP_404_NOT_FOUND)


    if user['role'] != 'ADMIN' and user['role'] != 'MANAGER' and user['id'] != doctor.user_id:
        return JSONResponse({"error": "You are not authorized to update this doctor"}, status_code=status.HTTP_403_FORBIDDEN)
    doctor.full_name = data.get("name")
    doctor.speciality = data.get("speciality")
    doctor.experience = data.get("experience")
    doctor.clinic_id = data.get("clinic_id")
    db.commit()
    return JSONResponse({"message": "Doctor updated successfully"})


## USER ROUTES
@requires_roles(ADMIN, MANAGER, CUSTOMER)
@api_router.put("/api/users/{user_id}")
async def update_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    
    session_user = db.query(User).filter(User.id == user_id).first()    
    session_user.full_name = data.get("full_name")
    session_user.email = data.get("email")
    session_user.contact = data.get("contact")
    session_user.identifier = data.get("identifier")

    db.commit()

    if data.get("user_id"):
        doctor_id = data.get("user_id")
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        doctor.user_id = session_user.id
        db.commit()

    return JSONResponse({"message": "User updated successfully"})

@api_router.delete("/api/users/{user_id}")
async def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "User not logged in"}, status_code=status.HTTP_401_UNAUTHORIZED)
    if user['role'] != 'ADMIN':
        return JSONResponse({"error": "You are not authorized to delete this user"}, status_code=status.HTTP_403_FORBIDDEN)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=status.HTTP_404_NOT_FOUND)
    db.delete(user)
    db.commit()
    return JSONResponse({"message": "User deleted successfully"})
    
### API ROUTES
@api_router.post("/api/appointments/{appointment_id}")
async def confirm_appointment(appointment_id: int, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    status = data.get("status")
    requires_surgery = data.get("requires_surgery")
    requires_admission = data.get("requires_admission")

    if not status:
        return JSONResponse(
            {"error": "Status is required"}, 
            status_code=status.HTTP_400_BAD_REQUEST
        )
        
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        return JSONResponse(
            {"error": "Appointment not found"}, 
            status_code=status.HTTP_404_NOT_FOUND
        )
        
    appointment.status = status
    db.commit()

    # Handle room booking
    booking_date = appointment.appointment_date.strftime("%Y-%m-%d")
    
    # Get existing bookings for the day
    bookings = db.query(Booking).filter(Booking.booking_date == booking_date).all()
    
    # Get room counts by type
    room_counts = {
        "surgery": sum(1 for b in bookings if db.query(Room).get(b.room_id).room_type == "surgery" and b.clinic_id == appointment.clinic_id),
        "regular": sum(1 for b in bookings if db.query(Room).get(b.room_id).room_type == "regular" and b.clinic_id == appointment.clinic_id)
    }

    # Determine required room type and validate availability
    room_type = "surgery" if requires_surgery else "regular"
    max_rooms = 1 if room_type == "surgery" else 2
    
    if room_counts[room_type] >= max_rooms:
        error_msg = f"{'Surgery' if room_type == 'surgery' else 'Regular'} room{'s' if max_rooms > 1 else ''} already fully booked for the day"
        return JSONResponse({"error": error_msg}, status_code=400)

    # Find available room
    available_room = db.query(Room).filter(
        Room.room_type == room_type,
        Room.id.notin_([b.room_id for b in bookings])
    ).first()

    if not available_room:
        return JSONResponse(
            {"error": f"No {room_type} rooms available"}, 
            status_code=400
        )

    # Create new booking
    new_booking = Booking(
        room_id=available_room.id,
        clinic_id=appointment.clinic_id,
        booking_date=booking_date,
        patient_id=appointment.patient_id
    )
    db.add(new_booking)
    db.commit()

    return JSONResponse({"message": "Appointment status updated successfully"})

@api_router.post("/api/appointments/cancel/{appointment_id}")
async def cancel_appointment(appointment_id: int, request: Request, db: Session = Depends(get_db)):

    user = request.session.get("user")
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not appointment:
        return JSONResponse({"error": "Appointment not found"}, status_code=status.HTTP_404_NOT_FOUND)

    if not user:
        return JSONResponse({"error": "User not logged in"}, status_code=status.HTTP_401_UNAUTHORIZED)
    if user['id'] != appointment.patient_id:
        return JSONResponse({"error": "You are not authorized to cancel this appointment"}, status_code=status.HTTP_403_FORBIDDEN)

    if appointment.status == "CANCELLED":
        return JSONResponse({"error": "Appointment already cancelled"}, status_code=status.HTTP_400_BAD_REQUEST)
    
    appointment.status = "CANCELLED"
    db.commit()
    return JSONResponse({"message": "Appointment cancelled successfully"})

@api_router.post("/api/schedule")
async def save_schedule(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    if user['role'] != 'MANAGER' and user['role'] != 'ADMIN' and user['role'] != 'DOCTOR':
        return JSONResponse({"error": "You are not authorized to save this schedule"}, status_code=status.HTTP_403_FORBIDDEN)
    
    data = await request.json()
    date = data.get("date")
    doctor_id = data.get("doctor_id")
    shift = data.get("shift")
    clinic_id = data.get("clinic_id")

    # If doctor_id is empty or not passed, delete the schedule
    if not doctor_id:
        existing_schedule = db.query(Schedule).filter(
            Schedule.date == date,
            Schedule.clinic_id == clinic_id
        ).first()
        if existing_schedule:
            db.delete(existing_schedule)
            db.commit()
            return JSONResponse({"message": "Schedule cleared successfully"})
        return JSONResponse({"message": "No schedule found to clear"})

    ## lets add one more validation if its adding current date make sure the shift is already not passed lets say morning, afternoon, evening is not passed
    current_date = datetime.now()
    current_time = current_date.time()
    current_date = current_date.strftime("%Y-%m-%d")

    if date == current_date:
        # Check if shift has already passed
        if shift == "MORNING" and current_time.hour >= 12:
            return JSONResponse({"error": "Morning shift has already passed"}, status_code=status.HTTP_400_BAD_REQUEST)
        elif shift == "AFTERNOON" and current_time.hour >= 17:
            return JSONResponse({"error": "Afternoon shift has already passed"}, status_code=status.HTTP_400_BAD_REQUEST) 
        elif shift == "EVENING" and current_time.hour >= 22:
            return JSONResponse({"error": "Evening shift has already passed"}, status_code=status.HTTP_400_BAD_REQUEST)
    
    ## check if the schedule already exists
    existing_schedule = db.query(Schedule).filter(Schedule.date == date, Schedule.doctor_id == doctor_id, Schedule.clinic_id == clinic_id).first()
    if existing_schedule:
        return JSONResponse({"message": "Schedule modified successfully"})
    
    new_schedule = Schedule(
        date=date,
        doctor_id=doctor_id,
        clinic_id=clinic_id,
        time_slot=shift
    )
    db.add(new_schedule)
    db.commit()
    return JSONResponse({"message": "Schedule saved successfully"})

@api_router.get("/api/schedule")
async def get_schedule(request: Request, start: str, end: str, clinic_id: int, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.date >= start, Schedule.date <= end, Schedule.clinic_id == clinic_id).all()
    return schedule


@api_router.post("/api/users")
async def add_user(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    ## user has to be admin
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "User not logged in"}, status_code=status.HTTP_401_UNAUTHORIZED)
    if user['role'] != 'ADMIN':
        return JSONResponse({"error": "You are not authorized to add this user"}, status_code=status.HTTP_403_FORBIDDEN)

    user = User(
        full_name=data.get("full_name"),
        email=data.get("email"),
        contact=data.get("contact"),
        identifier=data.get("identifier"),
        role=data.get("role"),
        hashed_password=bcrypt.hash(data.get("password"))
    )

    if data.get("user_id"):
        doctor_id = data.get("user_id")
        ## update doctor add user_id to doctor
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        doctor.user_id = user.id
        db.commit()

    db.add(user)
    db.commit() 
    return JSONResponse({"message": "User added successfully"})


@api_router.post("/api/clinics/add")
async def add_clinic(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    
    if user['role'] != 'ADMIN':
        return JSONResponse({"error": "You are not authorized to add this clinic"}, status_code=status.HTTP_403_FORBIDDEN)   
    
    data = await request.form()
    clinic_name = data.get("clinic_name")
    clinic_location = data.get("clinic_location")

    clinic = Clinic(
        name=clinic_name,
        location=clinic_location,
        is_active=data.get("is_active")
    )

    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    
    return JSONResponse({"message": "Clinic added successfully"})

@api_router.put("/api/clinics/{clinic_id}/update")
async def update_clinic(clinic_id: int, request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "User not logged in"}, status_code=status.HTTP_401_UNAUTHORIZED)
    
    if user['role'] != 'ADMIN':
        return JSONResponse({"error": "You are not authorized to update this clinic"}, status_code=status.HTTP_403_FORBIDDEN)

    data = await request.json()
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        return JSONResponse({"error": "Clinic not found"}, status_code=status.HTTP_404_NOT_FOUND)

    clinic.name = data.get("clinic_name")
    clinic.location = data.get("clinic_location")
    clinic.is_active = data.get("is_active")
    
    db.commit()
    return JSONResponse({"message": "Clinic updated successfully"})
