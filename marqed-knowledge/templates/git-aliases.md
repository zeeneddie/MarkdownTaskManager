# Git Aliases for AI-Assisted Development
# MarQed.ai Platform - Week 101

## Installation

Add these aliases to your `~/.gitconfig`:

```bash
git config --global alias.checkpoint '!f() { git add -A && git commit -m "✅ Checkpoint: $1"; }; f'
git config --global alias.micro '!f() { git add -A && git commit -m "📍 Micro: $1"; }; f'
git config --global alias.wip '!f() { git add -A && git commit -m "🔄 WIP: $1"; }; f'
git config --global alias.fix '!f() { git add -A && git commit -m "🔧 Fix: $1"; }; f'
git config --global alias.feat '!f() { git add -A && git commit -m "✨ Feature: $1"; }; f'
git config --global alias.refactor '!f() { git add -A && git commit -m "♻️ Refactor: $1"; }; f'
git config --global alias.test '!f() { git add -A && git commit -m "🧪 Test: $1"; }; f'
git config --global alias.docs '!f() { git add -A && git commit -m "📝 Docs: $1"; }; f'
```

Or copy the [alias] section below to your `~/.gitconfig`:

```ini
[alias]
    # =========================================================================
    # Quick Commits with Emoji Markers
    # =========================================================================

    # Checkpoint: Save progress at a stable point
    # Usage: git checkpoint "completed user authentication"
    checkpoint = "!f() { git add -A && git commit -m \"✅ Checkpoint: $1\"; }; f"

    # Micro-checkpoint: Very small incremental saves
    # Usage: git micro "added validation helper"
    micro = "!f() { git add -A && git commit -m \"📍 Micro: $1\"; }; f"

    # Work in progress: Unfinished but need to save
    # Usage: git wip "halfway through refactoring"
    wip = "!f() { git add -A && git commit -m \"🔄 WIP: $1\"; }; f"

    # Bug fix
    # Usage: git fix "null pointer in user service"
    fix = "!f() { git add -A && git commit -m \"🔧 Fix: $1\"; }; f"

    # New feature
    # Usage: git feat "user profile page"
    feat = "!f() { git add -A && git commit -m \"✨ Feature: $1\"; }; f"

    # Refactoring
    # Usage: git refactor "extract payment service"
    refactor = "!f() { git add -A && git commit -m \"♻️ Refactor: $1\"; }; f"

    # Tests
    # Usage: git test "user service unit tests"
    test = "!f() { git add -A && git commit -m \"🧪 Test: $1\"; }; f"

    # Documentation
    # Usage: git docs "API endpoint documentation"
    docs = "!f() { git add -A && git commit -m \"📝 Docs: $1\"; }; f"

    # =========================================================================
    # AI Development Workflow
    # =========================================================================

    # Start AI session: Create a branch for AI-assisted work
    # Usage: git ai-start "feature-auth-system"
    ai-start = "!f() { git checkout -b ai/$1 && git checkpoint \"Started AI session: $1\"; }; f"

    # End AI session: Summarize and prepare for review
    # Usage: git ai-end "Completed authentication system"
    ai-end = "!f() { git add -A && git commit -m \"🤖 AI Session Complete: $1\"; }; f"

    # Rollback AI changes: Reset to last checkpoint
    # Usage: git ai-rollback
    ai-rollback = "!git reset --hard HEAD~1"

    # Squash AI commits: Combine micro-commits into one
    # Usage: git ai-squash 5 "Implemented user authentication"
    ai-squash = "!f() { git reset --soft HEAD~$1 && git commit -m \"$2\"; }; f"

    # =========================================================================
    # Review & Quality
    # =========================================================================

    # Show changes since last checkpoint
    last-changes = "diff HEAD~1"

    # Show recent commits with graph
    history = "log --oneline --graph -10"

    # Show commits by marker type
    checkpoints = "log --oneline --grep='Checkpoint'"

    # List modified files
    changed = "diff --name-only HEAD~1"

    # =========================================================================
    # Safety
    # =========================================================================

    # Undo last commit but keep changes
    undo = "reset --soft HEAD~1"

    # Completely discard last commit
    discard = "reset --hard HEAD~1"

    # Show what would be committed
    preview = "diff --cached"

    # Status with short format
    s = "status -sb"
```

## Usage Patterns

### During AI-Assisted Development

1. **Start a session:**
   ```bash
   git ai-start "implement-user-auth"
   ```

2. **Make micro-commits frequently:**
   ```bash
   git micro "added User entity"
   git micro "added UserRepository"
   git micro "added UserService"
   ```

3. **Create checkpoints at stable points:**
   ```bash
   git checkpoint "user CRUD complete"
   ```

4. **If something goes wrong, rollback:**
   ```bash
   git ai-rollback
   ```

5. **End the session:**
   ```bash
   git ai-end "User authentication system complete"
   ```

### Commit Message Conventions

| Emoji | Type | Usage |
|-------|------|-------|
| ✅ | Checkpoint | Stable, tested state |
| 📍 | Micro | Small incremental change |
| 🔄 | WIP | Work in progress, unstable |
| 🔧 | Fix | Bug fix |
| ✨ | Feature | New feature |
| ♻️ | Refactor | Code restructuring |
| 🧪 | Test | Test additions/changes |
| 📝 | Docs | Documentation |
| 🤖 | AI | AI-generated code |

## Best Practices

1. **Commit often**: Small commits are easier to review and rollback
2. **Use descriptive messages**: Future you will thank present you
3. **Checkpoint before experiments**: Easy to rollback if it fails
4. **Review AI commits**: Never push without human review
5. **Squash before PR**: Clean up micro-commits for reviewers

---

**Version:** 1.0.0
**Updated:** 2024-12-24
