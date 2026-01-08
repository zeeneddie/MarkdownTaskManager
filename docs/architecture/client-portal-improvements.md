# Client Portal 2.0 - Customer Experience Improvements

**Version:** 1.0
**Status:** PLANNED (Week 115-122)
**Datum:** 2025-12-25
**Priority:** P0-P3

---

## Executive Summary

Verbeteringsplan voor de Client Portal gebaseerd op het principe dat AI-systemen playbooks, repetitie, performance, process en automation moeten afhandelen, zodat klanten zich kunnen focussen op resultaten en relaties.

**Kernvisie:** Van "klant zoekt informatie" naar "informatie vindt klant"

---

## Huidige Stand (Week 90 COMPLETE)

| Feature | Status | Kwaliteit | Gap |
|---------|--------|-----------|-----|
| Authentication (OAuth2/JWT) | ✅ | Goed | - |
| Feature Request Form | ✅ | Basis | Geen duplicate detectie |
| Real-time Progress (WebSocket) | ✅ | Goed | Technische taal |
| Test Results Display | ✅ | Basis | Geen context |
| Voting/Comments | ✅ | Basis | Geen gamification |
| Roadmap View | ✅ | Basis | Geen ETA's |
| Analysis Queue | ✅ | Goed | - |
| Public Roadmaps | ✅ | Basis | Geen personalisatie |

---

## Improvement Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLIENT PORTAL 2.0 ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LAYER 1: PROACTIVE COMMUNICATION                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  NotificationDispatcher → Email | Push | SMS | In-App                   ││
│  │  Diana Agent → Human-friendly message generation                        ││
│  │  Preference Engine → Per-user notification configuration                ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  LAYER 2: TRANSPARENCY & PREDICTION                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  ETA Calculator → Sprint velocity + Eliza estimation                    ││
│  │  Impact Previewer → Felix analysis + affected components                ││
│  │  Journey Tracker → Complete customer lifecycle visibility               ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  LAYER 3: SELF-SERVICE & CONTROL                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Priority Boost System → Customer-controlled prioritization             ││
│  │  Duplicate Detector → Similar request suggestions                       ││
│  │  Feedback Loop → Post-release satisfaction tracking                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  LAYER 4: ENGAGEMENT & RECOGNITION                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Gamification Engine → Badges, levels, recognition                      ││
│  │  Personalized Dashboard → Tailored experience per user                  ││
│  │  Conversational Interface → LLM-powered chatbot                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Proactive Communication (Week 115-116)

### 1.1 Notification Dispatcher Service

**Priority:** P0 | **Effort:** 16 uur | **Impact:** ZEER HOOG

```python
# backend/app/services/notification_dispatcher_service.py

class NotificationDispatcherService:
    """
    Central notification hub for all customer communications.
    Respects user preferences and ensures timely delivery.
    """

    CHANNELS = ["email", "push", "sms", "in_app"]

    async def dispatch(
        self,
        user_id: str,
        event_type: str,
        payload: dict
    ) -> NotificationResult:
        """
        Dispatch notification based on user preferences.

        Event types:
        - feature_status_changed
        - sprint_assigned
        - test_completed
        - feature_released
        - feedback_requested
        """
        preferences = await self.get_user_preferences(user_id)
        channels = self._get_channels_for_event(event_type, preferences)

        results = []
        for channel in channels:
            result = await self._send(channel, user_id, payload)
            results.append(result)

        return NotificationResult(
            success=all(r.success for r in results),
            channels_used=channels
        )
```

**Database Extension:**

