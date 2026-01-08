# Blue-Green Deployment Strategy voor Migratie

**Version**: 1.0
**Date**: 2025-12-31
**Status**: PLANNED (Fase 26, Week 140-141)
**Related Services**: StranglerFigService, DualRunComparisonService, WavePlannerService

---

## Overview

Deze strategie definieert hoe Blue-Green deployment wordt toegepast tijdens legacy migraties, met focus op:
1. **Graduele traffic switching** met automated health checks
2. **Dual-run testing** in productie omgeving
3. **Automated rollback** bij problemen
4. **Healthcare-compliant monitoring** (NEN7510/GDPR)

---

## Architecture Integration

### Positie in MarQed Migration Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  BROWN_PAPER_ENHANCED (Fase 20)    │  MIGRATION_ENHANCED (Fase 21)              │
│  ─────────────────────────────────  │  ─────────────────────────────────        │
│  Phase 1: Code Understanding       │  Phase 1: Preparation                      │
│  Phase 2: Domain Extraction        │  Phase 2: Code Transformation              │
│  Phase 3: Hierarchical Extraction  │  Phase 3: Data Migration                   │
│  Phase 4: Deep Extraction          │  Phase 4: Testing                          │
│  Phase 5: Estimation               │  Phase 5: Validation ◄─── Gate Check       │
│  Phase 6: Output                   │  Phase 6: Acceptance                       │
│                                    │  Phase 7: Deployment ◄─── BLUE-GREEN HERE  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  DEPLOYMENT PHASE (Fase 26 Services)                                             │
│                                                                                  │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐             │
│  │ StranglerFigSvc  │   │ DualRunCompareSvc│   │ WavePlannerSvc   │             │
│  │ ────────────────  │   │ ────────────────  │   │ ────────────────  │             │
│  │ • Traffic routing│   │ • Output compare │   │ • Wave scheduling │             │
│  │ • Feature flags  │   │ • Diff detection │   │ • Risk balancing  │             │
│  │ • Circuit breaker│   │ • Auto validation│   │ • Dependency order│             │
│  └──────────────────┘   └──────────────────┘   └──────────────────┘             │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                    BlueGreenDeploymentOrchestrator                         │ │
│  │                                                                            │ │
│  │  Gradual Rollout: 0% → 1% → 5% → 10% → 25% → 50% → 75% → 100%             │ │
│  │  Monitoring Duration: 5 min per step                                       │ │
│  │  Auto-Rollback Thresholds:                                                 │ │
│  │    • Error rate > 5%                                                       │ │
│  │    • Latency > 150% of baseline                                            │ │
│  │    • Health check failures                                                 │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Service Specifications

### 1. BlueGreenDeploymentService

