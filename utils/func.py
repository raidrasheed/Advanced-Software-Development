from datetime import datetime, timedelta
from fastapi import Request
from fastapi.templating import Jinja2Templates
from database import SessionLocal
from models.user import User
from sqlalchemy.orm import Session
from passlib.hash import bcrypt


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


