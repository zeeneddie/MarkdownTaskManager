# Forked Repositories Tracking

**Last Updated:** 2026-01-08
**Owner:** zeeneddie
**Purpose:** Track sync status with upstream repositories

---

## How to Use

Before making significant commits, check if any of these repos have updates:

```bash
# Quick sync check for all repos
gh api users/zeeneddie/repos --jq '.[].name' | while read repo; do
  echo "Checking $repo..."
  gh api repos/zeeneddie/$repo --jq '.parent.full_name // "not a fork"'
done
```

---

## Active Forked Repositories

| # | Our Repo | Original Upstream | Purpose | Last Checked |
|---|----------|-------------------|---------|--------------|
| 1 | `zeeneddie/claude-code-by-agents` | TBD | Multi-agent orchestration, Claude CLI auth | 2026-01-08 |
| 2 | `zeeneddie/equilateral-agents-open-core` | TBD | 22 self-learning agents, institutional knowledge | 2026-01-08 |
| 3 | `zeeneddie/agents2` | TBD | 87 agents, 47 skills, 64 plugins | 2026-01-08 |
| 4 | `zeeneddie/a-list-of-claude-code-agents` | TBD | Agent definitions (Python, UI, Reviewer) | 2026-01-08 |
| 5 | `zeeneddie/AgentEvolver` | TBD | Self-evolution patterns | 2026-01-08 |
| 6 | `zeeneddie/context-engineering-intro` | coleam00/context-engineering-intro | Validation framework | 2026-01-08 |
| 7 | `zeeneddie/kaibanjs` | kaiban-ai/KaibanJS | Kanban system | 2026-01-08 |
| 8 | `zeeneddie/llm-council` | TBD | Multi-LLM coordination | 2026-01-08 |
| 9 | `zeeneddie/agent-os` | TBD | Standards system | 2026-01-08 |
| 10 | `zeeneddie/design-os` | buildermethods/design-os | Design methodology (Brian Casel) | 2026-01-08 |
| 11 | `zeeneddie/CodeWiki` | TBD | Documentation generation | 2026-01-08 |
| 12 | `zeeneddie/user-story` | TBD | Portal frontend (React) | 2026-01-08 |
| 13 | `zeeneddie/strapi` | strapi/strapi | Portal backend CMS | 2026-01-08 |
| 14 | `zeeneddie/augmented-coding-patterns` | lexler/augmented-coding-patterns | Pattern language (Gregor Riegler) | 2026-01-08 |

---

## External Tools (Not Forked)

These are referenced but not forked:

| Tool | Upstream | Purpose |
|------|----------|---------|
| `fischJan/CiRA` | fischJan/CiRA | Causality detection |
| `jimmc414/cctrace` | jimmc414/cctrace | Observability tracing |
| `alexfazio/cc-trace` | alexfazio/cc-trace | CC trace tooling |
| `terryyin/lizard` | terryyin/lizard | Code complexity analyzer |
| `geneseframework/complexity` | geneseframework/complexity | Complexity analysis |
| `dotnet/upgrade-assistant` | dotnet/upgrade-assistant | .NET migration |
| `darold/ora2pg` | darold/ora2pg | Oracle to PostgreSQL |
| `dmtolpeko/sqlines` | dmtolpeko/sqlines | SQL migration |
| `dimitri/pgloader` | dimitri/pgloader | PostgreSQL loader |
| `tree-sitter/tree-sitter` | tree-sitter/tree-sitter | Code parsing |
| `vllm-project/vllm` | vllm-project/vllm | LLM serving |
| `DLR-RM/stable-baselines3` | DLR-RM/stable-baselines3 | RL training |

---

## Sync Check Commands

### Check single repo
```bash
# Check if behind upstream
gh api repos/zeeneddie/kaibanjs --jq '.parent.full_name as $upstream |
  "Upstream: \($upstream)"'

# Compare commits
gh api repos/zeeneddie/kaibanjs/compare/main...kaiban-ai:KaibanJS:main \
  --jq '.ahead_by as $ahead | .behind_by as $behind |
  "Ahead: \($ahead), Behind: \($behind)"'
```

### Sync from upstream
```bash
# Fetch upstream and merge
cd ~/repos/repo-name
git fetch upstream
git merge upstream/main
git push origin main
```

---

## Integration Points

Each forked repo provides specific capabilities used in MarQed:

| Repo | MarQed Integration | Files Using |
|------|-------------------|-------------|
| augmented-coding-patterns | UNIFIED_IMPROVEMENT_PLAN.md | Planning, Quality Gates |
| context-engineering-intro | Validation Framework | backend/app/services/orchestration/ |
| kaibanjs | Kanban System | backend/app/services/kanban_* |
| agent-os | Standards System | backend/app/services/standards_* |
| design-os | Design OS | backend/app/services/design_os_* |
| AgentEvolver | Self Evolution | backend/app/services/agent_evolution_* |

---

## Update Log

| Date | Repo | Action | Notes |
|------|------|--------|-------|
| 2026-01-08 | All | Initial tracking | Created this document |

---

**Reminder:** Run sync check before major releases!
