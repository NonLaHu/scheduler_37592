#!/usr/bin/env python3
import re
import os
import platform
from datetime import datetime, timedelta
import typer

app = typer.Typer()

DEBUG = False

file_path = '/home/empty/Projects/schedule/grid.txt'


def debug(msg):
    if DEBUG:
        typer.secho(f"[DEBUG] {msg}", fg=typer.colors.BRIGHT_BLACK)


def format_time(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"


def parse_duration_to_min(text):
    clean_text = text.split('#')[0]

    h = re.search(r'(\d+)h', clean_text)
    m = re.search(r'(\d+)m', clean_text)

    result = (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)

    debug(f"Duration parse: '{text}' -> {result} min")

    return result


def get_comment(text):
    if '#' in text:
        return text.split('#')[1].strip()
    return None


def get_priority_color(text):
    if "HIGHEST" in text: return typer.colors.MAGENTA
    if "HIGH" in text: return typer.colors.YELLOW
    if "LOW" in text: return typer.colors.BRIGHT_BLACK
    return typer.colors.WHITE


@app.command()
def edit():
    if not os.path.exists(file_path):
        typer.secho(f"Error: {file_path} not found.", fg=typer.colors.RED)
        return

    debug(f"Opening editor for {file_path}")

    if platform.system() == "Windows":
        os.system(f"notepad {file_path}")
    else:
        os.system(f"nano {file_path}")


@app.command()
def run(
    days: int = typer.Argument(1, help="Number of days to show"),
    debug_mode: bool = typer.Option(False, "--debug")
):

    global DEBUG
    DEBUG = debug_mode

    debug("Debug mode enabled")

    try:
        with open(file_path, 'r') as f:
            data = f.read()

    except FileNotFoundError:
        typer.secho(f"Error: {file_path} not found.", fg=typer.colors.RED)
        return


    availability = {
        "weekday": 270,
        "weekend": 510
    }

    base_date = datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    debug(f"Base date: {base_date}")

    habits = re.search(r'HABITS \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')
    recurring = re.search(r'RECURRING \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')
    tasks = re.search(r'TASKS \{(.*?)\}', data, re.DOTALL).group(1).strip().split('\n')


    filler_match = re.search(r'FILLER \{(.*?)\}', data, re.DOTALL)
    fillers = (
        [
            x.strip()
            for x in filler_match.group(1).split('\n')
            if x.strip()
        ]
        if filler_match
        else []
    )


    debug(f"Habits: {len(habits)}")
    debug(f"Recurring: {len(recurring)}")
    debug(f"Tasks: {len(tasks)}")
    debug(f"Fillers: {len(fillers)}")


    for i in range(days):

        current = base_date + timedelta(days=i)

        day_num = current.isoweekday()

        capacity = availability["weekend"] if day_num >= 6 else availability["weekday"]

        debug(f"Generating {current.date()} capacity={capacity}")


        daily_tasks = []
        total_used = 0


        for h in habits:
            dur = parse_duration_to_min(h)
            comment = get_comment(h)

            debug(f"Adding habit: {h}")

            daily_tasks.append((h, dur, comment))
            total_used += dur



        for r in recurring:

            match = re.search(r'\[DAYS: ([\d, ]+)\]', r)

            if match:

                allowed_days = [
                    d.strip()
                    for d in match.group(1).split(',')
                ]

                debug(f"Recurring check {r} days={allowed_days}")


                if str(day_num) in allowed_days:

                    dur = parse_duration_to_min(r)
                    comment = get_comment(r)

                    debug(f"Adding recurring: {r}")

                    daily_tasks.append((r, dur, comment))
                    total_used += dur



        for t in tasks:

            parts = [p.strip() for p in t.split(':')]

            debug(f"Checking task: {t}")


            if len(parts) < 2:
                continue


            try:
                t_date = datetime.strptime(parts[0], '%Y-%m-%d')


                if len(parts) > 3:

                    metadata_segment = (
                        parts[3] +
                        " " +
                        (parts[4] if len(parts) > 4 else "")
                    ).strip()


                    if metadata_segment == "P":
                        debug("Priority P detected, moving date back")
                        t_date -= timedelta(days=1)



                if t_date.date() == current.date():

                    dur = parse_duration_to_min(
                        parts[2] if len(parts) > 2 else "0m"
                    )

                    debug(f"Adding task {parts[1]} {dur}min")

                    daily_tasks.append(
                        (
                            parts[1],
                            dur,
                            get_comment(t)
                        )
                    )

                    total_used += dur


            except Exception as e:
                debug(f"Task parse failed: {e}")
                continue



        debug(f"Used before fillers: {total_used}/{capacity}")


        if total_used < capacity:

            remaining = capacity - total_used

            for f in fillers:

                if remaining <= 0:
                    break


                dur = parse_duration_to_min(f)

                if dur <= remaining:

                    debug(f"Adding filler {f}")

                    daily_tasks.append((f, dur, None))

                    total_used += dur
                    remaining -= dur



        daily_tasks.sort(key=lambda x: x[1])


        typer.secho(
            f"--- {current.strftime('%A, %Y-%m-%d')} (Day {day_num}) ---",
            fg=typer.colors.CYAN,
            bold=True
        )


        for line, dur, comment in daily_tasks:

            color = get_priority_color(line)

            raw_name = line.split(':')[0].strip()

            display_name = raw_name.replace('_', ' ').title()


            task_str = f"- {display_name}: {format_time(dur)}"

            if comment:
                task_str += f" | # {comment}"


            typer.secho(task_str, fg=color)



        diff = capacity - total_used

        status_color = (
            typer.colors.GREEN
            if diff >= 0
            else typer.colors.RED
        )


        status_text = (
            f"{format_time(abs(diff))} "
            f"{'FREE' if diff >= 0 else 'OVERLOADED'}"
        )


        typer.secho(
            f"\nTotal: {format_time(total_used)} / Capacity: {format_time(capacity)} -> {status_text}",
            fg=status_color,
            bold=True
        )

        typer.echo("")


if __name__ == "__main__":
    app()