```python
# backend/app/services/blue_green_deployment_service.py

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class DeploymentPhase(Enum):
    PREPARATION = "preparation"
    BASELINE_CAPTURE = "baseline_capture"
    GRADUAL_ROLLOUT = "gradual_rollout"
    MONITORING = "monitoring"
    VALIDATION = "validation"
    COMPLETE = "complete"
    ROLLBACK = "rollback"
    FAILED = "failed"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class RolloutStep:
    percent: int
    duration_seconds: int
    completed: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metrics: Optional[Dict] = None
    health_status: HealthStatus = HealthStatus.UNKNOWN

@dataclass
class BlueGreenSession:
    id: str
    migration_session_id: str
    blue_environment: str  # e.g., "production-blue"
    green_environment: str  # e.g., "production-green"
    current_phase: DeploymentPhase
    current_step_index: int
    rollout_steps: List[RolloutStep]
    baseline_metrics: Optional[Dict] = None
    created_at: datetime = None
    updated_at: datetime = None

    # Thresholds
    max_error_rate: float = 0.05  # 5%
    max_latency_increase: float = 1.5  # 150%
    min_request_count: int = 100

@dataclass
class EnvironmentMetrics:
    error_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    request_count: int
    success_rate: float
    health_status: HealthStatus
    timestamp: datetime

class BlueGreenDeploymentService:
    """
    Orchestrates Blue-Green deployments for migration projects.

    Agent Integration:
    - Miguel: Initiates deployment, monitors infrastructure
    - Tessa: Validates test results during each stage
    - Quinn: Security checks during rollout
    - Paul: Approves wave progression
    """

    def __init__(self, db, prometheus_client, nginx_controller, alerting_service):
        self.db = db
        self.prometheus = prometheus_client
        self.nginx = nginx_controller
        self.alerting = alerting_service

        # Default rollout configuration
        self.default_rollout_steps = [
            RolloutStep(percent=0, duration_seconds=0),      # Initial state
            RolloutStep(percent=1, duration_seconds=300),    # 1% for 5 min
            RolloutStep(percent=5, duration_seconds=300),    # 5% for 5 min
            RolloutStep(percent=10, duration_seconds=600),   # 10% for 10 min
            RolloutStep(percent=25, duration_seconds=900),   # 25% for 15 min
            RolloutStep(percent=50, duration_seconds=1800),  # 50% for 30 min
            RolloutStep(percent=75, duration_seconds=1800),  # 75% for 30 min
            RolloutStep(percent=100, duration_seconds=0),    # Full cutover
        ]

    async def create_session(
        self,
        migration_session_id: str,
        blue_environment: str,
        green_environment: str,
        custom_rollout_steps: Optional[List[RolloutStep]] = None
    ) -> BlueGreenSession:
        """Create new Blue-Green deployment session."""
        session = BlueGreenSession(
            id=str(uuid.uuid4()),
            migration_session_id=migration_session_id,
            blue_environment=blue_environment,
            green_environment=green_environment,
            current_phase=DeploymentPhase.PREPARATION,
            current_step_index=0,
            rollout_steps=custom_rollout_steps or self.default_rollout_steps.copy(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Save to database
        await self._save_session(session)

        # Notify agents
        await self._notify_agents(session, "deployment_session_created")

        return session

    async def capture_baseline(self, session_id: str) -> EnvironmentMetrics:
        """Capture baseline metrics from Blue environment."""
        session = await self._get_session(session_id)

        session.current_phase = DeploymentPhase.BASELINE_CAPTURE

        # Query Prometheus for baseline metrics
        metrics = await self._query_environment_metrics(
            session.blue_environment,
            duration_minutes=10
        )

        session.baseline_metrics = {
            'error_rate': metrics.error_rate,
            'avg_latency_ms': metrics.avg_latency_ms,
            'p95_latency_ms': metrics.p95_latency_ms,
            'request_count': metrics.request_count,
            'captured_at': datetime.utcnow().isoformat()
        }

        await self._save_session(session)

        return metrics

    async def start_rollout(self, session_id: str) -> BlueGreenSession:
        """Start gradual rollout process."""
        session = await self._get_session(session_id)

        if session.baseline_metrics is None:
            raise ValueError("Baseline metrics not captured - run capture_baseline first")

        session.current_phase = DeploymentPhase.GRADUAL_ROLLOUT
        session.current_step_index = 0

        await self._save_session(session)

        # Start automated rollout loop
        await self._execute_rollout(session)

        return session

    async def _execute_rollout(self, session: BlueGreenSession):
        """Execute automated rollout with health checks."""

        for i, step in enumerate(session.rollout_steps):
            session.current_step_index = i
            step.started_at = datetime.utcnow()

            try:
                # Update traffic split
                await self.nginx.update_traffic_split(
                    blue_weight=100 - step.percent,
                    green_weight=step.percent
                )

                await self.alerting.send_notification(
                    f"📊 Rollout stage {step.percent}% started",
                    severity="info"
                )

                if step.percent == 0:
                    step.completed = True
                    step.completed_at = datetime.utcnow()
                    continue

                # Monitor for duration
                session.current_phase = DeploymentPhase.MONITORING
                await self._save_session(session)

                green_metrics = await self._monitor_and_validate(
                    session,
                    step.duration_seconds
                )

                step.metrics = {
                    'error_rate': green_metrics.error_rate,
                    'avg_latency_ms': green_metrics.avg_latency_ms,
                    'request_count': green_metrics.request_count
                }

                # Validate health
                is_healthy, issues = self._validate_health(
                    session.baseline_metrics,
                    green_metrics,
                    session
                )

                step.health_status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY

                if not is_healthy:
                    # Auto-rollback
                    await self._execute_rollback(session, issues)
                    return

                step.completed = True
                step.completed_at = datetime.utcnow()

                await self.alerting.send_notification(
                    f"✅ Rollout stage {step.percent}% completed - "
                    f"Error rate: {green_metrics.error_rate:.2%}, "
                    f"Latency: {green_metrics.avg_latency_ms:.0f}ms",
                    severity="info"
                )

            except Exception as e:
                await self._execute_rollback(session, [str(e)])
                return

        # All steps completed successfully
        session.current_phase = DeploymentPhase.COMPLETE
        await self._save_session(session)

        await self.alerting.send_notification(
            "🎉 Blue-Green rollout completed! 100% traffic on Green",
            severity="success"
        )

    async def _execute_rollback(
        self,
        session: BlueGreenSession,
        issues: List[str]
    ):
        """Execute emergency rollback to Blue."""
        session.current_phase = DeploymentPhase.ROLLBACK
        await self._save_session(session)

        # Immediate traffic switch
        await self.nginx.update_traffic_split(
            blue_weight=100,
            green_weight=0
        )

        await self.alerting.send_notification(
            f"🚨 ROLLBACK executed!\n" + "\n".join(issues),
            severity="critical"
        )

        session.current_phase = DeploymentPhase.FAILED
        await self._save_session(session)

    async def manual_rollback(self, session_id: str, reason: str):
        """Manual rollback triggered by operator/agent."""
        session = await self._get_session(session_id)
        await self._execute_rollback(session, [f"Manual rollback: {reason}"])

    async def pause_rollout(self, session_id: str):
        """Pause rollout at current stage."""
        session = await self._get_session(session_id)
        session.current_phase = DeploymentPhase.VALIDATION
        await self._save_session(session)

        await self.alerting.send_notification(
            f"⏸️ Rollout paused at {session.rollout_steps[session.current_step_index].percent}%",
            severity="warning"
        )

    async def resume_rollout(self, session_id: str):
        """Resume paused rollout."""
        session = await self._get_session(session_id)
        session.current_phase = DeploymentPhase.GRADUAL_ROLLOUT
        await self._save_session(session)

        # Continue from current step
        await self._execute_rollout(session)

    def _validate_health(
        self,
        baseline: Dict,
        current: EnvironmentMetrics,
        session: BlueGreenSession
    ) -> tuple[bool, List[str]]:
        """Validate Green health against Blue baseline."""
        issues = []

        # Check error rate threshold
        if current.error_rate > session.max_error_rate:
            issues.append(
                f"Error rate {current.error_rate:.2%} exceeds threshold {session.max_error_rate:.2%}"
            )

        # Check error rate vs baseline
        if current.error_rate > baseline['error_rate'] * 2:
            issues.append(
                f"Error rate {current.error_rate:.2%} is 2x higher than baseline {baseline['error_rate']:.2%}"
            )

        # Check latency degradation
        baseline_latency = baseline['avg_latency_ms']
        if current.avg_latency_ms > baseline_latency * session.max_latency_increase:
            issues.append(
                f"Latency {current.avg_latency_ms:.0f}ms exceeds "
                f"{session.max_latency_increase}x baseline ({baseline_latency:.0f}ms)"
            )

        # Check minimum request count
        if current.request_count < session.min_request_count:
            issues.append(
                f"Insufficient traffic ({current.request_count} requests) for reliable validation"
            )

        return len(issues) == 0, issues

    async def _query_environment_metrics(
        self,
        environment: str,
        duration_minutes: int = 5
    ) -> EnvironmentMetrics:
        """Query Prometheus for environment metrics."""
        # Error rate query
        error_rate = await self.prometheus.query(
            f'sum(rate(http_requests_total{{environment="{environment}",status=~"5.."}}[{duration_minutes}m])) / '
            f'sum(rate(http_requests_total{{environment="{environment}"}}[{duration_minutes}m]))'
        )

        # Latency queries
        avg_latency = await self.prometheus.query(
            f'avg(rate(http_request_duration_seconds_sum{{environment="{environment}"}}[{duration_minutes}m]) / '
            f'rate(http_request_duration_seconds_count{{environment="{environment}"}}[{duration_minutes}m])) * 1000'
        )

        p95_latency = await self.prometheus.query(
            f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{environment="{environment}"}}[{duration_minutes}m])) * 1000'
        )

        # Request count
        request_count = await self.prometheus.query(
            f'sum(increase(http_requests_total{{environment="{environment}"}}[{duration_minutes}m]))'
        )

        # Success rate
        success_rate = 1.0 - error_rate if error_rate else 1.0

        # Health status based on thresholds
        health_status = HealthStatus.HEALTHY
        if error_rate > 0.05:
            health_status = HealthStatus.UNHEALTHY
        elif error_rate > 0.02:
            health_status = HealthStatus.DEGRADED

        return EnvironmentMetrics(
            error_rate=error_rate or 0.0,
            avg_latency_ms=avg_latency or 0.0,
            p95_latency_ms=p95_latency or 0.0,
            request_count=int(request_count or 0),
            success_rate=success_rate,
            health_status=health_status,
            timestamp=datetime.utcnow()
        )
```

