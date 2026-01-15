# Fase 33: DevStats Developer Metrics Dashboard

**Status:** PLANNED
**Priority:** MEDIUM-HIGH (ROI 7.0)
**Timeline:** Week 179-184
**Effort:** 152 uur (~4-5 weken)
**Dependencies:** Fase 24-E1 (Visual Dependency Graph), Fase 23.5 (Confucius Orchestrator)

---

## Executive Summary

Developer contribution analytics dashboard gebaseerd op CNCF DevStats en GrimoireLab concepten. Biedt klanten inzicht in team velocity, kennisconcentratie, en code health metrics voor legacy modernization trajecten.

**Kernwaarde voor Klanten:**
- Identificeer bus factor risico's voor kritieke modules
- Track developer productivity trends over tijd
- Correleer contributions met releases
- Ontdek bottlenecks in code review processen

---

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DEVSTATS ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌────────────────┐  │
│  │  Git Collectors  │    │  Data Enrichers │    │  Metric Store  │  │
│  │  ───────────────│    │  ──────────────│    │  ─────────────│  │
│  │  • GitHub API   │ -> │  • Identity    │ -> │  • TimeSeries  │  │
│  │  • GitLab API   │    │    Merging     │    │  • Aggregations│  │
│  │  • Bitbucket    │    │  • Commit      │    │  • Snapshots   │  │
│  │  • Local Git    │    │    Enrichment  │    │                │  │
│  └─────────────────┘    └─────────────────┘    └────────────────┘  │
│                                                        │            │
│                                                        ▼            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    ANALYTICS ENGINE                          │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │   │
│  │  │Contribution │ │  Bus Factor │ │   Release   │            │   │
│  │  │  Analyzer   │ │  Calculator │ │  Correlator │            │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘            │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │   │
│  │  │  PR Cycle   │ │ Code Churn  │ │  Activity   │            │   │
│  │  │   Analyzer  │ │  Tracker    │ │   Trends    │            │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  VISUALIZATION LAYER                         │   │
│  │                                                              │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │   │
│  │  │  D3.js      │ │  Heatmaps   │ │  Timeline   │            │   │
│  │  │  Charts     │ │  & Treemaps │ │  Views      │            │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘            │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Metrics

### 1. Developer Contribution Metrics

| Metric | Description | Insight |
|--------|-------------|---------|
| **Commits/Week** | Weekly commit frequency per developer | Activity levels |
| **Lines Changed** | LOC added/removed per period | Output volume |
| **Files Touched** | Number of unique files modified | Scope of work |
| **Commit Time Distribution** | Hour/day patterns | Working habits |
| **First Commit Age** | Days since first contribution | Team tenure |

### 2. Code Ownership Metrics (Bus Factor)

| Metric | Description | Risk Level |
|--------|-------------|------------|
| **Bus Factor** | Minimum developers to lose 50% knowledge | < 2 = HIGH RISK |
| **Ownership Concentration** | % code owned by top 1-3 developers | > 70% = HIGH RISK |
| **Knowledge Silos** | Modules with single maintainer | Any = MEDIUM RISK |
| **Cross-pollination** | Developers working across modules | Low = MEDIUM RISK |

### 3. Release Correlation Metrics

| Metric | Description | Value |
|--------|-------------|-------|
| **Contribution per Release** | % of release work per developer | Team balance |
| **Release Velocity** | Time between releases | Delivery cadence |
| **Feature Lead Time** | First commit to release | Development efficiency |
| **Hotfix Ratio** | % of commits that are hotfixes | Quality indicator |

### 4. Code Review Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **PR Open Duration** | Time from open to merge | < 2 days |
| **Review Turnaround** | Time to first review | < 8 hours |
| **Comments per PR** | Average review comments | 2-5 ideal |
| **Approval Rate** | % PRs approved first try | > 80% |

### 5. Code Health Metrics

