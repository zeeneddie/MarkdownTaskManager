#!/usr/bin/env python3
"""
Refactor file structure: Remove intermediate layers (features/, stories/, tasks/)
From: epics/EPIC-XXX/features/FEATURE-XXX/stories/STORY-XXX/tasks/TASK-XXX.md
To: Projecten/MarkdownTaskManager/EPIC-XXX/FEATURE-XXX/STORY-XXX/TASK-XXX.md
"""

from pathlib import Path
import shutil

def refactor_structure():
    old_root = Path("/home/eddie/Projects/MarkdownTaskManager/epics")
    new_root = Path("/home/eddie/Projects/MarkdownTaskManager/Projecten/MarkdownTaskManager")

    if not old_root.exists():
        print(f"ERROR: {old_root} not found")
        return

    print(f"Refactoring from: {old_root}")
    print(f"Refactoring to: {new_root}")
    print("=" * 70)

    # Process each epic
    for epic_dir in old_root.iterdir():
        if not epic_dir.is_dir() or not epic_dir.name.startswith("EPIC-"):
            continue

        epic_id = epic_dir.name
        print(f"\n📁 Processing {epic_id}...")

        # Create new epic directory
        new_epic_dir = new_root / epic_id
        new_epic_dir.mkdir(parents=True, exist_ok=True)

        # Copy epic.md
        old_epic_file = epic_dir / "epic.md"
        if old_epic_file.exists():
            new_epic_file = new_epic_dir / "epic.md"
            shutil.copy2(old_epic_file, new_epic_file)
            print(f"  ✅ Copied epic.md")

        # Process features
        features_dir = epic_dir / "features"
        if not features_dir.exists():
            continue

        for feature_dir in features_dir.iterdir():
            if not feature_dir.is_dir() or not feature_dir.name.startswith("FEATURE-"):
                continue

            feature_id = feature_dir.name
            print(f"  📁 Processing {feature_id}...")

            # Create new feature directory (directly under epic, no 'features' folder)
            new_feature_dir = new_epic_dir / feature_id
            new_feature_dir.mkdir(parents=True, exist_ok=True)

            # Copy feature.md
            old_feature_file = feature_dir / "feature.md"
            if old_feature_file.exists():
                new_feature_file = new_feature_dir / "feature.md"
                shutil.copy2(old_feature_file, new_feature_file)
                print(f"    ✅ Copied feature.md")

            # Process stories
            stories_dir = feature_dir / "stories"
            if not stories_dir.exists():
                continue

            for story_dir in stories_dir.iterdir():
                if not story_dir.is_dir() or not story_dir.name.startswith("STORY-"):
                    continue

                story_id = story_dir.name
                print(f"    📁 Processing {story_id}...")

                # Create new story directory (directly under feature, no 'stories' folder)
                new_story_dir = new_feature_dir / story_id
                new_story_dir.mkdir(parents=True, exist_ok=True)

                # Copy story.md
                old_story_file = story_dir / "story.md"
                if old_story_file.exists():
                    new_story_file = new_story_dir / "story.md"
                    shutil.copy2(old_story_file, new_story_file)
                    print(f"      ✅ Copied story.md")

                # Process tasks
                tasks_dir = story_dir / "tasks"
                if not tasks_dir.exists():
                    continue

                for task_file in tasks_dir.glob("TASK-*.md"):
                    task_id = task_file.stem
                    print(f"      📄 Processing {task_id}.md...")

                    # Copy task file (directly under story, no 'tasks' folder)
                    new_task_file = new_story_dir / task_file.name
                    shutil.copy2(task_file, new_task_file)
                    print(f"        ✅ Copied {task_file.name}")

    print("\n" + "=" * 70)
    print("✅ Refactoring complete!")
    print(f"\nNew structure: {new_root}")

if __name__ == "__main__":
    refactor_structure()
