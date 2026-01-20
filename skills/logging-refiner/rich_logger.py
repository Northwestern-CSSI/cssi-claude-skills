"""
Rich Logger - Reusable logging components for parallel/batch processing.

Usage:
    from rich_logger import RichProgressTracker, create_parallel_processor

Example:
    tracker = RichProgressTracker(total_items=100, operation_name="Download")

    with tracker.live_display():
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(process, item, idx+1): item
                       for idx, item in enumerate(items)}
            for future in as_completed(futures):
                future.result()
                tracker.refresh()

    tracker.print_summary()
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Optional, Tuple, Generator
from contextlib import contextmanager

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich import box


class RichProgressTracker:
    """Thread-safe progress tracker with rich live display."""

    def __init__(
        self,
        total_items: int,
        operation_name: str = "Processing",
        categories: Optional[dict] = None,
        refresh_rate: int = 2
    ):
        """
        Initialize the progress tracker.

        Args:
            total_items: Total number of items to process
            operation_name: Name shown in header (e.g., "Download", "Convert")
            categories: Custom category names, defaults to:
                        {"existing": "Existing", "processing": "Processing",
                         "completed": "Completed", "failed": "Failed"}
            refresh_rate: Live display refresh rate in Hz
        """
        self.total_items = total_items
        self.operation_name = operation_name
        self.refresh_rate = refresh_rate

        # Category names (customizable)
        self.categories = categories or {
            "existing": "Existing",
            "processing": "Processing",
            "completed": "Completed",
            "failed": "Failed"
        }

        # Thread-safe tracking
        self.lock = threading.Lock()
        self.item_status = {}      # item_id -> status
        self.item_progress = {}    # item_id -> (current, total)
        self.item_index = {}       # item_id -> index (1-based)
        self.failed_items = []     # List of (item_id, error_message)

        # Timing
        self.start_time = None

        # Console
        self.console = Console()
        self._live = None

    def set_index(self, item_id: str, index: int):
        """Set the index for an item."""
        with self.lock:
            self.item_index[item_id] = index

    def set_existing(self, item_id: str):
        """Mark item as already existing (skipped)."""
        with self.lock:
            self.item_status[item_id] = "existing"

    def set_processing(self, item_id: str):
        """Mark item as currently processing."""
        with self.lock:
            self.item_status[item_id] = "processing"
            self.item_progress[item_id] = (0, 0)

    def update_progress(self, item_id: str, current: int, total: int):
        """Update progress for an item."""
        with self.lock:
            self.item_progress[item_id] = (current, total)

    def set_completed(self, item_id: str):
        """Mark item as completed."""
        with self.lock:
            self.item_status[item_id] = "completed"

    def set_failed(self, item_id: str, error: str = ""):
        """Mark item as failed."""
        with self.lock:
            self.item_status[item_id] = f"failed: {str(error)[:50]}"
            self.failed_items.append((item_id, str(error)))

    @property
    def existing_count(self) -> int:
        with self.lock:
            return len([v for v in self.item_status.values() if v == "existing"])

    @property
    def processing_count(self) -> int:
        with self.lock:
            return len([v for v in self.item_status.values() if v == "processing"])

    @property
    def completed_count(self) -> int:
        with self.lock:
            return len([v for v in self.item_status.values() if v == "completed"])

    @property
    def failed_count(self) -> int:
        with self.lock:
            return len([v for v in self.item_status.values() if v.startswith("failed")])

    @property
    def processed_count(self) -> int:
        """Items that are done (existing + completed + failed)."""
        return self.existing_count + self.completed_count + self.failed_count

    def _create_status_table(self) -> Table:
        """Create the status summary table."""
        table = Table(title=f"{self.operation_name} Status", box=box.ROUNDED, expand=True)
        table.add_column("Category", style="cyan", width=12)
        table.add_column("Count", style="magenta", justify="right", width=14)
        table.add_column("Items (up to 5)", style="dim", overflow="fold")

        with self.lock:
            existing = [(k, self.item_index.get(k, 0)) for k, v in self.item_status.items() if v == "existing"]
            processing = [(k, self.item_index.get(k, 0)) for k, v in self.item_status.items() if v == "processing"]
            completed = [(k, self.item_index.get(k, 0)) for k, v in self.item_status.items() if v == "completed"]
            failed = [(k, self.item_index.get(k, 0)) for k, v in self.item_status.items() if v.startswith("failed")]

        def format_items(item_list, limit=5, reverse=False):
            if not item_list:
                return "-"
            sorted_items = sorted(item_list, key=lambda x: -x[1] if reverse else x[1])[:limit]
            formatted = [f"{i[0][:15]}.. ({i[1]}/{self.total_items})" if len(i[0]) > 17
                        else f"{i[0]} ({i[1]}/{self.total_items})" for i in sorted_items]
            suffix = "..." if len(item_list) > limit else ""
            return ", ".join(formatted) + suffix

        table.add_row(f"[yellow]{self.categories['existing']}[/yellow]",
                      f"{len(existing)}/{self.total_items}", format_items(existing))
        table.add_row(f"[blue]{self.categories['processing']}[/blue]",
                      f"{len(processing)}/{self.total_items}", format_items(processing))
        table.add_row(f"[green]{self.categories['completed']}[/green]",
                      f"{len(completed)}/{self.total_items}", format_items(completed, reverse=True))
        table.add_row(f"[red]{self.categories['failed']}[/red]",
                      f"{len(failed)}/{self.total_items}", format_items(failed))

        return table

    def _create_progress_table(self) -> Table:
        """Create the active operations progress table."""
        table = Table(title=f"Active {self.operation_name}s", box=box.SIMPLE, expand=True)
        table.add_column("#", style="white bold", width=12, justify="right")
        table.add_column("Item", style="cyan", width=20)
        table.add_column("Progress", width=32)
        table.add_column("Current", style="green", justify="right", width=10)
        table.add_column("Total", style="blue", justify="right", width=10)

        with self.lock:
            active = [(k, v, self.item_index.get(k, 0)) for k, v in self.item_progress.items()
                      if self.item_status.get(k) == "processing"]

        active = sorted(active, key=lambda x: x[2])

        for item_id, (current, total), idx in active:
            idx_str = f"{idx}/{self.total_items}"
            item_display = item_id[:18] + ".." if len(item_id) > 20 else item_id

            if total > 0:
                pct = current / total
                bar_width = 22
                filled = int(bar_width * pct)
                bar = "[green]" + "█" * filled + "[/green]" + "░" * (bar_width - filled)
                pct_str = f"{pct*100:.1f}%"
            else:
                bar = "[dim]Starting...[/dim]"
                pct_str = ""

            # Auto-format sizes
            def fmt_size(b):
                if b < 1024:
                    return f"{b} B"
                elif b < 1024 * 1024:
                    return f"{b/1024:.0f} KB"
                else:
                    return f"{b/(1024*1024):.1f} MB"

            current_str = fmt_size(current)
            total_str = fmt_size(total) if total > 0 else "?"

            table.add_row(idx_str, item_display, f"{bar} {pct_str}", current_str, total_str)

        if not active:
            table.add_row("-", f"[dim]No active {self.operation_name.lower()}s[/dim]", "", "", "")

        return table

    def create_display(self) -> Table:
        """Create the full dashboard display."""
        layout = Table.grid(expand=True)

        # Header
        processed = self.processed_count
        header = f"[bold]{self.operation_name} Progress[/bold] - {processed}/{self.total_items} processed"

        if self.start_time:
            elapsed = time.time() - self.start_time
            header += f" | Elapsed: {elapsed:.0f}s"
            if processed > 0:
                rate = processed / elapsed
                remaining = (self.total_items - processed) / rate if rate > 0 else 0
                header += f" | ETA: {remaining:.0f}s"

        layout.add_row(Panel(header, style="blue"))
        layout.add_row(self._create_status_table())
        layout.add_row(self._create_progress_table())

        return layout

    def refresh(self):
        """Refresh the live display."""
        if self._live:
            self._live.update(self.create_display())

    @contextmanager
    def live_display(self):
        """Context manager for live display."""
        self.start_time = time.time()
        with Live(self.create_display(), console=self.console,
                  refresh_per_second=self.refresh_rate) as live:
            self._live = live
            yield live
            live.update(self.create_display())
        self._live = None

    def print_summary(self):
        """Print final summary after processing."""
        elapsed = time.time() - self.start_time if self.start_time else 0

        self.console.print("\n")
        self.console.print(Panel.fit(
            f"[bold]{self.operation_name} Complete[/bold]\n"
            f"Time elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)\n\n"
            f"[bold]Results:[/bold]\n"
            f"  [yellow]{self.categories['existing']}:[/yellow]  {self.existing_count:>10,}/{self.total_items:,}\n"
            f"  [green]{self.categories['completed']}:[/green] {self.completed_count:>10,}/{self.total_items:,}\n"
            f"  [red]{self.categories['failed']}:[/red]     {self.failed_count:>10,}/{self.total_items:,}",
            title="Summary", border_style="blue"
        ))

        if self.failed_items:
            self.console.print(f"\n[red bold]Failed items ({len(self.failed_items)}):[/red bold]")
            for item_id, error in self.failed_items[:20]:
                idx = self.item_index.get(item_id, "?")
                self.console.print(f"  - [{idx}/{self.total_items}] {item_id}: {error}")
            if len(self.failed_items) > 20:
                self.console.print(f"  ... and {len(self.failed_items) - 20} more")


def create_parallel_processor(
    items: List[Any],
    process_func: Callable[[Any, int, RichProgressTracker], Tuple[str, str]],
    operation_name: str = "Processing",
    max_workers: int = 8,
    categories: Optional[dict] = None
) -> RichProgressTracker:
    """
    Convenience function to run parallel processing with rich logging.

    Args:
        items: List of items to process
        process_func: Function(item, index, tracker) -> (item_id, status)
                     Should call tracker.set_* methods to update status
        operation_name: Name for the operation
        max_workers: Number of parallel workers
        categories: Custom category names

    Returns:
        RichProgressTracker with final statistics

    Example:
        def download_file(item, index, tracker):
            file_id = item['id']
            tracker.set_index(file_id, index)

            if os.path.exists(item['path']):
                tracker.set_existing(file_id)
                return file_id, "existing"

            tracker.set_processing(file_id)
            try:
                # Download with progress updates
                for downloaded, total in download_with_progress(item['url']):
                    tracker.update_progress(file_id, downloaded, total)
                tracker.set_completed(file_id)
                return file_id, "completed"
            except Exception as e:
                tracker.set_failed(file_id, str(e))
                return file_id, "failed"

        tracker = create_parallel_processor(files, download_file, "Download", max_workers=10)
    """
    tracker = RichProgressTracker(
        total_items=len(items),
        operation_name=operation_name,
        categories=categories
    )

    with tracker.live_display():
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_func, item, idx + 1, tracker): item
                for idx, item in enumerate(items)
            }

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass
                tracker.refresh()

    tracker.print_summary()
    return tracker
