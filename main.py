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


def parse_time(time_str):
    if not time_str or "0m" in time_str: return 0
    minutes = 0
    h_match = re.search(r'(\d+)h', time_str)
    m_match = re.search(r'(\d+)m', time_str)
    if h_match: minutes += int(h_match.group(1)) * 60
    if m_match: minutes += int(m_match.group(1))
    return minutes

def get_schedule(data, days_to_show=1):
    # Setup Availability
    # Weekday (1-5): 19:00-23:30 | Weekend (6-7): 08:00-00:00 & 19:00-23:30
    availability = {
        "weekday": (19, 23.5),
        "weekend": [(8, 24), (19, 23.5)]
    }

    base_date = datetime.strptime(re.search(r'DATE: (\d{4}-\d{2}-\d{2})', data).group(1), '%Y-%m-%d')
    habits = re.search(r'HABITS \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')
    recurring = re.search(r'RECURRING \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')
    tasks = re.search(r'TASKS \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')

    for i in range(days_to_show):
        current = base_date + timedelta(days=i)
        day_num = current.isoweekday()
        is_weekend = day_num >= 6

        # Determine time slots
        slots = availability["weekend"] if is_weekend else [availability["weekday"]]
        slot_str = " | ".join([f"{s[0]:02d}:00 to {int(s[1]):02d}:{int((s[1]%1)*60):02d}" for s in slots])

        print(f"\n--- {current.strftime('%A, %Y-%m-%d')} (Day {day_num}) ---")
        print(f"AVAILABLE HOURS: {slot_str}")

        print("[HABITS]")
        for h in habits: print(f"  * {h.strip()}")

        print("[RECURRING]")
        for r in recurring:
            days_match = re.search(r'\[DAYS: ([\d, ]+)\]', r)
            if days_match and str(day_num) in [d.strip() for d in days_match.group(1).split(',')]:
                print(f"  * {r.split(':')[0].strip()}")

        print("[TASKS]")
        for t in tasks:
            parts = t.split(':')
            t_date = datetime.strptime(parts[0].strip(), '%Y-%m-%d')
            is_prep = ": P" in t
            if is_prep: t_date -= timedelta(days=1)

            if t_date.date() == current.date():
                print(f"  * {parts[1].strip()}")

# Usage
get_schedule(grid_data, days_to_show=7)
