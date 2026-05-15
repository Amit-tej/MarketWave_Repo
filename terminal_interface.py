import datetime
from utils import get_logger

logger = get_logger('terminal_interface')

SPARK_CHARS = ['▁','▂','▃','▄','▅','▆','▇','█']

def _have_rich():
    try:
        import rich
        return True
    except Exception:
        return False

def choose_from_list(prompt, options):
    """Prompt user to choose from options (returns selected option)."""
    if not options:
        raise ValueError('No options to choose from')
    if _have_rich():
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table(show_header=True, header_style='bold magenta')
        table.add_column('#', style='dim')
        table.add_column('Option')
        for i,opt in enumerate(options, start=1):
            table.add_row(str(i), str(opt))
        console.print(table)
        console.print(f'[bold] {prompt} [/bold]')
        choice = console.input('Enter number> ')
    else:
        print('Options:')
        for i,opt in enumerate(options, start=1):
            print(f'{i}. {opt}')
        choice = input(prompt + ' (enter number): ')
    try:
        idx = int(choice.strip()) - 1
        if idx < 0 or idx >= len(options):
            raise ValueError()
    except Exception:
        print('Invalid selection, defaulting to first option.')
        idx = 0
    return options[idx]

def show_calendar(start_date=None, horizon=30):
    start = start_date or datetime.date.today()
    days = [start + datetime.timedelta(days=i) for i in range(horizon)]
    # group by week
    weeks = []
    week = []
    for d in days:
        week.append(d)
        if d.weekday() == 6:
            weeks.append(week)
            week = []
    if week:
        weeks.append(week)

    lines = []
    for w in weeks:
        line = ' | '.join(d.strftime('%a %d-%b') for d in w)
        lines.append(line)

    if _have_rich():
        from rich.console import Console
        console = Console()
        console.print('[bold underline]30-day Calendar[/bold underline]')
        for l in lines:
            console.print(l)
    else:
        print('30-day Calendar')
        for l in lines:
            print(l)

def ascii_sparkline(values, width=40):
    import math
    vals = list(values)
    if not vals:
        return ''
    n = len(vals)
    if n > width:
        # downsample
        step = n / width
        sampled = []
        for i in range(width):
            idx = int(i*step)
            sampled.append(vals[idx])
        vals = sampled
        n = len(vals)
    # Convert values to floats when possible and treat None/NaN as missing
    def _to_float(x):
        try:
            if x is None:
                return float('nan')
            return float(x)
        except Exception:
            return float('nan')

    vals_f = [_to_float(v) for v in vals]
    valid = [v for v in vals_f if not math.isnan(v)]
    if not valid:
        # no valid numeric values -> return a blank/gap string of same length
        return ' ' * len(vals_f)

    mn = min(valid)
    mx = max(valid)
    rng = mx - mn if mx != mn else 1.0

    out_chars = []
    for v in vals_f:
        if math.isnan(v):
            out_chars.append(' ')
            continue
        # normalize and map to spark char, clip index boundaries
        idx = int((v - mn) / rng * (len(SPARK_CHARS) - 1))
        idx = max(0, min(len(SPARK_CHARS) - 1, idx))
        out_chars.append(SPARK_CHARS[idx])

    return ''.join(out_chars)

def display_ranked_markets(df_rows):
    """df_rows: iterable of dict with keys market_name, modal, volatility, category"""
    if _have_rich():
        from rich.console import Console
        from rich.table import Table
        from rich.style import Style
        console = Console()
        table = Table(show_header=True, header_style='bold cyan')
        table.add_column('Market')
        table.add_column('Modal', justify='right')
        table.add_column('Volatility', justify='right')
        table.add_column('Category')
        color_map = {'Best':'green','Good':'yellow','Fair':'blue','Avoid':'red'}
        for r in df_rows:
            cat = r.get('category','')
            style = color_map.get(cat, 'white')
            table.add_row(r.get('market_name',''), f"{r.get('modal',0):.2f}", f"{r.get('volatility',0):.2f}", f"[{style}]{cat}[/{style}]")
        console.print(table)
    else:
        print('Market | Modal | Volatility | Category')
        for r in df_rows:
            print(f"{r.get('market_name','')}	{r.get('modal',0):.2f}	{r.get('volatility',0):.2f}	{r.get('category','')}")

def show_progress(iterable, description='Processing'):
    if _have_rich():
        from rich.progress import track
        return track(iterable, description=description)
    else:
        try:
            from tqdm import tqdm
            return tqdm(iterable, desc=description)
        except Exception:
            return iterable
