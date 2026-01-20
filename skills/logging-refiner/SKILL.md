---
name: logging-refiner
description: Refine logging for parallel/batch processing scripts with rich-based live dashboards. Shows file indices (x/N), progress bars, status tables, and detailed summaries. Apply to downloads, data processing, or any multi-file operations.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Logging Refiner Skill

Transform basic logging (print statements, tqdm) into professional rich-based live dashboards for parallel/batch processing operations.

## When to Use

Apply this skill when refining logging for:
- Parallel download scripts
- Batch file processing
- Multi-file data pipelines
- Any operation processing N items with progress tracking

## Required Packages

```python
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich import box
import threading
```

## Core Components

### 1. Thread-Safe Status Tracking

```python
import threading

# Global tracking dictionaries
item_status = {}      # item_id -> status (existing/processing/completed/failed)
item_progress = {}    # item_id -> (current_bytes, total_bytes)
item_index = {}       # item_id -> index (1-based)
total_items = 0       # Set after counting items
status_lock = threading.Lock()
console = Console()
```

### 2. Status Categories

Always track these four states:
- **existing** (yellow): Already done, skipped
- **processing/downloading** (blue): Currently active
- **completed** (green): Successfully finished
- **failed** (red): Error occurred

### 3. Status Table Function

```python
def create_status_table():
    """Create a status table showing all states with x/N counts."""
    table = Table(title="Processing Status", box=box.ROUNDED, expand=True)
    table.add_column("Category", style="cyan", width=12)
    table.add_column("Count", style="magenta", justify="right", width=14)
    table.add_column("Items (showing up to 5)", style="dim", overflow="fold")

    with status_lock:
        existing = [(k, item_index.get(k, 0)) for k, v in item_status.items() if v == "existing"]
        processing = [(k, item_index.get(k, 0)) for k, v in item_status.items() if v == "processing"]
        completed = [(k, item_index.get(k, 0)) for k, v in item_status.items() if v == "completed"]
        failed = [(k, item_index.get(k, 0)) for k, v in item_status.items() if v.startswith("failed")]

    def format_items(item_list, limit=5):
        if not item_list:
            return "-"
        sorted_items = sorted(item_list, key=lambda x: x[1])[:limit]
        formatted = [f"{item[0]} ({item[1]}/{total_items})" for item in sorted_items]
        suffix = "..." if len(item_list) > limit else ""
        return ", ".join(formatted) + suffix

    table.add_row("[yellow]Existing[/yellow]", f"{len(existing)}/{total_items}", format_items(existing))
    table.add_row("[blue]Processing[/blue]", f"{len(processing)}/{total_items}", format_items(processing))
    table.add_row("[green]Completed[/green]", f"{len(completed)}/{total_items}",
                  format_items(sorted(completed, key=lambda x: -x[1])[:5]))  # Most recent
    table.add_row("[red]Failed[/red]", f"{len(failed)}/{total_items}", format_items(failed))

    return table
```

### 4. Active Progress Table Function

```python
def create_progress_display():
    """Create a display showing active item progress with x/N indices."""
    table = Table(title="Active Operations", box=box.SIMPLE, expand=True)
    table.add_column("#", style="white bold", width=12, justify="right")
    table.add_column("Item", style="cyan", width=20)
    table.add_column("Progress", width=35)
    table.add_column("Current", style="green", justify="right", width=10)
    table.add_column("Total", style="blue", justify="right", width=10)

    with status_lock:
        active = [(k, v, item_index.get(k, 0)) for k, v in item_progress.items()
                  if item_status.get(k) == "processing"]

    # Sort by index
    active = sorted(active, key=lambda x: x[2])

    for item_id, (current, total), idx in active:
        idx_str = f"{idx}/{total_items}"

        if total > 0:
            pct = current / total
            bar_width = 25
            filled = int(bar_width * pct)
            bar = "[green]" + "█" * filled + "[/green]" + "░" * (bar_width - filled)
            pct_str = f"{pct*100:.1f}%"
        else:
            bar = "[dim]Starting...[/dim]"
            pct_str = ""

        # Format sizes (adapt units as needed)
        current_str = f"{current / (1024*1024):.1f} MB"
        total_str = f"{total / (1024*1024):.1f} MB" if total > 0 else "?"

        table.add_row(idx_str, item_id[:18] + ".." if len(item_id) > 20 else item_id,
                      f"{bar} {pct_str}", current_str, total_str)

    if not active:
        table.add_row("-", "[dim]No active operations[/dim]", "", "", "")

    return table
```

### 5. Full Dashboard Function