```sql
-- Migration: add_notification_preferences
CREATE TABLE notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL UNIQUE,
    email_digest VARCHAR(20) DEFAULT 'daily',  -- 'instant', 'daily', 'weekly', 'off'
    push_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    sms_phone VARCHAR(20),
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    event_preferences JSONB DEFAULT '{
        "feature_status_changed": ["in_app"],
        "sprint_assigned": ["email", "in_app"],
        "test_completed": ["in_app"],
        "feature_released": ["email", "push", "in_app"],
        "feedback_requested": ["email"]
    }',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### 1.2 Human-Friendly Message Generation

**Priority:** P0 | **Effort:** 8 uur | **Impact:** HOOG

Diana agent genereert klant-vriendelijke berichten in plaats van technische statussen.

| Technisch (nu) | Menselijk (nieuw) |
|----------------|-------------------|
| `status: analyzing` | "Peter is je verzoek aan het analyseren. Dit duurt meestal 5-10 minuten." |
| `status: testing` | "Tessa test je feature! 10 van 15 tests geslaagd. Verwacht over 30 min klaar." |
| `status: code_review` | "Quinn controleert de code kwaliteit. Tot nu toe ziet het er goed uit!" |
| `status: released` | "Gefeliciteerd! Je dark mode is nu live in versie 2.3.0. Probeer het nu!" |

```python
# backend/app/services/portal_message_service.py

class PortalMessageService:
    """Generate human-friendly messages via Diana agent."""

    MESSAGE_TEMPLATES = {
        "analyzing": {
            "title": "Je verzoek wordt geanalyseerd",
            "body": "{agent_name} is je verzoek aan het analyseren. Dit duurt meestal {avg_duration}.",
            "emoji": "🔍"
        },
        "testing": {
            "title": "Tests worden uitgevoerd",
            "body": "{agent_name} test je feature! {passed}/{total} tests geslaagd. {eta}",
            "emoji": "🧪"
        },
        "released": {
            "title": "Je feature is live!",
            "body": "Gefeliciteerd! {feature_name} is nu beschikbaar in versie {version}.",
            "emoji": "🎉",
            "cta": "Probeer het nu →"
        }
    }

    async def generate_message(
        self,
        status: str,
        context: dict,
        language: str = "nl"
    ) -> PortalMessage:
        """Generate contextual, friendly message."""
        template = self.MESSAGE_TEMPLATES.get(status)

        # Optional: Use Diana for complex/custom messages
        if context.get("custom_message_needed"):
            return await self.diana_generate(status, context, language)

        return PortalMessage(
            title=template["title"],
            body=template["body"].format(**context),
            emoji=template["emoji"],
            cta=template.get("cta")
        )
```

---

### 1.3 ETA Calculator Service

**Priority:** P0 | **Effort:** 12 uur | **Impact:** HOOG

```python
# backend/app/services/eta_calculator_service.py

class ETACalculatorService:
    """
    Calculate estimated time to completion based on:
    - Historical sprint velocity
    - Eliza's estimation
    - Current queue position
    - Agent availability
    """

    async def calculate_eta(
        self,
        feature_id: str,
        current_status: str
    ) -> ETAResult:
        """Calculate ETA for feature completion."""

        # Get historical data
        velocity = await self.get_sprint_velocity()
        queue_position = await self.get_queue_position(feature_id)
        story_points = await self.get_story_points(feature_id)

        # Calculate remaining work
        remaining_statuses = self._get_remaining_statuses(current_status)

        # Eliza estimation for complex features
        if story_points > 5:
            eliza_estimate = await self.eliza_service.estimate(feature_id)
            confidence = eliza_estimate.confidence
        else:
            eliza_estimate = None
            confidence = 0.8

        # Calculate ETA
        eta_hours = self._calculate_hours(
            story_points=story_points,
            velocity=velocity,
            queue_position=queue_position,
            remaining_statuses=remaining_statuses
        )

        return ETAResult(
            estimated_completion=datetime.now() + timedelta(hours=eta_hours),
            confidence=confidence,
            breakdown={
                "queue_wait": f"{queue_position * 2} hours",
                "development": f"{story_points * velocity} hours",
                "testing": "2-4 hours",
                "review": "1-2 hours"
            }
        )
