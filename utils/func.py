from datetime import datetime, timedelta
from fastapi import Request
from fastapi.templating import Jinja2Templates
from database import SessionLocal
from models.user import User
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from functools import wraps
from fastapi import status
from fastapi.responses import JSONResponse
import inspect


# Role constants
ADMIN = "ADMIN"
MANAGER = "MANAGER"
OFFICER = "OFFICER"
DOCTOR = "DOCTOR"
CUSTOMER = "CUSTOMER"

templates = Jinja2Templates(directory="templates")

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

def get_upcoming_dates(target_days):
    today = datetime.today()
    weekday_to_int = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Saturday": 5,
        "Sunday": 6,
    }

    dates = []
    for day_name in target_days:
        target_weekday = weekday_to_int[day_name]
        days_ahead = (target_weekday - today.weekday()) % 7
        day_date = today + timedelta(days=days_ahead)
        dates.append({
            "name": day_name,
            "date": day_date.strftime("%Y-%m-%d")
        })

    return dates

target_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"]
week_dates = get_upcoming_dates(target_days)



def render_template(request: Request, template_name: str, context: dict = None):
    context = context.copy() if context else {}
    context["request"] = request
    context["user"] = request.session.get("user")
    location = request.session.get("location", "Male City")  # Set default location to "Male City"
    request.session["location"] = location
    context["location"] = location
    return templates.TemplateResponse(template_name, context)



def requires_roles(*allowed_roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, db, *args, **kwargs):
            user_data = request.session.get("user")
            if not user_data:
                return JSONResponse(
                    {"error": "Not authenticated"},
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            session_user = db.query(User).filter(User.id == user_data["id"]).first()
            if not session_user or session_user.role not in allowed_roles:
                return JSONResponse(
                    {"error": "You are not authorized to perform this action"},
                    status_code=status.HTTP_403_FORBIDDEN
                )

            # Check if func is coroutine or not
            if inspect.iscoroutinefunction(func):
                return await func(request, db, *args, **kwargs)
            else:
                return func(request, db, *args, **kwargs)

        return wrapper
    return decorator