```python
import time

def create_full_display(start_time=None):
    """Create the full display combining header, status table, and progress."""
    with status_lock:
        processed = len([s for s in item_status.values()
                        if s in ("existing", "completed") or s.startswith("failed")])

    layout = Table.grid(expand=True)

    # Header with progress and timing
    header_text = f"[bold]Operation Progress[/bold] - {processed}/{total_items} files processed"
    if start_time:
        elapsed = time.time() - start_time
        header_text += f" | Elapsed: {elapsed:.0f}s"
        if processed > 0:
            rate = processed / elapsed
            remaining = (total_items - processed) / rate if rate > 0 else 0
            header_text += f" | ETA: {remaining:.0f}s"

    layout.add_row(Panel(header_text, style="blue"))
    layout.add_row(create_status_table())
    layout.add_row(create_progress_display())

    return layout
```

### 6. Main Execution Pattern

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_item(item, index):
    """Process a single item with status updates."""
    item_id = get_item_id(item)

    with status_lock:
        item_index[item_id] = index

    # Check if already done
    if is_already_done(item):
        with status_lock:
            item_status[item_id] = "existing"
        return item_id, "existing"

    # Mark as processing
    with status_lock:
        item_status[item_id] = "processing"
        item_progress[item_id] = (0, 0)

    try:
        # Do the work, updating progress periodically
        for current, total in do_work_with_progress(item):
            with status_lock:
                item_progress[item_id] = (current, total)

        with status_lock:
            item_status[item_id] = "completed"
        return item_id, "completed"

    except Exception as e:
        with status_lock:
            item_status[item_id] = f"failed: {str(e)[:50]}"
        return item_id, "failed"


# Main execution
items = get_all_items()
total_items = len(items)
start_time = time.time()

MAX_WORKERS = 8

with Live(create_full_display(start_time), console=console, refresh_per_second=2) as live:
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_item, item, idx+1): item
                   for idx, item in enumerate(items)}

        for future in as_completed(futures):
            try:
                item_id, status = future.result()
            except Exception:
                pass
            live.update(create_full_display(start_time))
```

### 7. Final Summary

```python
# Print final summary
console.print("\n[bold]Summary:[/bold]")
with status_lock:
    existing = len([v for v in item_status.values() if v == "existing"])
    completed = len([v for v in item_status.values() if v == "completed"])
    failed = [(k, v) for k, v in item_status.items() if v.startswith("failed")]

console.print(f"  [yellow]Already existed:[/yellow] {existing}/{total_items}")
console.print(f"  [green]Newly completed:[/green] {completed}/{total_items}")
console.print(f"  [red]Failed:[/red] {len(failed)}/{total_items}")

if failed:
    console.print("\n[red bold]Failed items:[/red bold]")
    for item_id, error in failed[:20]:
        idx = item_index.get(item_id, "?")
        console.print(f"  - [{idx}/{total_items}] {item_id}: {error}")
    if len(failed) > 20:
        console.print(f"  ... and {len(failed) - 20} more")

console.print("\n[bold green]Operation completed![/bold green]")
```

## Visual Output Example

```
╭─────────────────────────────────────────────────────────────────────╮
│ Operation Progress - 45/100 files processed | Elapsed: 120s | ETA: 147s │
╰─────────────────────────────────────────────────────────────────────╯

                         Download Status
╭──────────────┬──────────────┬─────────────────────────────────────╮
│ Category     │        Count │ Items (showing up to 5)             │
├──────────────┼──────────────┼─────────────────────────────────────┤
│ Existing     │       20/100 │ file_001 (1/100), file_002 (2/100)..│
│ Downloading  │        8/100 │ file_021 (21/100), file_022 (22/100)│
│ Completed    │       15/100 │ file_035 (35/100), file_034 (34/100)│
│ Failed       │        2/100 │ file_010 (10/100), file_015 (15/100)│
╰──────────────┴──────────────┴─────────────────────────────────────╯

                          Active Downloads
       #     Item              Progress                    Current     Total
  21/100     file_021          ████████░░░░░░░ 45.2%       150.3 MB   332.1 MB
  22/100     file_022          ██░░░░░░░░░░░░░ 12.8%        42.5 MB   332.1 MB
  23/100     file_023          Connecting...                  0 MB        ?
```

## Key Design Principles

1. **Always show x/N**: Every item shows its position (e.g., `21/100`)
2. **Four status categories**: existing (skipped), processing, completed, failed
3. **Thread-safe**: Use locks for all shared state
4. **Live updates**: 2Hz refresh rate with `rich.live.Live`
5. **Visual progress bars**: Unicode blocks (█░) for clear visualization
6. **ETA calculation**: Based on processing rate
7. **Truncate long IDs**: Keep display clean with `id[:18] + ".."`
8. **Final summary**: Clear counts with failed item details

## Customization Points

- **Status categories**: Rename "processing" to "downloading", "converting", etc.
- **Progress units**: Change MB to KB, items, records, etc.
- **Table widths**: Adjust column widths for your ID lengths
- **Refresh rate**: Lower for slower operations, higher for fast ones
- **Items shown**: Adjust `limit` parameter in `format_items()`
