# backend/app/services/azure_devops_service.py
"""
Azure DevOps Analysis Service - Week 97-98 (Fase 14).

Provides repository intelligence from Azure DevOps for extraction pipeline enrichment.
"""

import asyncio
import base64
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from collections import defaultdict

import httpx
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


@dataclass
class AzureDevOpsConfig:
    """Configuration for Azure DevOps API access."""
    personal_access_token: str
    organization: str
    project: str
    repository: Optional[str] = None
    api_version: str = "7.0"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class AzureAnalysisRequest:
    """Request parameters for Azure DevOps analysis."""
    repository_url: str
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    max_commits: int = 1000
    max_pull_requests: int = 500
    include_pipelines: bool = True
    include_work_items: bool = True
    project_id: Optional[int] = None


class AzureDevOpsService:
    """
    Service for analyzing Azure DevOps repositories.

    Provides:
    - Commit history and hot spot analysis
    - Contributor/knowledge silo detection
    - Pull request pattern analysis
    - Azure Pipelines health metrics
    - Work item correlation
    - Repository insights generation
    """

    def __init__(self, config: AzureDevOpsConfig, db: Session):
        self.config = config
        self.db = db
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def base_url(self) -> str:
        """Azure DevOps API base URL."""
        return f"https://dev.azure.com/{self.config.organization}/{self.config.project}/_apis"

    @property
    def auth_header(self) -> Dict[str, str]:
        """Basic auth header for Azure DevOps API."""
        credentials = base64.b64encode(
            f":{self.config.personal_access_token}".encode()
        ).decode()
        return {"Authorization": f"Basic {credentials}"}

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers=self.auth_header
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _api_get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make GET request to Azure DevOps API."""
        client = await self._get_client()

        if params is None:
            params = {}
        params["api-version"] = self.config.api_version

        url = f"{self.base_url}/{endpoint}"

        for attempt in range(self.config.max_retries):
            try:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return {}
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    response.raise_for_status()

            except httpx.TimeoutException:
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(1)

        return {}

    @staticmethod
    def parse_azure_url(url: str) -> Dict[str, str]:
        """
        Parse Azure DevOps repository URL.

        Supports formats:
        - https://dev.azure.com/{org}/{project}/_git/{repo}
        - https://{org}.visualstudio.com/{project}/_git/{repo}
        - {org}/{project}/{repo} (shorthand)
        """
        # Standard dev.azure.com format
        match = re.match(
            r'https?://dev\.azure\.com/([^/]+)/([^/]+)/_git/([^/]+)',
            url
        )
        if match:
            return {
                "organization": match.group(1),
                "project": match.group(2),
                "repository": match.group(3)
            }

        # Legacy visualstudio.com format
        match = re.match(
            r'https?://([^.]+)\.visualstudio\.com/([^/]+)/_git/([^/]+)',
            url
        )
        if match:
            return {
                "organization": match.group(1),
                "project": match.group(2),
                "repository": match.group(3)
            }

        # Shorthand format
        parts = url.strip("/").split("/")
        if len(parts) >= 3:
            return {
                "organization": parts[0],
                "project": parts[1],
                "repository": parts[2]
            }

        raise ValueError(f"Invalid Azure DevOps URL format: {url}")

    async def analyze_repository(
        self,
        request: AzureAnalysisRequest
    ) -> RepositoryAnalysis:
        """
        Perform full repository analysis.

        Returns:
            RepositoryAnalysis with all collected metrics
        """
        # Parse URL
        url_parts = self.parse_azure_url(request.repository_url)

        # Update config with parsed values
        self.config.organization = url_parts["organization"]
        self.config.project = url_parts["project"]
        self.config.repository = url_parts["repository"]

        # Create analysis record
        analysis = RepositoryAnalysis(
            project_id=request.project_id,
            platform=RepositoryPlatform.AZURE_DEVOPS,
            repository_url=request.repository_url,
            repository_name=url_parts["repository"],
            default_branch="main",  # Will be updated
            analysis_depth=request.analysis_depth,
            max_commits=request.max_commits,
            max_prs=request.max_pull_requests,
            status="running",
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        try:
            # Get repository info
            repo_info = await self._get_repository_info()
            if repo_info:
                analysis.default_branch = repo_info.get("defaultBranch", "main").replace("refs/heads/", "")

            # Analyze commits and build hot spots
            await self._analyze_commits(analysis, request.max_commits)

            # Analyze pull requests
            await self._analyze_pull_requests(analysis, request.max_pull_requests)

            # Analyze pipelines (if enabled and depth allows)
            if request.include_pipelines and request.analysis_depth in [
                AnalysisDepth.STANDARD, AnalysisDepth.FULL
            ]:
                await self._analyze_pipelines(analysis)

            # Analyze work items (if enabled)
            if request.include_work_items:
                await self._analyze_work_items(analysis)

            # Generate insights
            await self._generate_insights(analysis)

            # Update summary metrics
            analysis.status = "completed"
            analysis.completed_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(analysis)

            return analysis

        except Exception as e:
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise
        finally:
            await self.close()

    async def _get_repository_info(self) -> Dict[str, Any]:
        """Get repository metadata."""
        return await self._api_get(f"git/repositories/{self.config.repository}")

    async def _analyze_commits(self, analysis: RepositoryAnalysis, max_commits: int):
        """Analyze commit history for hot spots and contributors."""
        file_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "change_count": 0,
            "lines_changed": 0,
            "authors": set(),
            "last_modified": None,
            "bug_fixes": 0
        })

        contributor_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "name": "",
            "email": "",
            "commits": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "directories": defaultdict(int),
            "file_types": defaultdict(int),
            "first_commit": None,
            "last_commit": None
        })

        # Fetch commits
        skip = 0
        batch_size = 100
        total_commits = 0

        while total_commits < max_commits:
            params = {
                "searchCriteria.itemVersion.version": analysis.default_branch,
                "$skip": skip,
                "$top": min(batch_size, max_commits - total_commits)
            }

            result = await self._api_get(
                f"git/repositories/{self.config.repository}/commits",
                params=params
            )

            commits = result.get("value", [])
            if not commits:
                break

            for commit in commits:
                commit_id = commit.get("commitId", "")
                author = commit.get("author", {})
                author_email = author.get("email", "unknown")
                author_name = author.get("name", "Unknown")
                commit_date = commit.get("author", {}).get("date")
                comment = commit.get("comment", "").lower()

                # Parse commit date
                if commit_date:
                    try:
                        commit_dt = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
                    except:
                        commit_dt = datetime.now(timezone.utc)
                else:
                    commit_dt = datetime.now(timezone.utc)

                # Check if bug fix
                is_bug_fix = any(kw in comment for kw in ["fix", "bug", "issue", "error", "patch"])

                # Update contributor stats
                contrib = contributor_stats[author_email]
                contrib["name"] = author_name
                contrib["email"] = author_email
                contrib["commits"] += 1

                if contrib["first_commit"] is None or commit_dt < contrib["first_commit"]:
                    contrib["first_commit"] = commit_dt
                if contrib["last_commit"] is None or commit_dt > contrib["last_commit"]:
                    contrib["last_commit"] = commit_dt

                # Get commit changes
                changes_result = await self._api_get(
                    f"git/repositories/{self.config.repository}/commits/{commit_id}/changes"
                )

                for change in changes_result.get("changes", []):
                    item = change.get("item", {})
                    path = item.get("path", "")

                    if not path or item.get("gitObjectType") != "blob":
                        continue

                    # Update file stats
                    file_stats[path]["change_count"] += 1
                    file_stats[path]["authors"].add(author_email)

                    if file_stats[path]["last_modified"] is None or commit_dt > file_stats[path]["last_modified"]:
                        file_stats[path]["last_modified"] = commit_dt

                    if is_bug_fix:
                        file_stats[path]["bug_fixes"] += 1

                    # Estimate lines changed (Azure DevOps doesn't always provide this)
                    change_type = change.get("changeType", "")
                    if change_type in ["add", "edit"]:
                        file_stats[path]["lines_changed"] += 50  # Estimate

                    # Update contributor focus areas
                    dir_path = "/".join(path.split("/")[:-1]) or "/"
                    contrib["directories"][dir_path] += 1

                    ext = path.split(".")[-1] if "." in path else "no_ext"
                    contrib["file_types"][ext] += 1

                total_commits += 1

            skip += batch_size

            # Avoid excessive API calls
            await asyncio.sleep(0.1)

        analysis.total_commits = total_commits
        analysis.total_contributors = len(contributor_stats)

        # Calculate hot spots
        if file_stats:
            max_changes = max(f["change_count"] for f in file_stats.values())
            max_authors = max(len(f["authors"]) for f in file_stats.values())

            for path, stats in file_stats.items():
                freq_score = stats["change_count"] / max_changes if max_changes > 0 else 0
                complexity = len(stats["authors"]) / max_authors if max_authors > 0 else 0

                # Risk score: high change frequency + multiple authors + bug fixes
                bug_factor = min(stats["bug_fixes"] / 5, 1.0)  # Cap at 5 bugs
                risk_score = (freq_score * 0.4) + (complexity * 0.3) + (bug_factor * 0.3)

                ext = path.split(".")[-1] if "." in path else None

                hot_spot = HotSpot(
                    analysis_id=analysis.id,
                    file_path=path,
                    file_extension=ext,
                    change_count=stats["change_count"],
                    lines_changed_total=stats["lines_changed"],
                    distinct_authors=len(stats["authors"]),
                    change_frequency_score=freq_score,
                    complexity_score=complexity,
                    risk_score=risk_score,
                    last_modified=stats["last_modified"],
                    associated_bugs=stats["bug_fixes"]
                )
                self.db.add(hot_spot)

        # Save contributor analyses
        total_commits_all = sum(c["commits"] for c in contributor_stats.values())

        for email, stats in contributor_stats.items():
            bus_factor = stats["commits"] / total_commits_all if total_commits_all > 0 else 0

            # Sort directories and file types by frequency
            top_dirs = sorted(stats["directories"].items(), key=lambda x: -x[1])[:5]
            top_types = sorted(stats["file_types"].items(), key=lambda x: -x[1])[:5]

            contributor = ContributorAnalysis(
                analysis_id=analysis.id,
                contributor_id=email,
                contributor_name=stats["name"],
                contributor_email=stats["email"],
                total_commits=stats["commits"],
                lines_added=stats["lines_added"],
                lines_removed=stats["lines_removed"],
                primary_directories=[d[0] for d in top_dirs],
                primary_file_types=[t[0] for t in top_types],
                bus_factor_contribution=bus_factor,
                first_commit_date=stats["first_commit"],
                last_commit_date=stats["last_commit"]
            )
            self.db.add(contributor)

        self.db.commit()

    async def _analyze_pull_requests(
        self,
        analysis: RepositoryAnalysis,
        max_prs: int
    ):
        """Analyze pull request patterns."""
        skip = 0
        batch_size = 100
        total_prs = 0

        pr_metrics = {
            "review_times": [],
            "merge_times": [],
            "sizes": [],
            "conflicts": 0,
            "rework": 0
        }

        while total_prs < max_prs:
            params = {
                "searchCriteria.status": "all",
                "$skip": skip,
                "$top": min(batch_size, max_prs - total_prs)
            }

            result = await self._api_get(
                f"git/repositories/{self.config.repository}/pullrequests",
                params=params
            )

            prs = result.get("value", [])
            if not prs:
                break

            for pr in prs:
                pr_id = pr.get("pullRequestId")

                # Get PR threads for review analysis
                threads_result = await self._api_get(
                    f"git/repositories/{self.config.repository}/pullRequests/{pr_id}/threads"
                )
                threads = threads_result.get("value", [])

                # Count reviews and comments
                review_count = 0
                comment_count = 0
                change_requests = 0
                approvals = 0
                first_review_time = None

                for thread in threads:
                    status = thread.get("status", "")
                    comments = thread.get("comments", [])

                    if status == "active":
                        change_requests += 1
                    elif status == "fixed":
                        approvals += 1

                    comment_count += len(comments)

                    # Track first review time
                    for comment in comments:
                        if comment.get("commentType") == "text":
                            review_count += 1
                            pub_date = comment.get("publishedDate")
                            if pub_date and first_review_time is None:
                                try:
                                    first_review_time = datetime.fromisoformat(
                                        pub_date.replace("Z", "+00:00")
                                    )
                                except:
                                    pass

                # Parse dates
                created_at = None
                merged_at = None
                closed_at = None

                if pr.get("creationDate"):
                    try:
                        created_at = datetime.fromisoformat(
                            pr["creationDate"].replace("Z", "+00:00")
                        )
                    except:
                        pass

                if pr.get("closedDate"):
                    try:
                        closed_at = datetime.fromisoformat(
                            pr["closedDate"].replace("Z", "+00:00")
                        )
                    except:
                        pass

                # Check if merged
                if pr.get("status") == "completed":
                    merged_at = closed_at

                # Calculate time metrics
                time_to_first_review = None
                time_to_merge = None

                if created_at and first_review_time:
                    time_to_first_review = (first_review_time - created_at).total_seconds() / 3600
                    pr_metrics["review_times"].append(time_to_first_review)

                if created_at and merged_at:
                    time_to_merge = (merged_at - created_at).total_seconds() / 3600
                    pr_metrics["merge_times"].append(time_to_merge)

                # Check for merge conflicts (approximation)
                had_conflicts = any(
                    "conflict" in str(t.get("comments", [])).lower()
                    for t in threads
                )
                if had_conflicts:
                    pr_metrics["conflicts"] += 1

                # Check for rework (changes after review)
                required_rework = change_requests > 0
                if required_rework:
                    pr_metrics["rework"] += 1

                pr_pattern = PRPattern(
                    analysis_id=analysis.id,
                    pr_number=pr_id,
                    pr_title=pr.get("title", "")[:500],
                    pr_state=pr.get("status", "unknown"),
                    additions=0,  # Not easily available in Azure DevOps API
                    deletions=0,
                    changed_files=0,
                    review_count=review_count,
                    approval_count=approvals,
                    change_request_count=change_requests,
                    comment_count=comment_count,
                    time_to_first_review=time_to_first_review,
                    time_to_merge=time_to_merge,
                    had_merge_conflicts=had_conflicts,
                    had_ci_failures=False,  # Would need build API
                    required_rework=required_rework,
                    created_at=created_at,
                    merged_at=merged_at,
                    closed_at=closed_at
                )
                self.db.add(pr_pattern)

                total_prs += 1

            skip += batch_size
            await asyncio.sleep(0.1)

        # Update analysis summary
        analysis.total_prs = total_prs

        if pr_metrics["review_times"]:
            analysis.avg_pr_review_time_hours = sum(pr_metrics["review_times"]) / len(pr_metrics["review_times"])

        if total_prs > 0:
            analysis.merge_conflict_rate = pr_metrics["conflicts"] / total_prs

        self.db.commit()

    async def _analyze_pipelines(self, analysis: RepositoryAnalysis):
        """Analyze Azure Pipelines."""
        # Get pipeline definitions
        result = await self._api_get("pipelines")
        pipelines = result.get("value", [])

        for pipeline in pipelines[:20]:  # Limit to 20 pipelines
            pipeline_id = pipeline.get("id")
            pipeline_name = pipeline.get("name", "Unknown")

            # Get recent runs
            runs_result = await self._api_get(
                f"pipelines/{pipeline_id}/runs",
                params={"$top": 50}
            )
            runs = runs_result.get("value", [])

            if not runs:
                continue

            # Calculate metrics
            total_runs = len(runs)
            successful = sum(1 for r in runs if r.get("result") == "succeeded")
            failed = sum(1 for r in runs if r.get("result") == "failed")

            durations = []
            for run in runs:
                if run.get("createdDate") and run.get("finishedDate"):
                    try:
                        created = datetime.fromisoformat(
                            run["createdDate"].replace("Z", "+00:00")
                        )
                        finished = datetime.fromisoformat(
                            run["finishedDate"].replace("Z", "+00:00")
                        )
                        duration_mins = (finished - created).total_seconds() / 60
                        durations.append(duration_mins)
                    except:
                        pass

            avg_duration = sum(durations) / len(durations) if durations else None
            p95_duration = sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 10 else None

            # Build recent runs summary
            recent_runs_summary = [
                {
                    "id": r.get("id"),
                    "result": r.get("result"),
                    "state": r.get("state")
                }
                for r in runs[:10]
            ]

            pipeline_analysis = CIPipelineAnalysis(
                analysis_id=analysis.id,
                pipeline_name=pipeline_name,
                pipeline_type="azure_pipeline",
                total_runs=total_runs,
                successful_runs=successful,
                failed_runs=failed,
                avg_duration_minutes=avg_duration,
                p95_duration_minutes=p95_duration,
                success_rate=successful / total_runs if total_runs > 0 else 0,
                flaky_test_count=0,  # Would need test results API
                triggers=pipeline.get("configuration", {}).get("triggers", []),
                stages=[],  # Would need pipeline YAML parsing
                recent_runs=recent_runs_summary
            )
            self.db.add(pipeline_analysis)

        # Update build success rate
        all_pipelines = analysis.ci_pipelines
        if all_pipelines:
            total_success = sum(p.successful_runs for p in all_pipelines)
            total_runs = sum(p.total_runs for p in all_pipelines)
            analysis.build_success_rate = total_success / total_runs if total_runs > 0 else None

        self.db.commit()

    async def _analyze_work_items(self, analysis: RepositoryAnalysis):
        """Analyze work items (bugs, features, etc.)."""
        # Query work items linked to repository
        wiql_query = {
            "query": f"""
                SELECT [System.Id], [System.Title], [System.WorkItemType],
                       [System.State], [System.Tags], [Microsoft.VSTS.Common.Priority]
                FROM WorkItems
                WHERE [System.TeamProject] = '{self.config.project}'
                AND [System.State] <> 'Removed'
                ORDER BY [System.CreatedDate] DESC
            """
        }

        # Note: WIQL endpoint is different
        wiql_url = f"https://dev.azure.com/{self.config.organization}/{self.config.project}/_apis/wit/wiql"

        client = await self._get_client()

        try:
            response = await client.post(
                wiql_url,
                params={"api-version": self.config.api_version},
                json=wiql_query
            )

            if response.status_code != 200:
                return

            result = response.json()
            work_item_refs = result.get("workItems", [])[:200]  # Limit to 200

            if not work_item_refs:
                return

            # Get work item details in batches
            ids = [wi["id"] for wi in work_item_refs]

            for i in range(0, len(ids), 50):
                batch_ids = ids[i:i+50]

                details_result = await self._api_get(
                    "wit/workitems",
                    params={
                        "ids": ",".join(map(str, batch_ids)),
                        "$expand": "relations"
                    }
                )

                work_items = details_result.get("value", [])

                for wi in work_items:
                    fields = wi.get("fields", {})

                    # Determine work type
                    wi_type = fields.get("System.WorkItemType", "").lower()
                    if "bug" in wi_type:
                        suggested_work_type = "bug"
                    elif "feature" in wi_type or "user story" in wi_type:
                        suggested_work_type = "feature"
                    else:
                        suggested_work_type = "enhancement"

                    # Extract linked PRs
                    linked_prs = []
                    for relation in wi.get("relations", []):
                        if "pullRequest" in relation.get("rel", ""):
                            linked_prs.append(relation.get("url", ""))

                    # Parse dates
                    created_at = None
                    closed_at = None

                    if fields.get("System.CreatedDate"):
                        try:
                            created_at = datetime.fromisoformat(
                                fields["System.CreatedDate"].replace("Z", "+00:00")
                            )
                        except:
                            pass

                    if fields.get("Microsoft.VSTS.Common.ClosedDate"):
                        try:
                            closed_at = datetime.fromisoformat(
                                fields["Microsoft.VSTS.Common.ClosedDate"].replace("Z", "+00:00")
                            )
                        except:
                            pass

                    # Get tags/labels
                    tags_str = fields.get("System.Tags", "")
                    labels = [t.strip() for t in tags_str.split(";")] if tags_str else []

                    correlation = IssueCorrelation(
                        analysis_id=analysis.id,
                        issue_number=wi["id"],
                        issue_title=fields.get("System.Title", "")[:500],
                        issue_type=wi_type,
                        issue_state=fields.get("System.State", ""),
                        labels=labels,
                        priority=str(fields.get("Microsoft.VSTS.Common.Priority", "")),
                        linked_pr_numbers=linked_prs,
                        affected_files=[],
                        suggested_epic=None,
                        suggested_work_type=suggested_work_type,
                        confidence_score=0.7,
                        created_at=created_at,
                        closed_at=closed_at
                    )
                    self.db.add(correlation)

            analysis.total_issues = len(work_item_refs)
            self.db.commit()

        except Exception:
            # Work item analysis is optional
            pass

    async def _generate_insights(self, analysis: RepositoryAnalysis):
        """Generate high-level repository insights."""
        insights = []

        # Hot spot insights
        high_risk_files = [
            hs for hs in analysis.hot_spots
            if hs.risk_score > 0.7
        ]

        if high_risk_files:
            insights.append(RepositoryInsight(
                analysis_id=analysis.id,
                insight_type="risk",
                category="code_quality",
                title="High-Risk Files Detected",
                description=f"Found {len(high_risk_files)} files with high change frequency and multiple contributors. These files may benefit from refactoring or additional test coverage.",
                severity=0.8,
                evidence={
                    "file_count": len(high_risk_files),
                    "top_files": [f.file_path for f in high_risk_files[:5]]
                },
                affected_files=[f.file_path for f in high_risk_files],
                recommendations=[
                    "Consider breaking down large files",
                    "Add comprehensive test coverage",
                    "Review code ownership"
                ]
            ))

        # Knowledge silo insights
        sole_maintainers = [
            c for c in analysis.contributors
            if c.is_sole_maintainer_files > 5
        ]

        if sole_maintainers:
            insights.append(RepositoryInsight(
                analysis_id=analysis.id,
                insight_type="risk",
                category="team",
                title="Knowledge Silos Detected",
                description=f"Found {len(sole_maintainers)} contributors who are sole maintainers of multiple files. This creates bus factor risk.",
                severity=0.7,
                evidence={
                    "contributors": [
                        {
                            "name": c.contributor_name,
                            "sole_files": c.is_sole_maintainer_files
                        }
                        for c in sole_maintainers[:5]
                    ]
                },
                affected_files=[],
                recommendations=[
                    "Encourage pair programming",
                    "Implement code review requirements",
                    "Document critical systems"
                ]
            ))

        # PR velocity insights
        if analysis.avg_pr_review_time_hours:
            if analysis.avg_pr_review_time_hours > 48:
                insights.append(RepositoryInsight(
                    analysis_id=analysis.id,
                    insight_type="recommendation",
                    category="process",
                    title="Slow PR Review Times",
                    description=f"Average PR review time is {analysis.avg_pr_review_time_hours:.1f} hours. Consider implementing review SLAs.",
                    severity=0.6,
                    evidence={
                        "avg_review_time_hours": analysis.avg_pr_review_time_hours
                    },
                    affected_files=[],
                    recommendations=[
                        "Set review time SLAs",
                        "Use automated reviewers for simple changes",
                        "Balance reviewer workload"
                    ]
                ))

        # CI/CD insights
        if analysis.build_success_rate and analysis.build_success_rate < 0.8:
            insights.append(RepositoryInsight(
                analysis_id=analysis.id,
                insight_type="risk",
                category="ci_cd",
                title="Low Build Success Rate",
                description=f"Build success rate is {analysis.build_success_rate*100:.1f}%. This may indicate flaky tests or infrastructure issues.",
                severity=0.7,
                evidence={
                    "success_rate": analysis.build_success_rate
                },
                affected_files=[],
                recommendations=[
                    "Identify and fix flaky tests",
                    "Review recent CI configuration changes",
                    "Monitor infrastructure health"
                ]
            ))

        for insight in insights:
            self.db.add(insight)

        self.db.commit()

    def to_extraction_context(self, analysis: RepositoryAnalysis) -> Dict[str, Any]:
        """
        Convert analysis results to extraction pipeline context.

        Returns dict suitable for enriching extraction sessions.
        """
        return {
            "repository": {
                "platform": "azure_devops",
                "url": analysis.repository_url,
                "name": analysis.repository_name,
                "default_branch": analysis.default_branch
            },
            "metrics": {
                "total_commits": analysis.total_commits,
                "total_prs": analysis.total_prs,
                "total_contributors": analysis.total_contributors,
                "avg_pr_review_time_hours": analysis.avg_pr_review_time_hours,
                "build_success_rate": analysis.build_success_rate
            },
            "hot_spots": [
                {
                    "path": hs.file_path,
                    "risk_score": hs.risk_score,
                    "change_count": hs.change_count,
                    "bug_associations": hs.associated_bugs
                }
                for hs in sorted(analysis.hot_spots, key=lambda x: -x.risk_score)[:20]
            ],
            "knowledge_silos": [
                {
                    "contributor": c.contributor_name,
                    "bus_factor": c.bus_factor_contribution,
                    "focus_areas": c.primary_directories
                }
                for c in sorted(
                    analysis.contributors,
                    key=lambda x: -x.bus_factor_contribution
                )[:10]
            ],
            "work_item_summary": {
                "total": analysis.total_issues,
                "by_type": self._count_work_item_types(analysis)
            }
        }

    def _count_work_item_types(self, analysis: RepositoryAnalysis) -> Dict[str, int]:
        """Count work items by type."""
        from collections import Counter

        # Query issue correlations
        correlations = self.db.query(IssueCorrelation).filter(
            IssueCorrelation.analysis_id == analysis.id
        ).all()

        type_counts = Counter(ic.suggested_work_type for ic in correlations)
        return dict(type_counts)


def create_azure_devops_service(
    pat: str,
    organization: str,
    project: str,
    db: Session
) -> AzureDevOpsService:
    """Factory function to create AzureDevOpsService."""
    config = AzureDevOpsConfig(
        personal_access_token=pat,
        organization=organization,
        project=project
    )
    return AzureDevOpsService(config, db)
