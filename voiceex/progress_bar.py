from rich.progress import Progress, MofNCompleteColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from typing import Optional
from colorama import deinit

deinit()
progress = Progress(TextColumn("[progress.description]{task.description}"),
                    BarColumn(complete_style="#F92672", finished_style="green", pulse_style="yellow"),
                    MofNCompleteColumn(), TaskProgressColumn(), TimeRemainingColumn())

def track(sequence, description: str = "Working...", total: Optional[float] = None, update_period: float = 0.1,
    is_sub_track=False, sub_remove_end=False):
    if progress.live.console._live:
        is_sub_track = True
    if not sequence:
        return sequence

    if not is_sub_track:
        with progress:
            yield from progress.track(sequence, total=total, description=description, update_period=update_period)
    else:
        task = progress.add_task(description=description, total=total or len(sequence))
        for i in sequence:
            progress.update(task, advance=1)
            yield i
        if sub_remove_end:
            progress.remove_task(task)