---

## Healthcare Compliance (NEN7510/GDPR)

### Audit Logging Requirements

```python
@dataclass
class DeploymentAuditLog:
    """NEN7510 compliant audit logging for deployment actions."""

    id: str
    session_id: str
    action: str  # TRAFFIC_SWITCH, ROLLBACK, HEALTH_CHECK, etc.
    actor: str  # System or user identity
    timestamp: datetime
    previous_state: Dict
    new_state: Dict
    justification: Optional[str]

    # NEN7510 required fields
    patient_data_accessed: bool = False
    data_integrity_verified: bool = True
    encryption_status: str = "TLS_1_3"

    # GDPR fields
    data_processing_basis: str = "legitimate_interest"
    data_subjects_affected: int = 0

class ComplianceMonitoringService:
    """Healthcare-specific monitoring during Blue-Green deployment."""

    async def pre_deployment_checks(self, session: BlueGreenSession) -> List[str]:
        """Run compliance checks before deployment."""
        checks = []

        # NEN7510 checks
        checks.append(await self._verify_encryption())
        checks.append(await self._verify_audit_logging())
        checks.append(await self._verify_access_controls())

        # GDPR checks
        checks.append(await self._verify_data_retention())
        checks.append(await self._verify_consent_management())

        # HCI-CRS specific
        checks.append(await self._verify_patient_data_isolation())
        checks.append(await self._verify_emergency_access_procedures())

        return checks

    async def monitor_data_integrity(
        self,
        blue_env: str,
        green_env: str
    ) -> Dict:
        """Monitor data integrity during dual-run."""
        return {
            'record_count_match': await self._compare_record_counts(blue_env, green_env),
            'checksum_match': await self._compare_checksums(blue_env, green_env),
            'patient_ids_match': await self._compare_patient_ids(blue_env, green_env),
            'audit_trail_intact': await self._verify_audit_trail(green_env)
        }
```