| Metric | Description | Warning Level |
|--------|-------------|---------------|
| **Code Churn** | Lines added then deleted same release | > 30% concerning |
| **Rework Rate** | % commits fixing recent commits | > 20% concerning |
| **Dead Code Ratio** | Untouched code for 12+ months | > 40% risk |
| **Complexity Trend** | Cyclomatic complexity over time | Increasing = bad |

---

## Data Collection Layer

### GitDataCollector

```python
class GitDataCollector:
    """
    Collects contribution data from multiple Git sources.

    Supports:
    - GitHub API (REST + GraphQL)
    - GitLab API
    - Bitbucket API
    - Local git repository (fallback)
    """

    def __init__(self, config: CollectorConfig):
        self.github = GitHubClient(config.github_token)
        self.gitlab = GitLabClient(config.gitlab_token)
        self.local = LocalGitClient()

    async def collect_commits(
        self,
        repo_url: str,
        since: datetime,
        until: datetime,
        branch: str = "main"
    ) -> List[CommitData]:
        """Collect all commits in date range."""
        source = self._detect_source(repo_url)

        if source == GitSource.GITHUB:
            return await self._collect_github_commits(repo_url, since, until)
        elif source == GitSource.GITLAB:
            return await self._collect_gitlab_commits(repo_url, since, until)
        else:
            return await self._collect_local_commits(repo_url, since, until)

    async def collect_pull_requests(
        self,
        repo_url: str,
        since: datetime,
        state: PRState = PRState.ALL
    ) -> List[PullRequestData]:
        """Collect PR data with review info."""
        pass

    async def collect_releases(
        self,
        repo_url: str,
        limit: int = 50
    ) -> List[ReleaseData]:
        """Collect release/tag data."""
        pass


@dataclass
class CommitData:
    """Normalized commit data across sources."""
    sha: str
    message: str
    author_name: str
    author_email: str
    authored_date: datetime
    committer_name: str
    committer_email: str
    committed_date: datetime
    files_changed: int
    lines_added: int
    lines_deleted: int
    parent_shas: List[str]
    is_merge: bool


@dataclass
class PullRequestData:
    """Normalized PR data."""
    pr_id: int
    title: str
    author: str
    created_at: datetime
    merged_at: Optional[datetime]
    closed_at: Optional[datetime]
    state: PRState
    commits_count: int
    additions: int
    deletions: int
    reviews: List[ReviewData]
    review_comments: int
    time_to_first_review: Optional[timedelta]
    time_to_merge: Optional[timedelta]
```

### IdentityMerger

```python
class IdentityMerger:
    """
    Merges multiple git identities into single developer profiles.

    Problem: Same developer may have multiple emails:
    - john@company.com
    - john.doe@gmail.com
    - john@localhost

    Solution: Fuzzy matching + manual mapping.
    """

    def __init__(self, identity_map: Optional[Dict[str, str]] = None):
        self.identity_map = identity_map or {}
        self.fuzzy_threshold = 0.85

    def merge(
        self,
        commits: List[CommitData]
    ) -> Dict[str, DeveloperProfile]:
        """Group commits by canonical developer identity."""
        profiles: Dict[str, DeveloperProfile] = {}

        for commit in commits:
            canonical = self._get_canonical_identity(
                commit.author_name,
                commit.author_email
            )

            if canonical not in profiles:
                profiles[canonical] = DeveloperProfile(
                    canonical_name=canonical,
                    emails=set(),
                    names=set(),
                    commits=[]
                )

            profiles[canonical].emails.add(commit.author_email)
            profiles[canonical].names.add(commit.author_name)
            profiles[canonical].commits.append(commit)

        return profiles

    def _get_canonical_identity(
        self,
        name: str,
        email: str
    ) -> str:
        """Get canonical identity for name/email combination."""
        # Check explicit mapping
        if email in self.identity_map:
            return self.identity_map[email]

        # Fuzzy match against existing identities
        for canonical, emails in self._canonical_to_emails.items():
            if self._is_same_person(name, email, canonical, emails):
                return canonical

        # New identity
        return name
```

---

## Analytics Engine

### ContributionAnalyzer