```

---

## Phase 2: Transparency & Control (Week 117-118)

### 2.1 Impact Preview Service

**Priority:** P1 | **Effort:** 16 uur | **Impact:** HOOG

```
Feature: "Add dark mode toggle"
┌─────────────────────────────────────────────────────┐
│  IMPACT PREVIEW                                     │
├─────────────────────────────────────────────────────┤
│  📊 Effort: 3 story points (~12 uur dev)           │
│  🎯 Affected screens: 15                            │
│  👥 Users benefited: ~2,400 (60% actieve users)    │
│  ⚡ Performance impact: Neutraal                    │
│                                                     │
│  Agent Analysis by: Felix (Architect)               │
│  Confidence: 87%                                    │
└─────────────────────────────────────────────────────┘
```

```python
# backend/app/services/impact_preview_service.py

class ImpactPreviewService:
    """Generate impact preview for feature requests using Felix agent."""

    async def generate_preview(self, feature_id: str) -> ImpactPreview:
        # Get Felix analysis
        felix_analysis = await self.felix_service.analyze_feature(feature_id)

        # Calculate user impact
        user_impact = await self.calculate_user_impact(
            affected_components=felix_analysis.affected_components
        )

        return ImpactPreview(
            effort_story_points=felix_analysis.story_points,
            effort_hours=felix_analysis.story_points * 4,  # avg 4h per SP
            affected_screens=len(felix_analysis.affected_screens),
            users_benefited=user_impact.count,
            users_percentage=user_impact.percentage,
            performance_impact=felix_analysis.performance_assessment,
            agent="Felix (Architect)",
            confidence=felix_analysis.confidence
        )
```

---

### 2.2 Priority Boost System

**Priority:** P1 | **Effort:** 12 uur | **Impact:** MEDIUM-HOOG

```sql
-- Migration: add_priority_boost_system
CREATE TABLE priority_boosts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    feature_id VARCHAR(100) NOT NULL,
    boost_type VARCHAR(20) DEFAULT 'standard',  -- 'standard', 'urgent'
    applied_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(user_id, feature_id)
);

