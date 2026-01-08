# Client Portal Architecture

**Version:** 1.0
**Status:** PLANNED (Week 87-90)
**Datum:** 2025-12-19

---

## Executive Summary

Customer-facing portal waar klanten feature requests kunnen indienen en de voortgang kunnen volgen. Volledige integratie met MarkdownTaskManager voor automatische processing door AI agents.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT PORTAL ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                              PRESENTATION LAYER                                      ││
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐          ││
│  │  │     Login Page      │  │   Feature Request   │  │   Progress View     │          ││
│  │  │  OAuth2/JWT Auth    │  │   Form + Validation │  │   Real-time Status  │          ││
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘          ││
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐          ││
│  │  │   Test Results      │  │   Voting/Comments   │  │   Roadmap View      │          ││
│  │  │   Pass/Fail/Cover   │  │   Community Input   │  │   Drag-Drop Plan    │          ││
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘          ││
│  │                                                                                      ││
│  │  Technology: React + TypeScript | Repository: github.com/zeeneddie/user-story       ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                           │                                              │
│                                    REST/GraphQL                                          │
│                                           │                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                  BACKEND LAYER                                       ││
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐          ││
│  │  │   User Management   │  │  Feature Request    │  │   Status Tracking   │          ││
│  │  │   CRUD + Roles      │  │   CRUD + Workflow   │  │   Updates + History │          ││
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘          ││
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐          ││
│  │  │   Voting System     │  │   Comment System    │  │   Notification Svc  │          ││
│  │  │   Upvote/Downvote   │  │   Threaded Comments │  │   Email + WebSocket │          ││
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘          ││
│  │                                                                                      ││
│  │  Technology: Strapi CMS (Node.js, KoaJS, MongoDB) | Repo: github.com/zeeneddie/strapi││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                           │                                              │
│                                     REST API                                             │
│                                           │                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                              INTEGRATION LAYER                                       ││
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐          ││
│  │  │   Epic Mapping      │  │   Sprint Sync       │  │   Test Results      │          ││
│  │  │   Feature→Epic      │  │   Status Updates    │  │   Execution Logs    │          ││
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘          ││
│  │                                                                                      ││
│  │  Technology: FastAPI Integration Service | Repo: MarkdownTaskManager                ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                           │                                              │
│                                    Agent Routing                                         │
│                                           │                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                 AGENT LAYER                                          ││
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐          ││
│  │  │   Peter (Product)   │  │   Felix (Architect) │  │   Paul (Project)    │          ││
│  │  │   Classification    │  │   Tech Spec         │  │   Sprint Planning   │          ││
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘          ││
│  │  ┌─────────────────────┐  ┌─────────────────────┐                                   ││
│  │  │   Tessa (Test)      │  │   Diana (Docs)      │                                   ││
│  │  │   Test Strategy     │  │   Release Notes     │                                   ││
│  │  └─────────────────────┘  └─────────────────────┘                                   ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Stack Components

| Component | Technologie | Repository | Beschrijving |
|-----------|-------------|------------|--------------|
| **Frontend** | React + TypeScript | github.com/zeeneddie/user-story | Feature request UI, progress tracking |
| **Backend** | Strapi CMS | github.com/zeeneddie/strapi | Node.js, KoaJS, MongoDB, GraphQL |
| **Integration** | FastAPI | MarkdownTaskManager | REST API bridge, WebSocket |
| **Agents** | 10 Core Agents | MarkdownTaskManager | Automated processing |

---

## Authentication System

### 3-Tier Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. IDENTIFICATION                                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Email/Username → Lookup User → Return User Record           ││
│  │  API: POST /api/portal/auth/identify                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  2. AUTHENTICATION                                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Password Verify OR OAuth2 Token → Generate JWT              ││
│  │  Providers: Google, GitHub, Microsoft, Email+Password        ││
│  │  API: POST /api/portal/auth/login                            ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  3. AUTHORIZATION                                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  JWT Claims → Role Check → Permission Evaluation             ││
│  │  Roles: customer, power_user, admin                          ││
│  │  API: Middleware on all protected endpoints                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### User Roles & Permissions