```python
class ContributionAnalyzer:
    """
    Analyzes developer contribution patterns.

    Produces:
    - Per-developer statistics
    - Team-level aggregations
    - Trend analysis over time
    """

    async def analyze(
        self,
        profiles: Dict[str, DeveloperProfile],
        period: AnalysisPeriod
    ) -> ContributionReport:
        """Generate contribution analysis report."""

        developer_stats = {}
        for name, profile in profiles.items():
            stats = DeveloperStats(
                name=name,
                total_commits=len(profile.commits),
                lines_added=sum(c.lines_added for c in profile.commits),
                lines_deleted=sum(c.lines_deleted for c in profile.commits),
                files_touched=self._count_unique_files(profile.commits),
                first_commit=min(c.authored_date for c in profile.commits),
                last_commit=max(c.authored_date for c in profile.commits),
                active_days=self._count_active_days(profile.commits),
                commit_time_distribution=self._analyze_time_patterns(profile.commits),
                weekly_trend=self._calculate_weekly_trend(profile.commits, period)
            )
            developer_stats[name] = stats

        return ContributionReport(
            period=period,
            developer_stats=developer_stats,
            team_stats=self._aggregate_team_stats(developer_stats),
            top_contributors=self._rank_contributors(developer_stats),
            activity_heatmap=self._generate_heatmap(profiles)
        )


@dataclass
class DeveloperStats:
    """Statistics for a single developer."""
    name: str
    total_commits: int
    lines_added: int
    lines_deleted: int
    files_touched: int
    first_commit: datetime
    last_commit: datetime
    active_days: int
    commit_time_distribution: Dict[int, int]  # hour -> count
    weekly_trend: List[WeeklyData]

    @property
    def net_lines(self) -> int:
        return self.lines_added - self.lines_deleted

    @property
    def avg_lines_per_commit(self) -> float:
        if self.total_commits == 0:
            return 0
        return (self.lines_added + self.lines_deleted) / self.total_commits

    @property
    def churn_ratio(self) -> float:
        """High churn = lots of deletes relative to adds."""
        if self.lines_added == 0:
            return 0
        return self.lines_deleted / self.lines_added
```

### BusFactorCalculator

```python
class BusFactorCalculator:
    """
    Calculates bus factor for modules and the entire codebase.

    Bus Factor = minimum number of developers that need to leave
    before 50% of knowledge is lost.

    Based on: https://www.cncf.io/devstats/
    """

    def calculate(
        self,
        file_ownership: Dict[str, Dict[str, float]],
        threshold: float = 0.5
    ) -> BusFactorReport:
        """
        Calculate bus factor.

        Args:
            file_ownership: file -> {developer -> ownership_score}
            threshold: ownership threshold (default 50%)

        Returns:
            BusFactorReport with overall and per-module scores
        """
        # Calculate ownership concentration
        module_factors = {}
        for module, files in self._group_by_module(file_ownership).items():
            module_factors[module] = self._calculate_module_bus_factor(
                files, threshold
            )

        # Overall bus factor
        overall = self._calculate_overall_bus_factor(
            file_ownership, threshold
        )

        # Identify knowledge silos
        silos = self._identify_silos(file_ownership)

        return BusFactorReport(
            overall_bus_factor=overall,
            module_bus_factors=module_factors,
            knowledge_silos=silos,
            risk_level=self._assess_risk(overall),
            recommendations=self._generate_recommendations(
                overall, module_factors, silos
            )
        )

    def _calculate_module_bus_factor(
        self,
        files: Dict[str, Dict[str, float]],
        threshold: float
    ) -> int:
        """Calculate bus factor for a module."""
        # Aggregate ownership across files
        total_ownership = defaultdict(float)
        for file_path, developers in files.items():
            for dev, score in developers.items():
                total_ownership[dev] += score

        # Normalize
        total = sum(total_ownership.values())
        normalized = {dev: score/total for dev, score in total_ownership.items()}

        # Sort by contribution
        sorted_devs = sorted(
            normalized.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Count how many needed to reach threshold
        cumulative = 0
        count = 0
        for dev, score in sorted_devs:
            cumulative += score
            count += 1
            if cumulative >= threshold:
                break

        return count


@dataclass
class BusFactorReport:
    """Bus factor analysis results."""
    overall_bus_factor: int
    module_bus_factors: Dict[str, int]
    knowledge_silos: List[KnowledgeSilo]
    risk_level: RiskLevel  # LOW, MEDIUM, HIGH, CRITICAL
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_bus_factor": self.overall_bus_factor,
            "module_bus_factors": self.module_bus_factors,
            "knowledge_silos": [s.to_dict() for s in self.knowledge_silos],
            "risk_level": self.risk_level.value,
            "recommendations": self.recommendations
        }


@dataclass
class KnowledgeSilo:
    """A module with concentrated knowledge."""
    module_path: str
    primary_maintainer: str
    ownership_percentage: float
    files_count: int
    lines_of_code: int
    last_other_contribution: Optional[datetime]
    risk_assessment: str
```