CREATE TABLE boost_allowances (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL UNIQUE,
    monthly_boosts INTEGER DEFAULT 2,
    boosts_used INTEGER DEFAULT 0,
    tier VARCHAR(20) DEFAULT 'standard',  -- affects monthly_boosts
    reset_date DATE DEFAULT (DATE_TRUNC('month', NOW()) + INTERVAL '1 month'),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**UI Component:**

```
┌─────────────────────────────────────────────────────┐
│  Mijn Feature Requests                              │
├─────────────────────────────────────────────────────┤
│  ⬆️ Priority Boost beschikbaar: 2 van 2            │
│                                                     │
│  #123 Dark Mode Toggle      ★★★☆☆  [BOOST ⬆️]      │
│  #124 Export to PDF         ★★☆☆☆  [BOOST ⬆️]      │
│  #125 Multi-language        ★★★★☆  (geboost)       │
│                                                     │
│  ℹ️ Boost = +2 priority sterren, geldig 30 dagen   │
└─────────────────────────────────────────────────────┘
```

---

### 2.3 Duplicate Detection Service

**Priority:** P1 | **Effort:** 16 uur | **Impact:** HOOG

```python
# backend/app/services/duplicate_detection_service.py

class DuplicateDetectionService:
    """
    Detect similar feature requests using:
    1. Title similarity (fuzzy matching)
    2. Description embedding similarity (ChromaDB)
    3. Tag overlap
    """

    SIMILARITY_THRESHOLD = 0.75

    async def find_similar(
        self,
        title: str,
        description: str,
        tags: List[str]
    ) -> List[SimilarFeature]:
        """Find similar existing feature requests."""

        # 1. Fuzzy title matching
        title_matches = await self._fuzzy_title_search(title)

        # 2. Semantic similarity via ChromaDB
        embedding = await self.embedding_service.embed(description)
        semantic_matches = await self.chromadb.query(
            collection="feature_requests",
            query_embeddings=[embedding],
            n_results=5
        )

        # 3. Tag overlap
        tag_matches = await self._tag_overlap_search(tags)

        # Combine and rank
        combined = self._merge_results(
            title_matches,
            semantic_matches,
            tag_matches
        )

        return [
            SimilarFeature(
                id=match.id,
                title=match.title,
                similarity_score=match.score,
                votes=match.vote_count,
                status=match.status,
                author=match.author_name
            )
            for match in combined
            if match.score >= self.SIMILARITY_THRESHOLD
        ]
```

**UI Flow:**

```
Bij nieuw feature request:

"Je feature lijkt op 3 bestaande requests:"
┌─────────────────────────────────────────────────────┐
│  #89 Dark Theme (Jan) - 23 votes ⬆️                │
│       Similarity: 92% | Status: In Development     │
│                                                     │
│  #102 Night Mode (Lisa) - 12 votes                 │
│       Similarity: 85% | Status: Backlog            │
│                                                     │
│  #115 OLED Mode (Mark) - 8 votes                   │
│       Similarity: 78% | Status: Submitted          │
├─────────────────────────────────────────────────────┤
│  [Voeg stem toe aan #89] [Toch nieuw request →]    │
└─────────────────────────────────────────────────────┘
```

---

## Phase 3: Engagement & Recognition (Week 119-120)

### 3.1 Feedback Loop Closure

**Priority:** P1 | **Effort:** 12 uur | **Impact:** HOOG

Post-release satisfaction tracking:

```python
# backend/app/services/feedback_loop_service.py

class FeedbackLoopService:
    """
    Close the feedback loop after feature release.
    Triggers: 48h after release, 7 days after release.
    """

    FEEDBACK_TRIGGERS = [
        {"hours_after_release": 48, "type": "initial"},
        {"hours_after_release": 168, "type": "followup"}  # 7 days
    ]

    async def request_feedback(
        self,
        feature_id: str,
        trigger_type: str
    ) -> FeedbackRequest:
        """Send feedback request to feature requester."""

        feature = await self.get_feature(feature_id)

        return FeedbackRequest(
            feature_id=feature_id,
            user_id=feature.author_id,
            question="Hoe werkt {feature_name} voor jou?".format(
                feature_name=feature.title
            ),
            options=[
                {"emoji": "😍", "label": "Perfect!", "value": 5},
                {"emoji": "😊", "label": "Goed, kleine issues", "value": 4},
                {"emoji": "😐", "label": "Niet wat ik verwachtte", "value": 2},
                {"emoji": "😞", "label": "Werkt niet goed", "value": 1}
            ],
            allow_comment=True,
            expires_at=datetime.now() + timedelta(days=14)
        )

    async def process_feedback(
        self,
        feature_id: str,
        rating: int,
        comment: Optional[str]
    ) -> None:
        """Process received feedback."""

        # Store feedback
        await self.store_feedback(feature_id, rating, comment)

        # If negative, trigger follow-up
        if rating <= 2:
            await self.trigger_followup(feature_id, comment)

        # Update satisfaction metrics
        await self.update_csat_metrics(feature_id, rating)
```

---

### 3.2 Gamification Engine

**Priority:** P2 | **Effort:** 20 uur | **Impact:** MEDIUM

```sql
-- Migration: add_gamification_system
CREATE TABLE user_badges (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    badge_type VARCHAR(50) NOT NULL,
    earned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, badge_type)
);

CREATE TABLE badge_definitions (
    id SERIAL PRIMARY KEY,
    badge_type VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    emoji VARCHAR(10),
    criteria JSONB NOT NULL,
    reward JSONB,
    tier INTEGER DEFAULT 1  -- bronze, silver, gold
);

-- Insert badge definitions
INSERT INTO badge_definitions (badge_type, name, emoji, criteria, reward) VALUES
('pioneer', 'Pioneer', '🌟', '{"feature_requests": 10}', '{"changelog_mention": true}'),
('community_voice', 'Community Voice', '🗳️', '{"votes_given": 50}', '{"priority_boosts": 1}'),
('innovator', 'Innovator', '💡', '{"features_implemented": 3}', '{"beta_access": true}'),
('bug_hunter', 'Bug Hunter', '🐛', '{"bugs_reported": 5}', '{"direct_line": "betty"}'),
('power_user', 'Power User', '⚡', '{"login_streak_days": 30}', '{"early_access": true}');
```

**Badge Display:**

```
┌─────────────────────────────────────────────────────┐
│  JOUW BADGES                                        │
├─────────────────────────────────────────────────────┤
│  🌟 Pioneer          - Eerste 10 feature requests  │
│  🗳️ Community Voice  - 50+ votes gegeven           │
│  💡 Innovator        - 3 features geïmplementeerd  │
│                                                     │
│  VOLGENDE BADGE:                                    │
│  🐛 Bug Hunter [███░░░░░░░] 3/5 bugs gerapporteerd │
└─────────────────────────────────────────────────────┘
```

---

### 3.3 Personalized Dashboard

**Priority:** P2 | **Effort:** 16 uur | **Impact:** MEDIUM

```python
# backend/app/services/personalized_dashboard_service.py

class PersonalizedDashboardService:
    """Generate personalized dashboard content per user."""

    async def get_dashboard(self, user_id: str) -> PersonalizedDashboard:
        """Get personalized dashboard data."""

        user = await self.get_user(user_id)
        stats = await self.get_user_stats(user_id)
        recommendations = await self.get_recommendations(user_id)

        return PersonalizedDashboard(
            welcome_message=f"Welkom terug, {user.first_name}!",
            impact_summary=ImpactSummary(
                features_contributed=stats.total_features,
                features_implemented=stats.implemented_features,
                implementation_rate=stats.implementation_rate,
                votes_received=stats.total_votes,
                user_level=self._calculate_level(stats)
            ),
            active_features=await self.get_active_features(user_id),
            recommendations=recommendations,
            badges=await self.get_badges(user_id),
            recent_activity=await self.get_recent_activity(user_id)
        )

    async def get_recommendations(self, user_id: str) -> List[Recommendation]:
        """Get personalized feature recommendations."""

        # Analyze user's past interests
        interests = await self.analyze_interests(user_id)

        # Find matching features in backlog
        matching = await self.find_matching_features(interests)

        return [
            Recommendation(
                feature_id=f.id,
                title=f.title,
                reason=f"Past bij jouw interesse in {f.category}",
                match_score=f.match_score
            )
            for f in matching[:5]
        ]
```

---

## Phase 4: Advanced Features (Week 121-122)

### 4.1 Conversational Interface

**Priority:** P3 | **Effort:** 24 uur | **Impact:** MEDIUM-HOOG

```python
# backend/app/services/portal_chatbot_service.py

class PortalChatbotService:
    """
    LLM-powered conversational interface for portal.
    Uses Peter agent for understanding, Diana for response generation.
    """

    async def handle_message(
        self,
        user_id: str,
        message: str
    ) -> ChatResponse:
        """Process user message and generate response."""

        # Classify intent
        intent = await self.classify_intent(message)

        if intent.type == "status_query":
            # Get feature status
            features = await self.get_user_features(user_id)
            matching = self._find_matching_feature(message, features)

            if matching:
                status = await self.get_detailed_status(matching.id)
                return await self.generate_status_response(status)

        elif intent.type == "eta_query":
            feature = self._extract_feature_reference(message)
            eta = await self.eta_service.calculate_eta(feature.id)
            return await self.generate_eta_response(eta)

        elif intent.type == "new_request":
            return ChatResponse(
                message="Ik help je graag met een nieuw verzoek! "
                        "Wat wil je graag toegevoegd zien?",
                action="start_feature_request_flow"
            )

        # Fallback to general assistant
        return await self.diana_generate_response(message, user_id)
```

**Example Conversations:**

```
💬 User: "Hoe staat het met mijn dark mode request?"

🤖 Bot: "Hey Jan! Je dark mode request (#123) is in de test fase.
        Tessa heeft 12 van 15 tests afgerond - allemaal geslaagd!
        Verwachte release: vrijdag 27 december.

        Wil je een notificatie als het live gaat? [Ja] [Nee]"

---

💬 User: "Wanneer komt de export functie?"

🤖 Bot: "Je export to PDF request (#124) staat gepland voor Sprint 24
        (start 3 januari). Op basis van onze velocity verwacht ik
        dat het rond 15 januari live gaat.

        Wil je een priority boost gebruiken? Je hebt er nog 2 deze maand."
```

---

### 4.2 Customer Journey Analytics

**Priority:** P3 | **Effort:** 20 uur | **Impact:** MEDIUM

```sql
-- Migration: add_customer_journey_analytics
CREATE TABLE journey_events (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    feature_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_journey_user ON journey_events(user_id);
CREATE INDEX ix_journey_type ON journey_events(event_type);
CREATE INDEX ix_journey_feature ON journey_events(feature_id);

-- Event types:
-- portal_visit, feature_view, feature_create, feature_vote,
-- status_check, notification_click, feedback_submit,
-- chatbot_interaction, settings_change
```

**Funnel Analysis:**

```
Awareness → Request → Analysis → Sprint → Build → Test → Release → Satisfaction
    │          │          │         │        │       │        │          │
   100%       45%        40%       35%      30%     28%      25%        22%
    │          │          │         │        │       │        │          │
    └──────────┴──────────┴─────────┴────────┴───────┴────────┴──────────┘
                              Conversion Funnel

Drop-off Analysis:
- Awareness → Request: 55% drop (improve onboarding)
- Sprint → Build: 5% drop (capacity issue)
- Release → Satisfaction: 3% drop (feedback loop gap)
```

---

## API Endpoints (New)

### Notification Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portal/notifications/preferences` | GET/PUT | User notification preferences |
| `/api/portal/notifications/history` | GET | Notification history |
| `/api/portal/notifications/test` | POST | Send test notification |

### ETA & Impact

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portal/features/{id}/eta` | GET | Get feature ETA |
| `/api/portal/features/{id}/impact` | GET | Get impact preview |
| `/api/portal/features/{id}/journey` | GET | Get feature journey |

### Priority & Boost

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portal/boosts/allowance` | GET | Get user's boost allowance |
| `/api/portal/features/{id}/boost` | POST | Apply priority boost |
| `/api/portal/boosts/history` | GET | Boost usage history |

### Duplicates & Similar

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portal/features/similar` | POST | Find similar features |
| `/api/portal/features/{id}/merge` | POST | Merge with existing |

### Feedback

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portal/features/{id}/feedback` | GET/POST | Feature feedback |
| `/api/portal/feedback/pending` | GET | Pending feedback requests |

### Gamification

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portal/badges` | GET | Available badges |
| `/api/portal/users/{id}/badges` | GET | User's earned badges |
| `/api/portal/users/{id}/level` | GET | User level & progress |

### Dashboard

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portal/dashboard` | GET | Personalized dashboard |
| `/api/portal/recommendations` | GET | Feature recommendations |

### Chatbot

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portal/chat` | POST | Send chat message |
| `/api/portal/chat/history` | GET | Chat history |

---

## Database Migrations

| Migration | Tables | Purpose |
|-----------|--------|---------|
| `051_add_notification_preferences.py` | notification_preferences | User notification settings |
| `052_add_priority_boost_system.py` | priority_boosts, boost_allowances | Priority boost tracking |
| `053_add_gamification_system.py` | user_badges, badge_definitions | Gamification |
| `054_add_journey_analytics.py` | journey_events | Customer journey tracking |
| `055_add_feedback_loop.py` | feature_feedback, feedback_requests | Post-release feedback |

---

## Integration with Existing Systems

### Agent Integration

| Agent | Portal Role |
|-------|-------------|
| **Diana** | Human-friendly message generation |
| **Peter** | Feature classification, chatbot intent |
| **Felix** | Impact analysis, effort estimation |
| **Eliza** | ETA calculation, story points |
| **Paul** | Sprint assignment communication |
| **Tessa** | Test progress updates |

### Workflow Integration

| Workflow | Portal Trigger |
|----------|----------------|
| `FEATURE_REQUEST` | New feature submitted |
| `BACKLOG_GENERATION` | Similar features detected |
| `QUALITY_AUDIT` | Post-release feedback < 3 |

### Unified Improvement Plan Integration

| Pattern | Portal Application |
|---------|-------------------|
| **Check Alignment (MP-QW-1)** | Agents confirm understanding with customer |
| **Active Partner (MP-QW-2)** | Agents push back on infeasible requests |
| **Feedback Loop Autonomy (MP-QW-3)** | Customer sets "iterate until satisfied" |
| **HATEOAG Navigation (AO-QW-1)** | Journey visible via hyperlinks |
| **Hypothesize Pattern (AO-QW-4)** | Agents state expectations upfront |

---

## Success Metrics

### Customer Experience KPIs

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Time to first response | 24h | 5 min | -99.6% |
| Status check visits/week | 3 | 0.5 | -83% |
| Support tickets (status) | 25% | <5% | -80% |
| Feature request duplicates | 30% | <10% | -67% |
| Post-release CSAT | 70% | 90% | +29% |
| Feature adoption rate | 40% | 75% | +88% |
| NPS (Net Promoter Score) | +20 | +50 | +150% |

### Engagement KPIs

| Metric | Current | Target |
|--------|---------|--------|
| Monthly active portal users | 40% | 70% |
| Votes per feature (avg) | 5 | 15 |
| Comments per feature (avg) | 2 | 8 |
| Badge earn rate | 0% | 50% |
| Chatbot usage | 0% | 30% |

---

## Implementation Roadmap

### Week 115-116: Phase 1 (P0)

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1-2 | Notification Dispatcher | Service + API + Preferences UI |
| 3 | Message Generation | Diana integration + Templates |
| 4-5 | ETA Calculator | Service + API + UI integration |

**Effort:** 36 uur

### Week 117-118: Phase 2 (P1)

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1-2 | Impact Preview | Felix integration + UI component |
| 3-4 | Priority Boost | Service + API + UI |
| 5 | Duplicate Detection | ChromaDB integration + UI flow |

**Effort:** 44 uur

### Week 119-120: Phase 3 (P2)

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1-2 | Feedback Loop | Service + Email templates + UI |
| 3-4 | Gamification | Badge system + Level progression |
| 5 | Personalized Dashboard | Service + UI components |

**Effort:** 48 uur

### Week 121-122: Phase 4 (P3)

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1-3 | Conversational Interface | LLM chatbot + UI |
| 4-5 | Journey Analytics | Tracking + Dashboard |

**Effort:** 44 uur

**Total Effort:** 172 uur (~4.5 weken full-time)

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [client-portal.md](./client-portal.md) | Original portal architecture |
| [AGENTS.md](../../AGENTS.md) | Agent system reference |
| [ROADMAP.md](../../ROADMAP.md) | Project timeline |
| [UNIFIED_IMPROVEMENT_PLAN.md](../planning/UNIFIED_IMPROVEMENT_PLAN.md) | Pattern integration |

---

**Last Updated:** 2025-12-25
**Version:** 1.0
**Status:** PLANNED
**Author:** AI Agent System
