import datetime


def format_timedelta(delta: datetime.timedelta) -> str:
    sign = "просрочено на " if delta.total_seconds() < 0 else "еще "
    total_seconds = abs(int(delta.total_seconds()))

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    parts = []

    if days:
        parts.append(f"{days}д")
    if hours:
        parts.append(f"{hours}ч")
    if minutes:
        parts.append(f"{minutes}мин")

    return sign + " ".join(parts or ["0мин"])