| Role | Create Features | View All | Vote | Comment | Manage | Admin |
|------|-----------------|----------|------|---------|--------|-------|
| **customer** | Own | Own | ✅ | ✅ | ❌ | ❌ |
| **power_user** | ✅ | ✅ | ✅ | ✅ | Own | ❌ |
| **admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### JWT Token Structure

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "customer",
  "organization_id": "org-uuid",
  "permissions": ["feature:create", "feature:read:own", "vote:create"],
  "iat": 1734567890,
  "exp": 1734654290
}
```

---

## Feature Request Flow

### Complete Flow Diagram (Real-Time Updates bij ELKE Stap)

```
CUSTOMER                  PORTAL BACKEND              MARKDOWNTASKMANAGER           AGENTS
   │                            │                             │                       │
   │  1. Submit Feature         │                             │                       │
   │───────────────────────────▶│                             │                       │
   │  ◄── Status: "Submitted"   │                             │                       │
   │                            │  2. Validate + Store         │                       │
   │                            │──────────────────────────────▶                       │
   │  ◄── Status: "Received"    │                             │                       │
   │                            │                             │  3. Route to Peter    │
   │  ◄── Status: "Analyzing"   │◀────────────────────────────│──────────────────────▶│
   │      "Peter analyzes..."   │                             │                       │
   │                            │                             │  4. Classification     │
   │  ◄── Status: "Classified"  │◀────────────────────────────│◀──────────────────────│
   │      "Type: Enhancement"   │                             │                       │
   │                            │                             │  5. Map to Epic       │
   │  ◄── Status: "Mapped"      │◀────────────────────────────│◀──────────────────────│
   │      "Epic: UI/UX"         │                             │                       │
   │                            │                             │                       │
   │  ◄── Status: "Backlog"     │◀────────────────────────────│                       │
   │      "In product backlog"  │                             │                       │
   │                            │                             │  6. Sprint Planning   │
   │  ◄── Status: "Planning"    │◀────────────────────────────│──────────────────────▶│
   │      "Paul assigns..."     │                             │    (Paul agent)       │
   │                            │                             │                       │
   │  ◄── Status: "Planned"     │◀────────────────────────────│◀──────────────────────│
   │      "Sprint 23 (Dec 25)"  │                             │                       │
   │                            │                             │                       │
   │  ◄── Status: "Queued"      │◀────────────────────────────│  7. Sprint Start      │
   │      "Waiting for sprint"  │                             │                       │
   │                            │                             │                       │
   │  ◄── Status: "Building"    │◀────────────────────────────│  8. Development Start │
   │      "Developer assigned"  │                             │                       │
   │                            │                             │                       │
   │  ◄── Status: "In Progress" │◀────────────────────────────│  9. Active Dev        │
   │      "50% complete"        │                             │                       │
   │                            │                             │                       │
   │  ◄── Status: "Code Review" │◀────────────────────────────│  10. Review           │
   │      "Quinn reviewing..."  │                             │──────────────────────▶│
   │                            │                             │                       │
   │  ◄── Status: "Testing"     │◀────────────────────────────│  11. Test Start       │
   │      "Tessa testing..."    │                             │──────────────────────▶│
   │                            │                             │    (Tessa agent)      │
   │  ◄── Test Progress         │◀────────────────────────────│◀──────────────────────│
   │      "5/15 tests run"      │                             │                       │
   │                            │                             │                       │
   │  ◄── Test Progress         │◀────────────────────────────│                       │
   │      "10/15 tests run"     │                             │                       │
   │                            │                             │                       │
   │  ◄── Status: "Test Done"   │◀────────────────────────────│                       │
   │      "15/15 passed ✅"     │                             │                       │
   │                            │                             │                       │
   │  ◄── Status: "Deploying"   │◀────────────────────────────│  12. Deployment       │
   │      "Deploying to prod"   │                             │                       │
   │                            │                             │                       │
   │  ◄── Status: "Released"    │◀────────────────────────────│  13. Live             │
   │      "v2.3.0 - LIVE! 🎉"   │                             │                       │
