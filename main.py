import re
from datetime import datetime, timedelta
import typer

app = typer.Typer()

def format_time(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

def parse_duration_to_min(text):
    h = re.search(r'(\d+)h', text)
    m = re.search(r'(\d+)m', text)
    return (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)

def get_priority_color(text):
    if "HIGHEST" in text: return typer.colors.MAGENTA
    if "HIGH" in text: return typer.colors.YELLOW
    if "LOW" in text: return typer.colors.BRIGHT_BLACK
    return typer.colors.WHITE

@app.command()
def run(days: int = typer.Argument(1, help="Number of days to show")):
    file_path = 'grid.txt'
    try:
        with open(file_path, 'r') as f:
            data = f.read()
    except FileNotFoundError:
        typer.secho(f"Error: {file_path} not found.", fg=typer.colors.RED)
        return

    availability = {"weekday": 270, "weekend": 510}
    base_date = datetime.strptime(re.search(r'DATE: (\d{4}-\d{2}-\d{2})', data).group(1), '%Y-%m-%d')

    habits = re.search(r'HABITS \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')
    recurring = re.search(r'RECURRING \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')
    tasks = re.search(r'TASKS \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')

    for i in range(days):
        current = base_date + timedelta(days=i)
        day_num = current.isoweekday()
        capacity = availability["weekend"] if day_num >= 6 else availability["weekday"]

        daily_tasks = []
        total_used = 0

        # Collection Logic (Adding priority string for coloring)
        for h in habits:
            dur = parse_duration_to_min(h)
            daily_tasks.append((h, dur)) # Keep full line for priority detection
            total_used += dur

        for r in recurring:
            match = re.search(r'\[DAYS: ([\d, ]+)\]', r)
            if match and str(day_num) in [d.strip() for d in match.group(1).split(',')]:
                dur = parse_duration_to_min(r)
                daily_tasks.append((r, dur))
                total_used += dur

        for t in tasks:
            parts = [p.strip() for p in t.split(':')]
            if len(parts) < 2: continue
            t_date = datetime.strptime(parts[0], '%Y-%m-%d')
            if ": P" in t: t_date -= timedelta(days=1)
            if t_date.date() == current.date():
                dur = parse_duration_to_min(parts[2] if len(parts) > 2 else "0m")
                daily_tasks.append((parts[1], dur))
                total_used += dur

        daily_tasks.sort(key=lambda x: x[1])

        # Output
        typer.secho(f"--- {current.strftime('%A, %Y-%m-%d')} (Day {day_num}) ---", fg=typer.colors.CYAN, bold=True)
        for line, dur in daily_tasks:
            color = get_priority_color(line)
            # Clean up task name for display
            display_name = line.split(':')[0].strip()
            typer.secho(f"- {display_name}: {format_time(dur)}", fg=color)

        # Status
        diff = capacity - total_used
        status_color = typer.colors.GREEN if diff >= 0 else typer.colors.RED
        status_text = f"{format_time(abs(diff))} {'FREE' if diff >= 0 else 'OVERLOADED'}"

        typer.secho(f"Total: {format_time(total_used)} / Capacity: {format_time(capacity)} -> {status_text}", fg=status_color, bold=True)
        typer.echo("")

if __name__ == "__main__":
    app()
