# backend/app/services/github_analysis_service.py
"""
GitHub Repository Analysis Service - Week 97-98 (Fase 14).

Analyzes GitHub repositories for:
- Hot spots (high-change frequency files)
- Contributor patterns (knowledge silos)
- PR patterns (review quality, merge conflicts)
- CI/CD pipeline health
- Issue correlation with code
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
import httpx
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.devops_analysis import (
    RepositoryAnalysis,
    HotSpot,
    ContributorAnalysis,
    PRPattern,
    CIPipelineAnalysis,
    IssueCorrelation,
    RepositoryInsight,
    RepositoryPlatform,
    AnalysisDepth,
)

logger = logging.getLogger(__name__)


@dataclass
class GitHubConfig:
    """Configuration for GitHub API access."""
    token: str
    api_base: str = "https://api.github.com"
    per_page: int = 100
    timeout: float = 30.0


@dataclass
class AnalysisRequest:
    """Request for repository analysis."""
    repository_url: str
    project_id: Optional[int] = None
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    max_commits: int = 1000
    max_prs: int = 500
    include_forks: bool = False
    lookback_days: int = 365  # How far back to analyze


@dataclass
class HotSpotData:
    """Intermediate hot spot data."""
    file_path: str
    change_count: int = 0
    lines_changed: int = 0
    authors: set = field(default_factory=set)
    last_modified: Optional[datetime] = None
    bug_fixes: int = 0


class GitHubAnalysisService:
    """Service for analyzing GitHub repositories."""

    def __init__(self, db: Session, config: Optional[GitHubConfig] = None):
        self.db = db
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            if self.config and self.config.token:
                headers["Authorization"] = f"Bearer {self.config.token}"

            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=self.config.timeout if self.config else 30.0,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _parse_repo_url(self, url: str) -> Tuple[str, str]:
        """Parse repository URL to owner/repo."""
        # Handle various URL formats
        url = url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]

        # https://github.com/owner/repo
        if "github.com" in url:
            parts = url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]

        raise ValueError(f"Could not parse repository URL: {url}")

    async def analyze_repository(self, request: AnalysisRequest) -> RepositoryAnalysis:
        """
        Perform full repository analysis.

        Args:
            request: Analysis request with configuration

        Returns:
            RepositoryAnalysis with all results
        """
        owner, repo = self._parse_repo_url(request.repository_url)

        # Create analysis record
        analysis = RepositoryAnalysis(
            project_id=request.project_id,
            platform=RepositoryPlatform.GITHUB,
            repository_url=request.repository_url,
            repository_name=f"{owner}/{repo}",
            analysis_depth=request.analysis_depth,
            max_commits=request.max_commits,
            max_prs=request.max_prs,
            include_forks=request.include_forks,
            status="running",
            started_at=datetime.utcnow(),
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        try:
            # Get repository info
            repo_info = await self._get_repo_info(owner, repo)
            analysis.default_branch = repo_info.get("default_branch", "main")

            # Analyze commits and hot spots
            hot_spots_data, contributor_data = await self._analyze_commits(
                owner, repo, request.max_commits, request.lookback_days
            )

            # Store hot spots
            for file_path, data in sorted(
                hot_spots_data.items(),
                key=lambda x: x[1].change_count,
                reverse=True
            )[:100]:  # Top 100 hot spots
                hot_spot = self._create_hot_spot(analysis.id, file_path, data, len(hot_spots_data))
                self.db.add(hot_spot)

            analysis.total_commits = sum(c.change_count for c in hot_spots_data.values()) // 10  # Approximate

            # Store contributors
            for contrib_id, data in contributor_data.items():
                contributor = self._create_contributor(analysis.id, contrib_id, data)
                self.db.add(contributor)

            analysis.total_contributors = len(contributor_data)

            # Analyze PRs (if standard or full depth)
            if request.analysis_depth in (AnalysisDepth.STANDARD, AnalysisDepth.FULL):
                pr_metrics = await self._analyze_prs(owner, repo, request.max_prs, analysis.id)
                analysis.total_prs = pr_metrics["total"]
                analysis.avg_pr_review_time_hours = pr_metrics.get("avg_review_time")
                analysis.avg_pr_size_lines = pr_metrics.get("avg_size")
                analysis.merge_conflict_rate = pr_metrics.get("conflict_rate")

            # Analyze CI/CD (if full depth)
            if request.analysis_depth == AnalysisDepth.FULL:
                await self._analyze_workflows(owner, repo, analysis.id)

            # Analyze issues
            await self._analyze_issues(owner, repo, analysis.id)

            # Generate insights
            await self._generate_insights(analysis)

            analysis.status = "completed"
            analysis.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Analysis failed for {request.repository_url}: {e}")
            analysis.status = "failed"
            analysis.error_message = str(e)

        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    async def _get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information."""
        client = await self._get_client()
        url = f"{self.config.api_base if self.config else 'https://api.github.com'}/repos/{owner}/{repo}"

        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def _analyze_commits(
        self,
        owner: str,
        repo: str,
        max_commits: int,
        lookback_days: int
    ) -> Tuple[Dict[str, HotSpotData], Dict[str, Dict]]:
        """Analyze commit history for hot spots and contributors."""
        client = await self._get_client()
        base_url = self.config.api_base if self.config else "https://api.github.com"

        hot_spots: Dict[str, HotSpotData] = defaultdict(lambda: HotSpotData(file_path=""))
        contributors: Dict[str, Dict] = defaultdict(lambda: {
            "commits": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "files": set(),
            "name": None,
            "email": None,
            "first_commit": None,
            "last_commit": None,
        })

        since = datetime.utcnow() - timedelta(days=lookback_days)
        page = 1
        commits_processed = 0

        while commits_processed < max_commits:
            url = f"{base_url}/repos/{owner}/{repo}/commits"
            params = {
                "since": since.isoformat() + "Z",
                "per_page": min(100, max_commits - commits_processed),
                "page": page,
            }

            try:
                response = await client.get(url, params=params)
                if response.status_code == 404:
                    break
                response.raise_for_status()
                commits = response.json()

                if not commits:
                    break

                for commit in commits:
                    sha = commit.get("sha")
                    author = commit.get("author") or {}
                    commit_data = commit.get("commit", {})
                    author_info = commit_data.get("author", {})

                    # Track contributor
                    author_id = author.get("login") or author_info.get("email", "unknown")
                    contributors[author_id]["commits"] += 1
                    contributors[author_id]["name"] = author_info.get("name")
                    contributors[author_id]["email"] = author_info.get("email")

                    commit_date = None
                    if author_info.get("date"):
                        try:
                            commit_date = datetime.fromisoformat(author_info["date"].replace("Z", "+00:00"))
                        except:
                            pass

                    if commit_date:
                        if not contributors[author_id]["first_commit"] or commit_date < contributors[author_id]["first_commit"]:
                            contributors[author_id]["first_commit"] = commit_date
                        if not contributors[author_id]["last_commit"] or commit_date > contributors[author_id]["last_commit"]:
                            contributors[author_id]["last_commit"] = commit_date

                    # Check if this is a bug fix (based on commit message)
                    message = commit_data.get("message", "").lower()
                    is_bug_fix = any(kw in message for kw in ["fix", "bug", "issue", "error", "crash", "patch"])

                    # Get commit details for file changes
                    try:
                        detail_response = await client.get(f"{base_url}/repos/{owner}/{repo}/commits/{sha}")
                        if detail_response.status_code == 200:
                            detail = detail_response.json()
                            files = detail.get("files", [])

                            for file in files:
                                filepath = file.get("filename", "")
                                if not filepath:
                                    continue

                                if filepath not in hot_spots:
                                    hot_spots[filepath] = HotSpotData(file_path=filepath)

                                hot_spots[filepath].change_count += 1
                                hot_spots[filepath].lines_changed += file.get("changes", 0)
                                hot_spots[filepath].authors.add(author_id)
                                hot_spots[filepath].last_modified = commit_date

                                if is_bug_fix:
                                    hot_spots[filepath].bug_fixes += 1

                                contributors[author_id]["files"].add(filepath)
                                contributors[author_id]["lines_added"] += file.get("additions", 0)
                                contributors[author_id]["lines_removed"] += file.get("deletions", 0)

                    except Exception as e:
                        logger.debug(f"Could not get commit details for {sha}: {e}")

                    commits_processed += 1
                    if commits_processed >= max_commits:
                        break

                page += 1

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.warning("GitHub API rate limit reached")
                    break
                raise

        return dict(hot_spots), dict(contributors)

    def _create_hot_spot(
        self,
        analysis_id: int,
        file_path: str,
        data: HotSpotData,
        total_files: int
    ) -> HotSpot:
        """Create HotSpot record from data."""
        # Calculate scores
        change_freq_score = min(1.0, data.change_count / 50)  # 50+ changes = max score
        author_score = min(1.0, len(data.authors) / 10)  # More authors = higher complexity
        bug_score = min(1.0, data.bug_fixes / 10)

        risk_score = (change_freq_score * 0.4) + (author_score * 0.3) + (bug_score * 0.3)

        # Get file extension
        ext = None
        if "." in file_path:
            ext = file_path.rsplit(".", 1)[-1]

        return HotSpot(
            analysis_id=analysis_id,
            file_path=file_path,
            file_extension=ext,
            change_count=data.change_count,
            lines_changed_total=data.lines_changed,
            distinct_authors=len(data.authors),
            change_frequency_score=change_freq_score,
            complexity_score=author_score,
            risk_score=risk_score,
            last_modified=data.last_modified,
            associated_bugs=data.bug_fixes,
        )

    def _create_contributor(
        self,
        analysis_id: int,
        contrib_id: str,
        data: Dict
    ) -> ContributorAnalysis:
        """Create ContributorAnalysis record from data."""
        # Calculate directories and file types
        files = data.get("files", set())
        dirs = defaultdict(int)
        extensions = defaultdict(int)

        for f in files:
            parts = f.split("/")
            if len(parts) > 1:
                dirs[parts[0]] += 1
            if "." in f:
                ext = f.rsplit(".", 1)[-1]
                extensions[ext] += 1

        top_dirs = sorted(dirs.items(), key=lambda x: x[1], reverse=True)[:5]
        top_exts = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:5]

        return ContributorAnalysis(
            analysis_id=analysis_id,
            contributor_id=contrib_id,
            contributor_name=data.get("name"),
            contributor_email=data.get("email"),
            total_commits=data.get("commits", 0),
            lines_added=data.get("lines_added", 0),
            lines_removed=data.get("lines_removed", 0),
            primary_directories=[d[0] for d in top_dirs],
            primary_file_types=[e[0] for e in top_exts],
            first_commit_date=data.get("first_commit"),
            last_commit_date=data.get("last_commit"),
        )

    async def _analyze_prs(
        self,
        owner: str,
        repo: str,
        max_prs: int,
        analysis_id: int
    ) -> Dict[str, Any]:
        """Analyze pull requests."""
        client = await self._get_client()
        base_url = self.config.api_base if self.config else "https://api.github.com"

        metrics = {
            "total": 0,
            "avg_review_time": None,
            "avg_size": None,
            "conflict_rate": None,
        }

        review_times = []
        sizes = []
        conflict_count = 0
        page = 1
        prs_processed = 0

        while prs_processed < max_prs:
            url = f"{base_url}/repos/{owner}/{repo}/pulls"
            params = {
                "state": "all",
                "per_page": min(100, max_prs - prs_processed),
                "page": page,
            }

            try:
                response = await client.get(url, params=params)
                if response.status_code == 404:
                    break
                response.raise_for_status()
                prs = response.json()

                if not prs:
                    break

                for pr in prs:
                    pr_record = PRPattern(
                        analysis_id=analysis_id,
                        pr_number=pr.get("number"),
                        pr_title=pr.get("title", "")[:500],
                        pr_state=pr.get("state"),
                        additions=pr.get("additions", 0),
                        deletions=pr.get("deletions", 0),
                        changed_files=pr.get("changed_files", 0),
                    )

                    # Parse timestamps
                    if pr.get("created_at"):
                        try:
                            pr_record.created_at = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                        except:
                            pass

                    if pr.get("merged_at"):
                        try:
                            pr_record.merged_at = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                        except:
                            pass

                    if pr.get("closed_at"):
                        try:
                            pr_record.closed_at = datetime.fromisoformat(pr["closed_at"].replace("Z", "+00:00"))
                        except:
                            pass

                    # Calculate time to merge
                    if pr_record.created_at and pr_record.merged_at:
                        delta = pr_record.merged_at - pr_record.created_at
                        pr_record.time_to_merge = delta.total_seconds() / 3600  # hours
                        review_times.append(pr_record.time_to_merge)

                    # Track sizes
                    total_changes = pr.get("additions", 0) + pr.get("deletions", 0)
                    sizes.append(total_changes)

                    # Check for merge conflicts (heuristic: if merged but had many review iterations)
                    # This is a simplification - real detection would need more API calls
                    if pr.get("merged"):
                        if pr.get("review_comments", 0) > 10:
                            pr_record.had_merge_conflicts = True
                            conflict_count += 1

                    self.db.add(pr_record)
                    prs_processed += 1

                    if prs_processed >= max_prs:
                        break

                page += 1

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.warning("GitHub API rate limit reached")
                    break
                raise

        metrics["total"] = prs_processed
        if review_times:
            metrics["avg_review_time"] = sum(review_times) / len(review_times)
        if sizes:
            metrics["avg_size"] = sum(sizes) / len(sizes)
        if prs_processed > 0:
            metrics["conflict_rate"] = conflict_count / prs_processed

        return metrics

    async def _analyze_workflows(
        self,
        owner: str,
        repo: str,
        analysis_id: int
    ):
        """Analyze GitHub Actions workflows."""
        client = await self._get_client()
        base_url = self.config.api_base if self.config else "https://api.github.com"

        try:
            # Get workflows
            url = f"{base_url}/repos/{owner}/{repo}/actions/workflows"
            response = await client.get(url)

            if response.status_code != 200:
                return

            workflows = response.json().get("workflows", [])

            for workflow in workflows:
                workflow_id = workflow.get("id")
                workflow_name = workflow.get("name", "Unknown")

                # Get workflow runs
                runs_url = f"{base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
                runs_response = await client.get(runs_url, params={"per_page": 100})

                if runs_response.status_code != 200:
                    continue

                runs = runs_response.json().get("workflow_runs", [])

                total_runs = len(runs)
                successful = sum(1 for r in runs if r.get("conclusion") == "success")
                failed = sum(1 for r in runs if r.get("conclusion") == "failure")

                # Calculate durations
                durations = []
                for run in runs:
                    if run.get("run_started_at") and run.get("updated_at"):
                        try:
                            start = datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00"))
                            end = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                            duration_mins = (end - start).total_seconds() / 60
                            durations.append(duration_mins)
                        except:
                            pass

                pipeline = CIPipelineAnalysis(
                    analysis_id=analysis_id,
                    pipeline_name=workflow_name,
                    pipeline_type="github_actions",
                    total_runs=total_runs,
                    successful_runs=successful,
                    failed_runs=failed,
                    success_rate=successful / total_runs if total_runs > 0 else 0.0,
                    avg_duration_minutes=sum(durations) / len(durations) if durations else None,
                    triggers=[workflow.get("path", "")],
                    recent_runs=[
                        {
                            "id": r.get("id"),
                            "status": r.get("conclusion"),
                            "created_at": r.get("created_at"),
                        }
                        for r in runs[:10]
                    ],
                )
                self.db.add(pipeline)

        except Exception as e:
            logger.warning(f"Could not analyze workflows: {e}")

    async def _analyze_issues(
        self,
        owner: str,
        repo: str,
        analysis_id: int,
        max_issues: int = 200
    ):
        """Analyze repository issues."""
        client = await self._get_client()
        base_url = self.config.api_base if self.config else "https://api.github.com"

        page = 1
        issues_processed = 0

        while issues_processed < max_issues:
            url = f"{base_url}/repos/{owner}/{repo}/issues"
            params = {
                "state": "all",
                "per_page": min(100, max_issues - issues_processed),
                "page": page,
            }

            try:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    break

                issues = response.json()
                if not issues:
                    break

                for issue in issues:
                    # Skip PRs (they appear in issues endpoint too)
                    if issue.get("pull_request"):
                        continue

                    labels = [l.get("name") for l in issue.get("labels", [])]

                    # Determine issue type from labels
                    issue_type = "unknown"
                    if any("bug" in l.lower() for l in labels):
                        issue_type = "bug"
                    elif any("feature" in l.lower() or "enhancement" in l.lower() for l in labels):
                        issue_type = "feature"
                    elif any("doc" in l.lower() for l in labels):
                        issue_type = "documentation"

                    # Suggest work type
                    work_type = "maintenance"
                    if issue_type == "bug":
                        work_type = "bug"
                    elif issue_type == "feature":
                        work_type = "new_feature"

                    correlation = IssueCorrelation(
                        analysis_id=analysis_id,
                        issue_number=issue.get("number"),
                        issue_title=issue.get("title", "")[:500],
                        issue_type=issue_type,
                        issue_state=issue.get("state"),
                        labels=labels,
                        suggested_work_type=work_type,
                        confidence_score=0.6 if issue_type != "unknown" else 0.3,
                    )

                    if issue.get("created_at"):
                        try:
                            correlation.created_at = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                        except:
                            pass

                    if issue.get("closed_at"):
                        try:
                            correlation.closed_at = datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
                        except:
                            pass

                    self.db.add(correlation)
                    issues_processed += 1

                    if issues_processed >= max_issues:
                        break

                page += 1

            except Exception as e:
                logger.warning(f"Could not analyze issues: {e}")
                break

    async def _generate_insights(self, analysis: RepositoryAnalysis):
        """Generate high-level insights from analysis."""
        insights = []

        # Hot spot insights
        hot_spots = self.db.query(HotSpot).filter(
            HotSpot.analysis_id == analysis.id,
            HotSpot.risk_score >= 0.7
        ).all()

        if hot_spots:
            insights.append(RepositoryInsight(
                analysis_id=analysis.id,
                insight_type="risk",
                category="code_quality",
                title=f"{len(hot_spots)} High-Risk Hot Spots Detected",
                description=f"Found {len(hot_spots)} files with high change frequency and bug association. These files may benefit from refactoring or additional test coverage.",
                severity=0.8,
                evidence={"hot_spot_count": len(hot_spots)},
                affected_files=[hs.file_path for hs in hot_spots[:10]],
                recommendations=[
                    "Consider refactoring high-risk files",
                    "Add unit tests for hot spot files",
                    "Review change patterns for improvement opportunities",
                ],
            ))

        # Knowledge silo insights
        contributors = self.db.query(ContributorAnalysis).filter(
            ContributorAnalysis.analysis_id == analysis.id
        ).all()

        if contributors:
            # Find knowledge silos (contributors with exclusive access to files)
            sole_maintainers = [c for c in contributors if c.is_sole_maintainer_files > 5]
            if sole_maintainers:
                insights.append(RepositoryInsight(
                    analysis_id=analysis.id,
                    insight_type="risk",
                    category="team",
                    title="Knowledge Silos Detected",
                    description=f"Found {len(sole_maintainers)} contributors who are sole maintainers of multiple files. This creates bus factor risk.",
                    severity=0.7,
                    evidence={"sole_maintainer_count": len(sole_maintainers)},
                    recommendations=[
                        "Encourage pair programming on critical files",
                        "Document critical code paths",
                        "Cross-train team members",
                    ],
                ))

        # CI/CD insights
        pipelines = self.db.query(CIPipelineAnalysis).filter(
            CIPipelineAnalysis.analysis_id == analysis.id
        ).all()

        for pipeline in pipelines:
            if pipeline.success_rate < 0.8:
                insights.append(RepositoryInsight(
                    analysis_id=analysis.id,
                    insight_type="risk",
                    category="ci_cd",
                    title=f"Low CI Success Rate: {pipeline.pipeline_name}",
                    description=f"Pipeline '{pipeline.pipeline_name}' has a {pipeline.success_rate:.1%} success rate. This may indicate flaky tests or infrastructure issues.",
                    severity=0.6,
                    evidence={
                        "success_rate": pipeline.success_rate,
                        "total_runs": pipeline.total_runs,
                        "failed_runs": pipeline.failed_runs,
                    },
                    recommendations=[
                        "Review failed runs for common patterns",
                        "Identify and fix flaky tests",
                        "Check infrastructure stability",
                    ],
                ))

        # Save insights
        for insight in insights:
            self.db.add(insight)

    async def get_analysis(self, analysis_id: int) -> Optional[RepositoryAnalysis]:
        """Get analysis by ID."""
        return self.db.query(RepositoryAnalysis).filter(
            RepositoryAnalysis.id == analysis_id
        ).first()

    async def get_analyses_for_project(self, project_id: int) -> List[RepositoryAnalysis]:
        """Get all analyses for a project."""
        return self.db.query(RepositoryAnalysis).filter(
            RepositoryAnalysis.project_id == project_id
        ).order_by(RepositoryAnalysis.created_at.desc()).all()

    async def get_hot_spots(
        self,
        analysis_id: int,
        min_risk_score: float = 0.0,
        limit: int = 50
    ) -> List[HotSpot]:
        """Get hot spots for an analysis."""
        return self.db.query(HotSpot).filter(
            HotSpot.analysis_id == analysis_id,
            HotSpot.risk_score >= min_risk_score
        ).order_by(HotSpot.risk_score.desc()).limit(limit).all()

    async def get_insights(self, analysis_id: int) -> List[RepositoryInsight]:
        """Get insights for an analysis."""
        return self.db.query(RepositoryInsight).filter(
            RepositoryInsight.analysis_id == analysis_id
        ).order_by(RepositoryInsight.severity.desc()).all()

    def to_extraction_context(self, analysis: RepositoryAnalysis) -> Dict[str, Any]:
        """Convert analysis to context for extraction pipeline."""
        hot_spots = self.db.query(HotSpot).filter(
            HotSpot.analysis_id == analysis.id,
            HotSpot.risk_score >= 0.5
        ).order_by(HotSpot.risk_score.desc()).limit(20).all()

        insights = self.db.query(RepositoryInsight).filter(
            RepositoryInsight.analysis_id == analysis.id
        ).all()

        issues = self.db.query(IssueCorrelation).filter(
            IssueCorrelation.analysis_id == analysis.id,
            IssueCorrelation.issue_state == "open"
        ).limit(50).all()

        return {
            "repository_analysis": {
                "repository": analysis.repository_name,
                "total_commits": analysis.total_commits,
                "total_contributors": analysis.total_contributors,
                "avg_pr_review_time_hours": analysis.avg_pr_review_time_hours,
                "merge_conflict_rate": analysis.merge_conflict_rate,
                "build_success_rate": analysis.build_success_rate,
            },
            "hot_spots": [
                {
                    "file": hs.file_path,
                    "risk_score": hs.risk_score,
                    "change_count": hs.change_count,
                    "bug_fixes": hs.associated_bugs,
                }
                for hs in hot_spots
            ],
            "insights": [
                {
                    "type": i.insight_type,
                    "category": i.category,
                    "title": i.title,
                    "severity": i.severity,
                }
                for i in insights
            ],
            "open_issues": [
                {
                    "number": i.issue_number,
                    "title": i.issue_title,
                    "type": i.issue_type,
                    "suggested_work_type": i.suggested_work_type,
                }
                for i in issues
            ],
        }


def create_github_service(db: Session, token: Optional[str] = None) -> GitHubAnalysisService:
    """Factory function to create GitHub analysis service."""
    config = GitHubConfig(token=token) if token else None
    return GitHubAnalysisService(db, config)