### ReleaseCorrelator

```python
class ReleaseCorrelator:
    """
    Correlates developer contributions with releases.

    Shows who contributed what to each release.
    """

    async def correlate(
        self,
        commits: List[CommitData],
        releases: List[ReleaseData]
    ) -> ReleaseContributionReport:
        """Map commits to releases."""
        release_contributions = {}

        for release in sorted(releases, key=lambda r: r.date):
            # Get commits for this release
            release_commits = self._get_commits_for_release(
                commits, release
            )

            # Calculate per-developer contribution
            contributions = defaultdict(lambda: ReleaseContribution())
            for commit in release_commits:
                dev = commit.author_name
                contributions[dev].commits += 1
                contributions[dev].lines_added += commit.lines_added
                contributions[dev].lines_deleted += commit.lines_deleted
                contributions[dev].files.update(commit.files_changed)

            release_contributions[release.tag] = ReleaseBreakdown(
                release=release,
                contributions=dict(contributions),
                total_commits=len(release_commits),
                total_contributors=len(contributions)
            )

        return ReleaseContributionReport(
            releases=release_contributions,
            developer_release_history=self._build_developer_history(
                release_contributions
            )
        )


@dataclass
class ReleaseBreakdown:
    """Contribution breakdown for a release."""
    release: ReleaseData
    contributions: Dict[str, ReleaseContribution]
    total_commits: int
    total_contributors: int

    def get_top_contributors(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top N contributors by percentage."""
        if not self.contributions:
            return []
        sorted_contribs = sorted(
            self.contributions.items(),
            key=lambda x: x[1].commits,
            reverse=True
        )
        return [
            (name, contrib.commits / self.total_commits * 100)
            for name, contrib in sorted_contribs[:n]
        ]
```

### PRCycleAnalyzer

```python
class PRCycleAnalyzer:
    """
    Analyzes pull request cycle times and review patterns.
    """

    async def analyze(
        self,
        pull_requests: List[PullRequestData]
    ) -> PRCycleReport:
        """Analyze PR workflow metrics."""
        merged_prs = [pr for pr in pull_requests if pr.merged_at]

        return PRCycleReport(
            total_prs=len(pull_requests),
            merged_prs=len(merged_prs),
            avg_time_to_merge=self._avg_time_to_merge(merged_prs),
            avg_time_to_first_review=self._avg_first_review(pull_requests),
            avg_comments_per_pr=self._avg_comments(pull_requests),
            approval_rate=self._calculate_approval_rate(merged_prs),
            pr_size_distribution=self._analyze_size_distribution(pull_requests),
            reviewer_stats=self._analyze_reviewers(pull_requests),
            bottlenecks=self._identify_bottlenecks(pull_requests)
        )

    def _identify_bottlenecks(
        self,
        prs: List[PullRequestData]
    ) -> List[PRBottleneck]:
        """Identify bottlenecks in the review process."""
        bottlenecks = []

        # Long-running PRs
        for pr in prs:
            if pr.time_to_merge and pr.time_to_merge > timedelta(days=7):
                bottlenecks.append(PRBottleneck(
                    pr_id=pr.pr_id,
                    type=BottleneckType.LONG_RUNNING,
                    duration=pr.time_to_merge,
                    description=f"PR #{pr.pr_id} took {pr.time_to_merge.days} days to merge"
                ))

        # Slow first review
        for pr in prs:
            if pr.time_to_first_review and pr.time_to_first_review > timedelta(days=2):
                bottlenecks.append(PRBottleneck(
                    pr_id=pr.pr_id,
                    type=BottleneckType.SLOW_REVIEW,
                    duration=pr.time_to_first_review,
                    description=f"PR #{pr.pr_id} waited {pr.time_to_first_review.days} days for first review"
                ))

        return bottlenecks
```

