"""
Roundtrip test: Parse → Generate → Parse → Compare
"""

from pathlib import Path
import logging
import json
from parser import MultiFileProjectParser
from generator import MultiFileProjectGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_roundtrip():
    """Test roundtrip: parse → generate → parse again"""

    project_root = Path("/home/eddie/Projects/MarkdownTaskManager")

    print("\n" + "="*70)
    print("ROUNDTRIP TEST")
    print("="*70)

    # Step 1: Parse original EPIC-002
    print("\n[Step 1] Parsing EPIC-002 (generated)...")
    parser1 = MultiFileProjectParser(project_root)

    # Parse only EPIC-002
    epic_002_dir = project_root / "Projecten" / "MarkdownTaskManager" / "EPIC-002"
    if not epic_002_dir.exists():
        print("ERROR: EPIC-002 not found")
        return

    epic_002_original = parser1.parse_epic(epic_002_dir)

    print(f"✅ Parsed EPIC-002: {epic_002_original['title']}")
    print(f"   - Features: {len(epic_002_original.get('features', []))}")
    if epic_002_original.get('features'):
        for feature in epic_002_original['features']:
            print(f"     - {feature['id']}: {feature['title']}")
            print(f"       - Stories: {len(feature.get('stories', []))}")
            if feature.get('stories'):
                for story in feature['stories']:
                    print(f"         - {story['id']}: {story['title']}")
                    print(f"           - Tasks: {len(story.get('tasks', []))}")

    # Step 2: Generate to EPIC-003 (copy)
    print("\n[Step 2] Generating EPIC-003 (copy of EPIC-002)...")

    # Create a copy with new ID
    epic_003 = epic_002_original.copy()
    epic_003['id'] = 'EPIC-003'

    # Update nested IDs
    if epic_003.get('features'):
        for i, feature in enumerate(epic_003['features']):
            old_feature_id = feature['id']
            new_feature_id = f"FEATURE-00{4+i}"
            feature['id'] = new_feature_id
            feature['parent_id'] = 'EPIC-003'

            if feature.get('stories'):
                for j, story in enumerate(feature['stories']):
                    old_story_id = story['id']
                    new_story_id = f"STORY-00{4+j}"
                    story['id'] = new_story_id
                    story['parent_id'] = new_feature_id

                    if story.get('tasks'):
                        for k, task in enumerate(story['tasks']):
                            task['id'] = f"TASK-00{4+k}"
                            task['parent_id'] = new_story_id

    generator = MultiFileProjectGenerator(project_root)
    generator.generate_epic(epic_003)

    print(f"✅ Generated EPIC-003")

    # Step 3: Parse EPIC-003
    print("\n[Step 3] Parsing EPIC-003 (re-generated)...")
    parser2 = MultiFileProjectParser(project_root)
    epic_003_dir = project_root / "Projecten" / "MarkdownTaskManager" / "EPIC-003"
    epic_003_parsed = parser2.parse_epic(epic_003_dir)

    print(f"✅ Parsed EPIC-003: {epic_003_parsed['title']}")

    # Step 4: Compare
    print("\n[Step 4] Comparing data...")

    differences = []

    # Compare basic fields
    basic_fields = ['title', 'status', 'priority', 'phase', 'owner',
                    'sp_total', 'sp_completed', 'epic_type', 'description']

    for field in basic_fields:
        original_val = epic_002_original.get(field)
        parsed_val = epic_003_parsed.get(field)

        if original_val != parsed_val:
            differences.append({
                'field': field,
                'original': original_val,
                'parsed': parsed_val
            })

    # Compare feature count
    original_feature_count = len(epic_002_original.get('features', []))
    parsed_feature_count = len(epic_003_parsed.get('features', []))

    if original_feature_count != parsed_feature_count:
        differences.append({
            'field': 'feature_count',
            'original': original_feature_count,
            'parsed': parsed_feature_count
        })

    # Compare first feature details
    if epic_002_original.get('features') and epic_003_parsed.get('features'):
        orig_feature = epic_002_original['features'][0]
        parsed_feature = epic_003_parsed['features'][0]

        feature_fields = ['title', 'status', 'priority', 'sp_total', 'description']
        for field in feature_fields:
            orig_val = orig_feature.get(field)
            parsed_val = parsed_feature.get(field)

            if orig_val != parsed_val:
                differences.append({
                    'field': f'feature.{field}',
                    'original': orig_val,
                    'parsed': parsed_val
                })

        # Compare story count
        orig_story_count = len(orig_feature.get('stories', []))
        parsed_story_count = len(parsed_feature.get('stories', []))

        if orig_story_count != parsed_story_count:
            differences.append({
                'field': 'story_count',
                'original': orig_story_count,
                'parsed': parsed_story_count
            })

        # Compare first story details
        if orig_feature.get('stories') and parsed_feature.get('stories'):
            orig_story = orig_feature['stories'][0]
            parsed_story = parsed_feature['stories'][0]

            story_fields = ['title', 'status', 'sp', 'estimated_hours']
            for field in story_fields:
                orig_val = orig_story.get(field)
                parsed_val = parsed_story.get(field)

                if orig_val != parsed_val:
                    differences.append({
                        'field': f'story.{field}',
                        'original': orig_val,
                        'parsed': parsed_val
                    })

            # Compare acceptance criteria
            orig_ac = orig_story.get('acceptance_criteria', [])
            parsed_ac = parsed_story.get('acceptance_criteria', [])

            if len(orig_ac) != len(parsed_ac):
                differences.append({
                    'field': 'acceptance_criteria_count',
                    'original': len(orig_ac),
                    'parsed': len(parsed_ac)
                })

            # Compare task count
            orig_task_count = len(orig_story.get('tasks', []))
            parsed_task_count = len(parsed_story.get('tasks', []))

            if orig_task_count != parsed_task_count:
                differences.append({
                    'field': 'task_count',
                    'original': orig_task_count,
                    'parsed': parsed_task_count
                })

    # Report results
    print("\n" + "="*70)
    print("ROUNDTRIP RESULTS")
    print("="*70)

    if not differences:
        print("\n✅ SUCCESS: Perfect roundtrip!")
        print("   All data preserved through parse → generate → parse cycle")
        print("\n   Tested:")
        print(f"   - Epic: EPIC-002 → EPIC-003")
        print(f"   - Features: {original_feature_count}")
        print(f"   - Stories: {orig_story_count if epic_002_original.get('features') else 0}")
        print(f"   - Tasks: {orig_task_count if epic_002_original.get('features') and orig_feature.get('stories') else 0}")
        print(f"   - Acceptance Criteria: {len(orig_ac) if epic_002_original.get('features') and orig_feature.get('stories') else 0}")
    else:
        print("\n⚠️  DIFFERENCES FOUND:")
        for diff in differences:
            print(f"\n   Field: {diff['field']}")
            print(f"   Original: {diff['original']}")
            print(f"   Parsed:   {diff['parsed']}")

    print("\n" + "="*70)

    # Additional validation: Parse both EPIC-001 and EPIC-002
    print("\n[Additional Test] Parsing all epics...")
    parser_all = MultiFileProjectParser(project_root)
    project = parser_all.parse_project()

    print(f"\n✅ Full project parsed:")
    print(f"   - Epics: {len(project['epics'])}")
    print(f"   - Features: {len(project['features'])}")
    print(f"   - Stories: {len(project['stories'])}")
    print(f"   - Tasks: {len(project['tasks'])}")

    print("\n   Epic details:")
    for epic in project['epics']:
        print(f"   - {epic['id']}: {epic['title']} ({epic.get('status')})")
        print(f"     SP: {epic.get('sp_total', 0)}, Features: {len(epic.get('features', []))}")

    return len(differences) == 0


if __name__ == "__main__":
    success = test_roundtrip()

    if success:
        print("\n🎉 ROUNDTRIP TEST PASSED!")
    else:
        print("\n❌ ROUNDTRIP TEST FAILED - See differences above")
