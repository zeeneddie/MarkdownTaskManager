#!/usr/bin/env python3
"""
Live File Watcher Test - Test auto-sync by editing markdown files

Run this script, then edit any .md file in Projecten/MarkdownTaskManager/
The watcher will detect changes and trigger sync.
"""

import asyncio
from pathlib import Path
import logging
from file_watcher import MarkdownFileWatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def sync_callback():
    """
    Callback function triggered when markdown files change.

    In production, this would call:
        await sync_markdown_to_db(project_root, db_session)
    """
    print("\n" + "="*70)
    print("🔄 SYNC TRIGGERED!")
    print("="*70)
    print("File change detected - would sync to database now")
    print("(Simulating sync process...)")

    # Simulate some work
    await asyncio.sleep(0.5)

    print("✅ Sync complete!")
    print("="*70 + "\n")


async def main():
    project_root = Path("/home/eddie/Projects/MarkdownTaskManager")

    print("\n" + "="*70)
    print("📁 FILE WATCHER TEST - Live Monitoring")
    print("="*70)
    print(f"\nWatching: {project_root}/Projecten/MarkdownTaskManager/")
    print("\nInstructions:")
    print("1. This script will monitor for .md file changes")
    print("2. Open any .md file in Projecten/MarkdownTaskManager/")
    print("3. Make a change and save")
    print("4. Watch the sync trigger automatically!")
    print("\nDebounce: 2 seconds (multiple rapid changes = 1 sync)")
    print("\nPress Ctrl+C to stop")
    print("="*70 + "\n")

    # Create and start watcher
    watcher = MarkdownFileWatcher(
        project_root,
        sync_callback,
        debounce_seconds=2.0
    )

    try:
        watcher.start()

        # Keep running until Ctrl+C
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\nStopping watcher...")
        watcher.stop()
        print("✅ Watcher stopped")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        watcher.stop()


if __name__ == "__main__":
    asyncio.run(main())