### CodeChurnTracker

```python
class CodeChurnTracker:
    """
    Tracks code churn - lines added then quickly removed.

    High churn indicates:
    - Unstable requirements
    - Rework due to bugs
    - Experimentation
    """

    async def analyze(
        self,
        commits: List[CommitData],
        window_days: int = 30
    ) -> ChurnReport:
        """Analyze code churn patterns."""
        churn_data = defaultdict(lambda: FileChurnData())

        # Track lines per file over time
        for commit in sorted(commits, key=lambda c: c.authored_date):
            for file_change in commit.file_changes:
                file_data = churn_data[file_change.path]
                file_data.add_change(
                    date=commit.authored_date,
                    added=file_change.lines_added,
                    deleted=file_change.lines_deleted
                )

        # Calculate churn within window
        results = {}
        for file_path, file_data in churn_data.items():
            churn = file_data.calculate_churn(window_days)
            results[file_path] = churn

        return ChurnReport(
            file_churn=results,
            high_churn_files=self._identify_high_churn(results),
            churn_by_developer=self._churn_per_developer(commits, window_days),
            overall_churn_rate=self._calculate_overall_rate(results),
            trend=self._calculate_trend(commits, window_days)
        )


@dataclass
class ChurnReport:
    """Code churn analysis results."""
    file_churn: Dict[str, FileChurnMetrics]
    high_churn_files: List[HighChurnFile]
    churn_by_developer: Dict[str, float]
    overall_churn_rate: float
    trend: ChurnTrend  # INCREASING, STABLE, DECREASING

    def get_risk_assessment(self) -> str:
        if self.overall_churn_rate > 0.4:
            return "HIGH - Significant rework detected. Review requirements clarity."
        elif self.overall_churn_rate > 0.25:
            return "MEDIUM - Moderate churn. May indicate iterative development."
        else:
            return "LOW - Healthy churn levels."
```

---

## Visualization Layer

### D3Visualizations

```python
class D3Visualizations:
    """
    Generates D3.js compatible visualization data.
    """

    def contribution_heatmap(
        self,
        contribution_data: ContributionReport
    ) -> D3HeatmapData:
        """
        Generate GitHub-style contribution heatmap.

        Output format for D3.js calendar heatmap.
        """
        return D3HeatmapData(
            data=[
                {
                    "date": date.isoformat(),
                    "count": count,
                    "level": self._get_level(count)
                }
                for date, count in contribution_data.daily_counts.items()
            ],
            color_scale=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
        )

    def bus_factor_treemap(
        self,
        bus_factor_data: BusFactorReport
    ) -> D3TreemapData:
        """
        Generate treemap showing code ownership.

        Size = LOC, Color = Bus factor risk
        """
        return D3TreemapData(
            name="codebase",
            children=[
                {
                    "name": module,
                    "value": data.lines_of_code,
                    "bus_factor": data.bus_factor,
                    "risk_color": self._risk_to_color(data.risk_level),
                    "primary_owner": data.primary_maintainer,
                    "children": self._build_file_nodes(data.files)
                }
                for module, data in bus_factor_data.module_bus_factors.items()
            ]
        )

    def release_timeline(
        self,
        release_data: ReleaseContributionReport
    ) -> D3TimelineData:
        """
        Generate release timeline with contribution bars.
        """
        return D3TimelineData(
            releases=[
                {
                    "tag": release.tag,
                    "date": release.date.isoformat(),
                    "contributors": [
                        {
                            "name": name,
                            "commits": contrib.commits,
                            "percentage": contrib.commits / release.total_commits * 100
                        }
                        for name, contrib in release.contributions.items()
                    ]
                }
                for tag, release in release_data.releases.items()
            ]
        )

    def pr_funnel(
        self,
        pr_data: PRCycleReport
    ) -> D3FunnelData:
        """
        Generate PR funnel visualization.

        Shows: Created -> Reviewed -> Approved -> Merged
        """
        return D3FunnelData(
            stages=[
                {"name": "Created", "count": pr_data.total_prs},
                {"name": "Reviewed", "count": pr_data.reviewed_prs},
                {"name": "Approved", "count": pr_data.approved_prs},
                {"name": "Merged", "count": pr_data.merged_prs}
            ],
            conversion_rates=self._calculate_conversion_rates(pr_data)
        )
```

