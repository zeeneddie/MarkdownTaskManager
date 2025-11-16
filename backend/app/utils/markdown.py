from typing import Dict, Any
from datetime import datetime

def generate_epic_markdown(epic: Dict[str, Any]) -> str:
    """Generate markdown representation of epic"""
    md = f"# {epic['id']} | {epic['title']}\n\n"
    md += f"**Type**: Epic\n"

    if epic.get('priority'):
        md += f"**Priority**: {epic['priority']}\n"
    if epic.get('status'):
        md += f"**Status**: {epic['status']}\n"
    if epic.get('owner'):
        md += f"**Owner**: {epic['owner']}\n"
    if epic.get('phase'):
        md += f"**Phase**: {epic['phase']}\n"

    if epic.get('created_at'):
        md += f"**Created**: {epic['created_at'].strftime('%Y-%m-%d') if isinstance(epic['created_at'], datetime) else epic['created_at']}\n"
    if epic.get('target_date'):
        md += f"**Target Date**: {epic['target_date'].strftime('%Y-%m-%d') if isinstance(epic['target_date'], datetime) else epic['target_date']}\n"

    md += f"\n## Story Points\n"
    md += f"**Total**: {epic.get('sp_total', 0)} SP\n"
    md += f"**Completed**: {epic.get('sp_completed', 0)} SP\n"

    if epic.get('description'):
        md += f"\n## Description\n{epic['description']}\n"

    return md

def generate_feature_markdown(feature: Dict[str, Any]) -> str:
    """Generate markdown representation of feature"""
    md = f"# {feature['id']} | {feature['title']}\n\n"
    md += f"**Type**: Feature\n"
    md += f"**Parent**: {feature.get('parent_id', 'N/A')}\n"

    if feature.get('priority'):
        md += f"**Priority**: {feature['priority']}\n"
    if feature.get('status'):
        md += f"**Status**: {feature['status']}\n"
    if feature.get('owner'):
        md += f"**Owner**: {feature['owner']}\n"
    if feature.get('assigned_to'):
        md += f"**Assigned To**: {feature['assigned_to']}\n"

    if feature.get('created_at'):
        md += f"**Created**: {feature['created_at'].strftime('%Y-%m-%d') if isinstance(feature['created_at'], datetime) else feature['created_at']}\n"
    if feature.get('target_date'):
        md += f"**Target Date**: {feature['target_date'].strftime('%Y-%m-%d') if isinstance(feature['target_date'], datetime) else feature['target_date']}\n"

    md += f"\n## Story Points\n"
    md += f"**Total**: {feature.get('sp_total', 0)} SP\n"
    md += f"**Completed**: {feature.get('sp_completed', 0)} SP\n"

    if feature.get('description'):
        md += f"\n## Description\n{feature['description']}\n"

    return md

def generate_story_markdown(story: Dict[str, Any]) -> str:
    """Generate markdown representation of story"""
    md = f"# {story['id']} | {story['title']}\n\n"
    md += f"**Type**: Story\n"
    md += f"**Parent**: {story.get('parent_id', 'N/A')}\n"

    if story.get('priority'):
        md += f"**Priority**: {story['priority']}\n"
    if story.get('status'):
        md += f"**Status**: {story['status']}\n"
    if story.get('owner'):
        md += f"**Owner**: {story['owner']}\n"
    if story.get('assigned_to'):
        md += f"**Assigned To**: {story['assigned_to']}\n"
    if story.get('sp'):
        md += f"**Story Points**: {story['sp']} SP\n"
    if story.get('sprint'):
        md += f"**Sprint**: {story['sprint']}\n"

    if story.get('created_at'):
        md += f"**Created**: {story['created_at'].strftime('%Y-%m-%d') if isinstance(story['created_at'], datetime) else story['created_at']}\n"
    if story.get('target_date'):
        md += f"**Target Date**: {story['target_date'].strftime('%Y-%m-%d') if isinstance(story['target_date'], datetime) else story['target_date']}\n"

    if story.get('description'):
        md += f"\n## Description\n{story['description']}\n"

    return md

def generate_task_markdown(task: Dict[str, Any]) -> str:
    """Generate markdown representation of task"""
    md = f"# {task['id']} | {task['title']}\n\n"
    md += f"**Type**: Task\n"
    md += f"**Parent**: {task.get('parent_id', 'N/A')}\n"

    if task.get('priority'):
        md += f"**Priority**: {task['priority']}\n"
    if task.get('status'):
        md += f"**Status**: {task['status']}\n"
    if task.get('assigned_to'):
        md += f"**Assigned To**: {task['assigned_to']}\n"
    if task.get('hours'):
        md += f"**Hours**: {task['hours']}h\n"

    if task.get('created_at'):
        md += f"**Created**: {task['created_at'].strftime('%Y-%m-%d') if isinstance(task['created_at'], datetime) else task['created_at']}\n"
    if task.get('target_date'):
        md += f"**Target Date**: {task['target_date'].strftime('%Y-%m-%d') if isinstance(task['target_date'], datetime) else task['target_date']}\n"

    if task.get('description'):
        md += f"\n## Description\n{task['description']}\n"

    return md

def parse_markdown(content: str) -> Dict[str, Any]:
    """Parse markdown content into structured data"""
    # This is a simplified parser - could be enhanced with proper markdown parsing library
    data = {}
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            # Parse title
            parts = line[2:].split('|')
            if len(parts) == 2:
                data['id'] = parts[0].strip()
                data['title'] = parts[1].strip()
        elif line.startswith('**') and line.endswith('**'):
            # Parse metadata
            parts = line[2:-2].split('**: ')
            if len(parts) == 2:
                key = parts[0].lower().replace(' ', '_')
                value = parts[1]
                data[key] = value

    return data
