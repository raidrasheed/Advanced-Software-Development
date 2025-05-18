from datetime import datetime, timedelta



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