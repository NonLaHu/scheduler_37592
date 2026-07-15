import re
from datetime import datetime, timedelta

# Input data
grid_data = """
GRID {
DATE: 2026-07-16
DAY: 4
HABITS {
ENGLISH: 20m
CHINESE: 10m [PRIORITY: LOW]
MONEY_LOGGING: 5m
CTF: 1h [PRIORITY: HIGH]
PYTHON_OPENCV: 2h [PRIORITY: HIGHEST]
}
RECURRING {
EXAM_TRACKING: [DAYS: 7] 0h
MANUAL_EDITING: [DAYS: 2,4,7] 1h 30m
CALL_MOM: [DAYS: 1,3,5,6] 1h
}
TASKS {
2026-07-16: SYNCTHING : 30m
2026-07-17: WEBSITE_MEETING : 0m
2026-07-17: SUDO_PACMAN_UPDATE_VPN : 20m
2026-07-20: MATH_TUTO : 20m : P
2026-07-23: UML_TUTO : 50m : P
}
}
"""


def parse_duration_to_min(text):
    """Extracts total minutes from strings like '1h 30m' or '20m'."""
    h = re.search(r'(\d+)h', text)
    m = re.search(r'(\d+)m', text)
    total = (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)
    return total

def get_schedule(data, days_to_show=1):
    availability = {
        "weekday": (19, 23.5), # 4.5 hours = 270 mins
        "weekend": [(8, 12), (19, 23.5)] # 4 hours + 4.5 hours = 510 mins
    }

    # Pre-parse sections
    habits = re.search(r'HABITS \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')
    recurring = re.search(r'RECURRING \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')
    tasks = re.search(r'TASKS \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')

    base_date = datetime.strptime(re.search(r'DATE: (\d{4}-\d{2}-\d{2})', data).group(1), '%Y-%m-%d')

    for i in range(days_to_show):
        current = base_date + timedelta(days=i)
        day_num = current.isoweekday()
        is_weekend = day_num >= 6

        # Calculate Capacity in Minutes
        if is_weekend:
            total_capacity = ((12-8) * 60) + ((23.5-19) * 60)
        else:
            total_capacity = (23.5-19) * 60

        daily_tasks = []
        total_used = 0

        # 1. Collect Habits
        for h in habits:
            dur = parse_duration_to_min(h)
            daily_tasks.append((h.split(':')[0].strip(), dur))
            total_used += dur

        # 2. Collect Recurring
        for r in recurring:
            days_match = re.search(r'\[DAYS: ([\d, ]+)\]', r)
            if days_match and str(day_num) in [d.strip() for d in days_match.group(1).split(',')]:
                dur = parse_duration_to_min(r)
                daily_tasks.append((r.split(':')[0].strip(), dur))
                total_used += dur

        # 3. Collect Tasks
        for t in tasks:
            parts = [p.strip() for p in t.split(':')]
            t_date = datetime.strptime(parts[0], '%Y-%m-%d')
            if ": P" in t: t_date -= timedelta(days=1)

            if t_date.date() == current.date():
                dur = parse_duration_to_min(parts[2] if len(parts) > 2 else "0m")
                daily_tasks.append((parts[1], dur))
                total_used += dur

        # Output
        print(f"--- {current.strftime('%A, %Y-%m-%d')} (Day {day_num}) ---")
        for task, dur in daily_tasks:
            print(f"- {task}: {dur}m")

        status = "OK" if total_used <= total_capacity else "OVERLOADED"
        print(f"Total: {total_used}m / Capacity: {int(total_capacity)}m -> {status}\n")

get_schedule(grid_data, days_to_show=7)