```

### Real-Time Update Principe

**ELKE status transitie triggert een portal update:**

```python
# Event-driven architecture: elke state change → portal notification
KANBAN_LANE_CHANGED     →  Portal Status Update + WebSocket + Optional Email
AGENT_TASK_STARTED      →  Portal Status Update + WebSocket
AGENT_TASK_COMPLETED    →  Portal Status Update + WebSocket
TEST_PROGRESS           →  Portal Status Update + WebSocket (live counter)
TEST_COMPLETED          →  Portal Status Update + WebSocket + Email
DEPLOYMENT_STARTED      →  Portal Status Update + WebSocket
DEPLOYMENT_COMPLETED    →  Portal Status Update + WebSocket + Email + Push
```

### Status States (Granulaire Updates)

| Status | Code | Beschrijving | Trigger | Notification |
|--------|------|--------------|---------|--------------|
| **Submitted** | `submitted` | Request ontvangen | Form submit | WebSocket |
| **Received** | `received` | Validatie geslaagd | Backend validation | WebSocket |
| **Analyzing** | `analyzing` | Peter agent classificeert | Agent start | WebSocket |
| **Classified** | `classified` | Work type bepaald | Peter completion | WebSocket |
| **Mapped** | `mapped` | Gekoppeld aan Epic | Epic assignment | WebSocket |
| **Backlog** | `backlog` | In product backlog | Backlog entry | WebSocket + Email |
| **Planning** | `planning` | Paul plant in sprint | Paul start | WebSocket |
| **Planned** | `planned` | Gepland in sprint | Paul completion | WebSocket + Email |
| **Queued** | `queued` | Wacht op sprint start | Sprint assignment | WebSocket |
| **Building** | `building` | Developer toegewezen | Dev assignment | WebSocket |
| **In Progress** | `in_progress` | Actief in ontwikkeling | First commit | WebSocket |
| **Code Review** | `code_review` | Quinn reviewt code | PR created | WebSocket |
| **Testing** | `testing` | Tessa test de feature | Test start | WebSocket |
| **Test Progress** | `test_progress` | Tests worden uitgevoerd | During tests | WebSocket (live) |
| **Test Done** | `test_done` | Alle tests compleet | Test completion | WebSocket + Email |
| **Deploying** | `deploying` | Deployment gestart | Deploy start | WebSocket |
| **Released** | `released` | Live in productie | Deploy complete | WebSocket + Email + Push |
| **Closed** | `closed` | Afgehandeld | Manual/Auto | WebSocket |

### Notification Strategie per Status

| Status Categorie | WebSocket | Email | Push | Frequentie |
|------------------|-----------|-------|------|------------|
| **Submission** (submitted→mapped) | ✅ | ❌ | ❌ | Per event |
| **Backlog** | ✅ | ✅ | ❌ | Eenmalig |
| **Planning** | ✅ | ✅ | ❌ | Eenmalig |
| **Development** (building→code_review) | ✅ | ❌ | ❌ | Per event |
| **Testing** | ✅ | ❌ | ❌ | Live progress |
| **Test Complete** | ✅ | ✅ | ❌ | Eenmalig |
| **Released** | ✅ | ✅ | ✅ | Eenmalig |

### Customer Notification Preferences

```json
{
  "notifications": {
    "email": {
      "backlog_entry": true,
      "sprint_planned": true,
      "test_completed": true,
      "released": true,
      "weekly_digest": true
    },
    "push": {
      "released": true
    },
    "websocket": {
      "all_updates": true  // Real-time in portal UI
    }
  }
}
```

### Event-Driven Notification Service

```python
# backend/app/services/portal_notification_service.py