---

## API Endpoints

| Endpoint | Method | Description | Agent |
|----------|--------|-------------|-------|
| `/api/deployment/blue-green/sessions` | POST | Create deployment session | Miguel |
| `/api/deployment/blue-green/{id}` | GET | Get session status | Miguel |
| `/api/deployment/blue-green/{id}/baseline` | POST | Capture baseline metrics | Miguel |
| `/api/deployment/blue-green/{id}/start` | POST | Start gradual rollout | Miguel + Paul |
| `/api/deployment/blue-green/{id}/pause` | POST | Pause rollout | Paul |
| `/api/deployment/blue-green/{id}/resume` | POST | Resume rollout | Paul |
| `/api/deployment/blue-green/{id}/rollback` | POST | Emergency rollback | Miguel |
| `/api/deployment/blue-green/{id}/metrics` | GET | Get current metrics | Tessa |
| `/api/deployment/blue-green/{id}/validate` | POST | Validate health | Quinn |
| `/api/deployment/blue-green/{id}/audit-log` | GET | Get audit trail | Quinn |

---

## Integration met DualRunComparisonService (Fase 23)

```python
class DeploymentDualRunIntegration:
    """Combines Blue-Green deployment with Dual-Run testing."""

    async def enable_dual_run_during_rollout(
        self,
        deployment_session_id: str,
        comparison_endpoints: List[str]
    ):
        """
        During gradual rollout, enable dual-run comparison:
        - Shadow traffic to Green (no response to user)
        - Compare outputs between Blue and Green
        - Report differences for validation
        """
        session = await self.deployment_service.get_session(deployment_session_id)

        for endpoint in comparison_endpoints:
            await self.dual_run_service.create_comparison(
                blue_url=f"{session.blue_environment}{endpoint}",
                green_url=f"{session.green_environment}{endpoint}",
                mode="shadow",  # Don't use Green response
                comparison_mode="strict"  # Exact output match
            )

        return {
            'dual_run_enabled': True,
            'endpoints': comparison_endpoints,
            'mode': 'shadow'
        }
```