---

## API Endpoints

### DevStats API

```python
# backend/app/api/routes/devstats.py

router = APIRouter(prefix="/api/devstats", tags=["DevStats"])


@router.post("/collect")
async def collect_data(
    request: CollectRequest,
    service: DevStatsService = Depends()
) -> CollectResponse:
    """
    Collect developer statistics from repository.

    Body:
    - repo_url: Git repository URL
    - since: Start date (optional, default: 1 year ago)
    - until: End date (optional, default: now)
    - branch: Branch to analyze (default: main)
    """
    pass


@router.get("/contributions/{repo_id}")
async def get_contributions(
    repo_id: str,
    period: Period = Query(default=Period.LAST_90_DAYS),
    service: DevStatsService = Depends()
) -> ContributionReport:
    """Get contribution statistics for repository."""
    pass


@router.get("/bus-factor/{repo_id}")
async def get_bus_factor(
    repo_id: str,
    threshold: float = Query(default=0.5),
    service: DevStatsService = Depends()
) -> BusFactorReport:
    """Calculate bus factor for repository."""
    pass


@router.get("/releases/{repo_id}")
async def get_release_contributions(
    repo_id: str,
    limit: int = Query(default=10),
    service: DevStatsService = Depends()
) -> ReleaseContributionReport:
    """Get contribution breakdown per release."""
    pass


@router.get("/pr-cycle/{repo_id}")
async def get_pr_cycle(
    repo_id: str,
    period: Period = Query(default=Period.LAST_90_DAYS),
    service: DevStatsService = Depends()
) -> PRCycleReport:
    """Get PR cycle time analysis."""
    pass


@router.get("/churn/{repo_id}")
async def get_code_churn(
    repo_id: str,
    window_days: int = Query(default=30),
    service: DevStatsService = Depends()
) -> ChurnReport:
    """Get code churn analysis."""
    pass


@router.get("/visualizations/{repo_id}/{viz_type}")
async def get_visualization(
    repo_id: str,
    viz_type: VizType,
    service: DevStatsService = Depends()
) -> D3VisualizationData:
    """
    Get D3.js compatible visualization data.

    viz_type: heatmap, treemap, timeline, funnel, network
    """
    pass


@router.get("/dashboard/{repo_id}")
async def get_dashboard(
    repo_id: str,
    service: DevStatsService = Depends()
) -> DashboardData:
    """Get complete dashboard data for repository."""
    return DashboardData(
        contributions=await service.get_contributions(repo_id),
        bus_factor=await service.get_bus_factor(repo_id),
        pr_cycle=await service.get_pr_cycle(repo_id),
        churn=await service.get_churn(repo_id),
        visualizations={
            "heatmap": await service.get_viz(repo_id, VizType.HEATMAP),
            "treemap": await service.get_viz(repo_id, VizType.TREEMAP),
            "timeline": await service.get_viz(repo_id, VizType.TIMELINE)
        }
    )
```

---

## Implementation Plan