class PortalNotificationService:
    """
    Centraal punt voor ALLE portal notificaties.
    Luistert naar Kanban events en pusht updates naar Portal.
    """

    # Status mapping: Kanban lane → Portal status
    LANE_TO_STATUS = {
        "BACKLOG": "backlog",
        "ANALYSIS": "analyzing",
        "PLANNED": "planned",
        "BUILD": "building",
        "TEST": "testing",
        "IN_REVIEW": "code_review",
        "DONE": "released"
    }

    async def on_kanban_event(self, event: KanbanEvent):
        """Handler voor ALLE Kanban events → Portal updates"""

        feature_id = await self.get_portal_feature_id(event.item_id)
        if not feature_id:
            return  # Geen portal link

        # Bepaal portal status
        portal_status = self._map_event_to_status(event)

        # 1. Update Portal database via Strapi API
        await self.strapi_client.update_feature_status(
            feature_id=feature_id,
            status=portal_status,
            metadata={
                "event_type": event.type,
                "lane": event.lane,
                "agent": event.agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                "details": event.details
            }
        )

        # 2. WebSocket broadcast (altijd, voor real-time UI)
        await self.websocket_broadcast(
            channel=f"feature:{feature_id}",
            event="status_changed",
            data={
                "status": portal_status,
                "message": self._get_status_message(portal_status, event),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # 3. Email (alleen voor belangrijke milestones)
        if self._should_email(portal_status):
            await self.email_service.send_status_update(
                feature_id=feature_id,
                status=portal_status,
                template=f"status_{portal_status}"
            )

        # 4. Push notification (alleen voor release)
        if portal_status == "released":
            await self.push_service.notify(
                feature_id=feature_id,
                title="Feature Released! 🎉",
                body=f"Your feature is now live in {event.details.get('version', 'production')}"
            )

    def _get_status_message(self, status: str, event: KanbanEvent) -> str:
        """Human-readable status message voor UI"""
        messages = {
            "submitted": "Your request has been submitted",
            "received": "Request validated successfully",
            "analyzing": f"Agent {event.agent_name} is analyzing your request...",
            "classified": f"Classified as: {event.details.get('work_type', 'Feature')}",
            "mapped": f"Linked to Epic: {event.details.get('epic_name', 'TBD')}",
            "backlog": "Added to product backlog",
            "planning": f"Agent {event.agent_name} is planning sprint assignment...",
            "planned": f"Scheduled for {event.details.get('sprint_name', 'next sprint')}",
            "queued": f"Waiting for sprint to start ({event.details.get('start_date', 'TBD')})",
            "building": f"Development started by {event.details.get('developer', 'team')}",
            "in_progress": f"Development {event.details.get('progress', 0)}% complete",
            "code_review": f"Code review in progress by {event.agent_name}",
            "testing": f"Testing started by {event.agent_name}",
            "test_progress": f"Tests running: {event.details.get('completed', 0)}/{event.details.get('total', 0)}",
            "test_done": f"All tests passed! ({event.details.get('passed', 0)}/{event.details.get('total', 0)})",
            "deploying": "Deploying to production...",
            "released": f"Live in version {event.details.get('version', 'latest')}! 🎉"
        }
        return messages.get(status, f"Status: {status}")


# Event listeners registratie
@event_listener("kanban.item.created")
@event_listener("kanban.item.lane_changed")
@event_listener("kanban.item.agent_started")
@event_listener("kanban.item.agent_completed")
@event_listener("kanban.item.test_progress")
@event_listener("kanban.item.test_completed")
@event_listener("kanban.item.deployed")
async def handle_kanban_event(event: KanbanEvent):
    """Alle Kanban events triggeren portal updates"""
    await portal_notification_service.on_kanban_event(event)
```

---

## API Endpoints

### Portal Authentication

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/portal/auth/register` | POST | Register new user | ❌ |
| `/api/portal/auth/login` | POST | User login | ❌ |
| `/api/portal/auth/oauth/{provider}` | GET | OAuth2 initiate | ❌ |
| `/api/portal/auth/oauth/{provider}/callback` | GET | OAuth2 callback | ❌ |
| `/api/portal/auth/refresh` | POST | Refresh JWT | ✅ |
| `/api/portal/auth/logout` | POST | Logout | ✅ |
| `/api/portal/auth/me` | GET | Current user | ✅ |

### Feature Requests

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/portal/features` | GET | List features (filtered by role) | ✅ |
| `/api/portal/features` | POST | Create feature request | ✅ |
| `/api/portal/features/{id}` | GET | Feature details | ✅ |
| `/api/portal/features/{id}` | PUT | Update feature | ✅ (owner) |
| `/api/portal/features/{id}` | DELETE | Delete feature | ✅ (admin) |
| `/api/portal/features/{id}/status` | GET | Status history | ✅ |
| `/api/portal/features/{id}/tests` | GET | Test results | ✅ |
| `/api/portal/features/{id}/attachments` | GET/POST | Attachments | ✅ |

### Social Features

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/portal/features/{id}/votes` | POST | Vote (up/down) | ✅ |
| `/api/portal/features/{id}/votes` | DELETE | Remove vote | ✅ |
| `/api/portal/features/{id}/comments` | GET | List comments | ✅ |
| `/api/portal/features/{id}/comments` | POST | Add comment | ✅ |
| `/api/portal/features/{id}/comments/{cid}` | PUT | Edit comment | ✅ (owner) |
| `/api/portal/features/{id}/comments/{cid}` | DELETE | Delete comment | ✅ (owner/admin) |

### Public Roadmap

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/portal/roadmap` | GET | Public roadmap | ❌ |
| `/api/portal/roadmap/releases` | GET | Release schedule | ❌ |
| `/api/portal/roadmap/changelog` | GET | Changelog | ❌ |

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `feature:status_changed` | Server→Client | Status update |
| `feature:comment_added` | Server→Client | New comment |
| `feature:vote_changed` | Server→Client | Vote count update |
| `test:results_available` | Server→Client | Test results ready |
| `sprint:assigned` | Server→Client | Sprint assignment |
| `release:published` | Server→Client | New release |

---

## Integration with MarkdownTaskManager

### Sync Service

```python
# backend/app/services/portal_integration_service.py

class PortalIntegrationService:
    """Bridges Portal Backend with MarkdownTaskManager"""

    async def create_work_item_from_feature(
        self,
        feature_request: FeatureRequest
    ) -> KanbanItem:
        """Create Kanban item from portal feature request"""

        # 1. Classify work type via Peter agent
        work_type = await self.agent_service.classify(
            title=feature_request.title,
            description=feature_request.description
        )

        # 2. Suggest epic mapping
        epic_suggestion = await self.backlog_service.suggest_epic(
            work_type=work_type,
            keywords=feature_request.keywords
        )

        # 3. Create Kanban item
        kanban_item = await self.kanban_service.create_item(
            title=feature_request.title,
            description=feature_request.description,
            source="portal",
            source_id=str(feature_request.id),
            epic_id=epic_suggestion.id if epic_suggestion else None,
            work_type=work_type,
            priority=feature_request.priority
        )

        # 4. Link portal feature to kanban item
        await self.portal_sync_service.link(
            feature_id=feature_request.id,
            kanban_item_id=kanban_item.id
        )

        return kanban_item

    async def sync_status_to_portal(
        self,
        kanban_item_id: int
    ):
        """Push status updates from Kanban to Portal"""

        item = await self.kanban_service.get_item(kanban_item_id)
        feature_id = await self.portal_sync_service.get_feature_id(kanban_item_id)

        if feature_id:
            # Map Kanban lane to Portal status
            portal_status = self._map_lane_to_status(item.lane)

            # Push update via Strapi API
            await self.strapi_client.update_feature_status(
                feature_id=feature_id,
                status=portal_status,
                metadata={
                    "lane": item.lane,
                    "sprint": item.sprint_id,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

            # Broadcast via WebSocket
            await self.websocket_service.broadcast(
                channel=f"feature:{feature_id}",
                event="status_changed",
                data={"status": portal_status}
            )
```

### Test Results Integration

```python
async def sync_test_results(
    self,
    kanban_item_id: int,
    test_run: TestRun
):
    """Push test results from Tessa agent to Portal"""

    feature_id = await self.portal_sync_service.get_feature_id(kanban_item_id)

    if feature_id:
        # Format test results for portal display
        test_summary = {
            "total": test_run.total_tests,
            "passed": test_run.passed_tests,
            "failed": test_run.failed_tests,
            "skipped": test_run.skipped_tests,
            "coverage": test_run.coverage_percent,
            "duration_ms": test_run.duration_ms,
            "run_at": test_run.executed_at.isoformat(),
            "details": [
                {
                    "name": t.name,
                    "status": t.status,
                    "duration_ms": t.duration_ms,
                    "error": t.error_message if t.status == "failed" else None
                }
                for t in test_run.test_cases[:50]  # Limit to first 50
            ]
        }

        # Push to Portal
        await self.strapi_client.update_feature_tests(
            feature_id=feature_id,
            test_results=test_summary
        )

        # WebSocket notification
        await self.websocket_service.broadcast(
            channel=f"feature:{feature_id}",
            event="test_results_available",
            data=test_summary
        )
```

---

## Database Schema

### Portal Backend (Strapi/MongoDB)

```javascript
// Feature Request Collection
{
  "_id": ObjectId,
  "title": String,
  "description": String,
  "priority": Enum["low", "medium", "high", "critical"],
  "status": Enum["submitted", "analyzing", "backlog", "planned", "building", "testing", "review", "released", "closed"],
  "category": String,
  "tags": [String],
  "author": { ref: "User" },
  "attachments": [{ name: String, url: String, type: String }],
  "votes": { up: Number, down: Number },
  "voters": [{ user: ref, vote: Number }],
  "comments": [{ ref: "Comment" }],
  "external_link": {
    "type": "kanban_item",
    "id": Number,
    "url": String
  },
  "sprint": {
    "id": Number,
    "name": String,
    "start_date": Date,
    "end_date": Date
  },
  "test_results": {
    "total": Number,
    "passed": Number,
    "failed": Number,
    "coverage": Number,
    "last_run": Date
  },
  "release": {
    "version": String,
    "date": Date,
    "changelog_url": String
  },
  "created_at": Date,
  "updated_at": Date
}

// User Collection
{
  "_id": ObjectId,
  "email": String,
  "username": String,
  "password_hash": String,  // null for OAuth users
  "oauth_providers": [{ provider: String, id: String }],
  "role": Enum["customer", "power_user", "admin"],
  "organization": { ref: "Organization" },
  "avatar_url": String,
  "notifications_enabled": Boolean,
  "created_at": Date
}

// Comment Collection
{
  "_id": ObjectId,
  "feature": { ref: "Feature" },
  "author": { ref: "User" },
  "content": String,
  "parent": { ref: "Comment" },  // For threaded comments
  "created_at": Date,
  "updated_at": Date
}
```

### MarkdownTaskManager (PostgreSQL)

```sql
-- Portal sync table
CREATE TABLE portal_feature_links (
    id SERIAL PRIMARY KEY,
    portal_feature_id VARCHAR(100) NOT NULL,
    kanban_item_id INTEGER REFERENCES kanban_items(id),
    epic_id UUID REFERENCES task_epics(id),
    sync_status VARCHAR(20) DEFAULT 'active',
    last_synced_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_portal_links_feature ON portal_feature_links(portal_feature_id);
CREATE INDEX ix_portal_links_kanban ON portal_feature_links(kanban_item_id);
```

---

## Week Planning

### Week 87: Authentication & User Management

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1-2 | Strapi setup | Docker setup, user content type, roles |
| 3 | OAuth2 integration | Google + GitHub providers |
| 4 | JWT implementation | Token generation, refresh, validation |
| 5 | Frontend auth | Login page, protected routes, context |

**Key Files:**
- `portal-backend/api/auth/*`
- `portal-frontend/src/contexts/AuthContext.tsx`
- `portal-frontend/src/pages/Login.tsx`

### Week 88: Feature Request Flow

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1-2 | Feature content type | Strapi model, validation, API |
| 3 | Integration service | PortalIntegrationService, sync |
| 4 | Feature form UI | React form, file upload |
| 5 | Status tracking | Status updates, history view |

**Key Files:**
- `portal-backend/api/feature/*`
- `backend/app/services/portal_integration_service.py`
- `portal-frontend/src/pages/FeatureRequest.tsx`

### Week 89: Progress & Test Integration

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1-2 | WebSocket setup | Real-time updates, channels |
| 3 | Test results API | Sync from Tessa, display format |
| 4 | Progress dashboard | Timeline view, status cards |
| 5 | Notifications | Email templates, WebSocket alerts |

**Key Files:**
- `backend/app/api/portal_websocket.py`
- `backend/app/services/portal_notification_service.py`
- `portal-frontend/src/pages/Progress.tsx`

### Week 90: UI Polish & Roadmap

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1 | Voting system | Upvote/downvote, ranking |
| 2 | Comments | Threaded comments, mentions |
| 3 | Roadmap view | Drag-drop, release grouping |
| 4 | UI polish | Responsive design, dark mode |
| 5 | Documentation | User guide, API docs |

**Key Files:**
- `portal-frontend/src/components/Voting.tsx`
- `portal-frontend/src/pages/Roadmap.tsx`
- `docs/user-guide/client-portal.md`

---

## Customer Experience Suggestions

### 1. Smart Notifications

| Event | Notification Type | Content |
|-------|-------------------|---------|
| Status change | Email + Push | "Your feature '{title}' is now in development!" |
| Sprint assigned | Email | "Your feature is planned for Sprint 23 (Dec 25 - Jan 5)" |
| Test results | Push | "Testing complete: 15/15 tests passed!" |
| Release | Email + Push | "Your feature is now live in v2.3.0!" |

### 2. Progress Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│  Feature: "Add dark mode toggle"                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ● Submitted           Dec 15, 2025 10:30                       │
│  ┃                                                               │
│  ● Analyzing           Dec 15, 2025 10:35  (5 min)              │
│  ┃  Peter classified as "ENHANCEMENT"                           │
│  ┃                                                               │
│  ● Backlog             Dec 15, 2025 10:40  (5 min)              │
│  ┃  Mapped to Epic: "UI/UX Improvements"                         │
│  ┃                                                               │
│  ● Planned             Dec 18, 2025 09:00  (3 days)             │
│  ┃  Sprint 23 (Dec 25 - Jan 5)                                   │
│  ┃                                                               │
│  ◐ Building            Dec 25, 2025 09:00  ← Current            │
│  ┃  Estimated completion: Dec 28                                 │
│  ┃                                                               │
│  ○ Testing             -                                         │
│  ○ Released            -                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Test Results View

```
┌─────────────────────────────────────────────────────────────────┐
│  Test Results for "Add dark mode toggle"                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Overall: 15/15 PASSED ✅        Coverage: 87%                   │
│  Duration: 45.2s                 Last run: Dec 28, 2025 14:30    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Unit Tests (10/10) ✅                                      ││
│  │  ├─ DarkModeToggle.test.tsx         ✅ 120ms               ││
│  │  ├─ ThemeContext.test.tsx           ✅ 85ms                ││
│  │  └─ ... 8 more                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  E2E Tests (5/5) ✅                                         ││
│  │  ├─ toggle-dark-mode.spec.ts        ✅ 3.2s                ││
│  │  ├─ persist-preference.spec.ts      ✅ 2.8s                ││
│  │  └─ ... 3 more                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Gamification Elements

- **Vote Badges**: "Top Contributor", "Feature Champion"
- **Status Celebrations**: Confetti animation on release
- **Progress Milestones**: Celebrate 25%, 50%, 75% completion
- **Community Recognition**: "Most Voted Feature of the Month"

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| **Rate Limiting** | 100 requests/min per user, 10 feature creates/day |
| **Input Validation** | Strapi built-in + custom validators |
| **XSS Prevention** | React sanitization, CSP headers |
| **CSRF** | Double-submit cookie pattern |
| **Data Exposure** | Role-based field filtering in responses |
| **OAuth Security** | State parameter, PKCE for mobile |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](../../ARCHITECTURE.md) | Platform architecture |
| [ROADMAP.md](../../ROADMAP.md) | Week 87-90 planning |
| [AGENTS.md](../../AGENTS.md) | Agent roles in portal |
| [Kanban System](./kanban-system.md) | Integration target |
| [WebSocket API](./websocket-api.md) | Real-time updates |

---

**Last Updated:** 2025-12-19
**Version:** 1.0
**Status:** PLANNED