---

## Wave Planning Integration (WavePlannerService)

```python
class WaveAwareBlueGreenDeployment:
    """Integrate wave planning with Blue-Green deployment."""

    async def deploy_wave(
        self,
        wave_id: str,
        deployment_config: Dict
    ) -> BlueGreenSession:
        """
        Deploy a migration wave with Blue-Green strategy.

        Waves are ordered by:
        1. Dependency graph (foundation first)
        2. Risk score (low risk first)
        3. User impact (internal first, then external)
        """
        wave = await self.wave_planner.get_wave(wave_id)

        # Validate wave is ready
        if not wave.all_dependencies_deployed:
            raise ValueError(f"Wave {wave_id} has undeployed dependencies")

        # Create deployment session for wave
        session = await self.deployment_service.create_session(
            migration_session_id=wave.migration_session_id,
            blue_environment=wave.blue_environment,
            green_environment=wave.green_environment,
            custom_rollout_steps=self._generate_wave_rollout_steps(wave)
        )

        # Capture baseline
        await self.deployment_service.capture_baseline(session.id)

        # Start rollout
        await self.deployment_service.start_rollout(session.id)

        return session

    def _generate_wave_rollout_steps(self, wave) -> List[RolloutStep]:
        """Generate rollout steps based on wave risk level."""

        if wave.risk_level == "high":
            # More gradual for high risk
            return [
                RolloutStep(percent=0, duration_seconds=0),
                RolloutStep(percent=1, duration_seconds=600),   # 10 min
                RolloutStep(percent=2, duration_seconds=600),
                RolloutStep(percent=5, duration_seconds=900),   # 15 min
                RolloutStep(percent=10, duration_seconds=1200), # 20 min
                RolloutStep(percent=25, duration_seconds=1800), # 30 min
                RolloutStep(percent=50, duration_seconds=3600), # 1 hour
                RolloutStep(percent=75, duration_seconds=3600),
                RolloutStep(percent=100, duration_seconds=0),
            ]
        elif wave.risk_level == "medium":
            return self.deployment_service.default_rollout_steps
        else:
            # Faster for low risk
            return [
                RolloutStep(percent=0, duration_seconds=0),
                RolloutStep(percent=10, duration_seconds=300),
                RolloutStep(percent=50, duration_seconds=600),
                RolloutStep(percent=100, duration_seconds=0),
            ]
```

---

## Monitoring Dashboard Integration

### Grafana Dashboard Specification

```json
{
  "dashboard": {
    "title": "Blue-Green Migration Deployment",
    "panels": [
      {
        "title": "Traffic Distribution (Blue vs Green)",
        "description": "Real-time traffic split percentage"
      },
      {
        "title": "Error Rate Comparison",
        "description": "Side-by-side error rates with thresholds"
      },
      {
        "title": "P95 Latency Comparison",
        "description": "Performance comparison between environments"
      },
      {
        "title": "Rollout Progress",
        "description": "Current stage, time remaining, health status"
      },
      {
        "title": "Dual-Run Comparison Results",
        "description": "Output differences detected"
      },
      {
        "title": "Compliance Status",
        "description": "NEN7510/GDPR compliance indicators"
      }
    ]
  }
}
```

---

## Related Documentation

| Topic | Document |
|-------|----------|
| Migration Enhanced Workflow | [migration-enhanced.md](migration-enhanced.md) |
| Testing Excellence (Dual-Run) | [ROADMAP.md - Fase 23](../../ROADMAP.md) |
| Wave Planning | [ROADMAP.md - Fase 26](../../ROADMAP.md) |
| StranglerFigService | [AGENTS.md - Gap Analysis](../../AGENTS.md) |
| Deep Extraction Pipeline | [deep-extraction-pipeline.md](deep-extraction-pipeline.md) |
