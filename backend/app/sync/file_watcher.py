"""
File Watcher - Monitor markdown files for changes and trigger auto-sync
"""

from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
import asyncio
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class MarkdownFileHandler(FileSystemEventHandler):
    """
    Handler for markdown file changes.

    Triggers sync when .md files are modified or created.
    """

    def __init__(self, sync_callback: Callable, debounce_seconds: float = 2.0):
        """
        Args:
            sync_callback: Async function to call when sync is needed
            debounce_seconds: Wait time before triggering sync (prevents rapid syncs)
        """
        self.sync_callback = sync_callback
        self.debounce_seconds = debounce_seconds
        self.pending_sync = False
        self.debounce_task: Optional[asyncio.Task] = None

    def on_modified(self, event):
        """Handle file modification events"""
        if isinstance(event, FileModifiedEvent) and event.src_path.endswith('.md'):
            logger.debug(f"Markdown file modified: {event.src_path}")
            self._schedule_sync(event.src_path)

    def on_created(self, event):
        """Handle file creation events"""
        if isinstance(event, FileCreatedEvent) and event.src_path.endswith('.md'):
            logger.debug(f"Markdown file created: {event.src_path}")
            self._schedule_sync(event.src_path)

    def _schedule_sync(self, file_path: str):
        """
        Schedule a sync with debouncing.

        Multiple rapid changes trigger only one sync after debounce period.
        """
        if self.debounce_task and not self.debounce_task.done():
            # Cancel pending sync
            self.debounce_task.cancel()

        # Schedule new sync
        self.debounce_task = asyncio.create_task(self._debounced_sync(file_path))

    async def _debounced_sync(self, file_path: str):
        """
        Wait for debounce period, then trigger sync.
        """
        try:
            await asyncio.sleep(self.debounce_seconds)
            logger.info(f"Triggering sync due to change in: {file_path}")
            await self.sync_callback()
        except asyncio.CancelledError:
            logger.debug("Debounced sync cancelled (new change detected)")
        except Exception as e:
            logger.error(f"Error during debounced sync: {str(e)}")


class MarkdownFileWatcher:
    """
    Watches markdown directory for changes and triggers auto-sync.

    Usage:
        async def sync_callback():
            await sync_markdown_to_db(project_root, db)

        watcher = MarkdownFileWatcher(project_root, sync_callback)
        watcher.start()

        # Later...
        watcher.stop()
    """

    def __init__(self, project_root: Path, sync_callback: Callable,
                 debounce_seconds: float = 2.0):
        """
        Args:
            project_root: Root directory to watch
            sync_callback: Async function to call when sync is needed
            debounce_seconds: Wait time before triggering sync
        """
        self.project_root = Path(project_root)
        self.markdown_dir = self.project_root / "Projecten" / "MarkdownTaskManager"
        self.sync_callback = sync_callback
        self.debounce_seconds = debounce_seconds

        self.observer: Optional[Observer] = None
        self.handler: Optional[MarkdownFileHandler] = None

    def start(self):
        """Start watching for file changes"""
        if self.observer and self.observer.is_alive():
            logger.warning("File watcher already running")
            return

        if not self.markdown_dir.exists():
            raise FileNotFoundError(f"Markdown directory not found: {self.markdown_dir}")

        logger.info(f"Starting file watcher on: {self.markdown_dir}")

        # Create handler and observer
        self.handler = MarkdownFileHandler(self.sync_callback, self.debounce_seconds)
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.markdown_dir), recursive=True)

        # Start observer thread
        self.observer.start()

        logger.info("File watcher started")

    def stop(self):
        """Stop watching for file changes"""
        if not self.observer:
            logger.warning("File watcher not running")
            return

        logger.info("Stopping file watcher")

        # Stop observer thread
        self.observer.stop()
        self.observer.join(timeout=5)

        self.observer = None
        self.handler = None

        logger.info("File watcher stopped")

    def is_running(self) -> bool:
        """Check if watcher is currently running"""
        return self.observer is not None and self.observer.is_alive()


# Example usage
if __name__ == "__main__":
    import asyncio

    async def example_sync():
        """Example sync callback"""
        print("Sync triggered!")
        await asyncio.sleep(1)  # Simulate sync work
        print("Sync complete!")

    async def main():
        project_root = Path("/home/eddie/Projects/MarkdownTaskManager")

        # Create watcher
        watcher = MarkdownFileWatcher(project_root, example_sync, debounce_seconds=2.0)

        # Start watching
        watcher.start()

        # Keep running for 60 seconds
        print("Watching for changes... (60 seconds)")
        await asyncio.sleep(60)

        # Stop watching
        watcher.stop()

    # Run example
    asyncio.run(main())