### Week 1: Data Collection (32 uur)

| Task | Hours | Description |
|------|-------|-------------|
| GitDataCollector | 12 | GitHub/GitLab API integration |
| IdentityMerger | 6 | Developer identity resolution |
| Data models | 6 | CommitData, PRData, ReleaseData |
| Local git fallback | 4 | gitpython integration |
| Unit tests | 4 | 20+ tests |

### Week 2: Analytics Engine (40 uur)

| Task | Hours | Description |
|------|-------|-------------|
| ContributionAnalyzer | 8 | Per-developer stats |
| BusFactorCalculator | 10 | Ownership analysis |
| ReleaseCorrelator | 8 | Release-commit mapping |
| PRCycleAnalyzer | 8 | PR workflow metrics |
| CodeChurnTracker | 6 | Churn detection |

### Week 3: Visualizations & API (40 uur)

| Task | Hours | Description |
|------|-------|-------------|
| D3Visualizations | 16 | Heatmap, treemap, timeline, funnel |
| API endpoints | 12 | REST API with async handlers |
| Dashboard aggregation | 8 | Combined dashboard endpoint |
| Caching layer | 4 | Redis caching for expensive ops |

### Week 4: Frontend & Integration (24 uur)

| Task | Hours | Description |
|------|-------|-------------|
| React dashboard | 12 | D3.js integration |
| Confucius integration | 4 | Workflow embedding |
| Export formats | 4 | PDF, Excel export |
| Documentation | 4 | API docs, examples |

### Week 5: Testing & Polish (16 uur)

| Task | Hours | Description |
|------|-------|-------------|
| E2E tests | 6 | Full workflow tests |
| Performance tuning | 6 | Large repo optimization |
| Bug fixes | 4 | Based on testing |

---

## Integration with Existing Platform

### Services Used

| Service | Integration |
|---------|-------------|
| `DependencyGraphService` | File ownership mapping |
| `ComplexityAnalyzer` | Complexity trend data |
| `ContextOptimizer` | Token-efficient API responses |
| `QualityGateEvaluator` | Quality trend correlation |
| `RiskHeatMapService` | Risk visualization overlay |

### Data Flow

```
Legacy Quickscan (Fase 24-A1)
         │
         ▼
DevStats Collection ──► Bus Factor Analysis
         │                      │
         ▼                      ▼
Contribution Report ◄──► Risk Heat Map (Fase 24-A4)
         │
         ▼
Customer Dashboard
```

---

## Success Criteria

### Functional Requirements

- [ ] Collect data from GitHub, GitLab, and local git
- [ ] Calculate bus factor per module with < 5% error
- [ ] Generate contribution heatmaps for 12-month periods
- [ ] Analyze PR cycle times with bottleneck detection
- [ ] Track code churn with trend analysis
- [ ] Export all visualizations as D3.js compatible JSON

### Quality Gates

- [ ] 50+ unit tests passing
- [ ] < 30s analysis for repos with 10K commits
- [ ] < 5MB memory per 1K commits processed
- [ ] API response time < 2s for dashboard

### Performance Metrics

| Metric | Target |
|--------|--------|
| Commit collection rate | 1000 commits/second |
| Analysis time (10K commits) | < 30 seconds |
| Dashboard load time | < 3 seconds |
| Memory usage | < 500MB for 100K commits |

---

## References

### Inspiration Sources

- [CNCF DevStats](https://devstats.cncf.io/) - 27+ Grafana dashboards
- [GrimoireLab](https://chaoss.github.io/grimoirelab/) - CHAOSS project, 30+ data sources
- [RepoSense](https://reposense.org/) - NUS contribution analyzer
- [Git Fame](https://github.com/casperdcl/git-fame) - Simple contribution stats

### Best Practices

- [CHAOSS Metrics](https://chaoss.community/metrics/) - Open source community health metrics
- [Developer Velocity](https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/developer-velocity-how-software-excellence-fuels-business-performance) - McKinsey research

---

*Created: Week 158 (2026-01-15)*
*Author: Claude Code*
