# Definition of Done (DoD) Checklist System

**Datum:** 2025-11-12
**Gebaseerd op:** BMAD-Method checklists
**Doel:** Quality gates voor workflow progression

---

## 🎯 Concept

**Definition of Done checklists voorkomen dat work items naar de volgende fase gaan voordat ze volledig klaar zijn. Elke work item type (Epic/Feature/Story/Task) heeft zijn eigen DoD checklist.**

**Principe:**
- ✅ DoD 100% compleet → Item kan naar volgende status
- ❌ DoD incomplete → Item geblokkeerd
- 🤖 Agents valideren DoD automatisch
- 👤 Human kan override met reden

---

## 📋 DoD per Work Item Type

### Epic DoD (PLANNED → IN PROGRESS)

**Bestand:** `epics/EPIC-001.md`

```markdown
---
id: EPIC-001
type: epic
title: Payment Integration
status: PLANNED
dod_status: incomplete  # incomplete | complete | overridden
dod_completion: 60      # 0-100%
---

# EPIC-001: Payment Integration

## ✅ Definition of Done

### Business Requirements
- [ ] Business value clearly defined and quantified
- [ ] Success metrics defined (KPIs)
- [ ] Target date agreed with stakeholders
- [ ] Budget approved
- [ ] ROI calculated

### Architecture
- [x] Architecture review completed by Software Architect Agent
- [x] ADR created for major decisions (ADR-017)
- [x] Security implications assessed
- [ ] Performance requirements defined
- [ ] Scalability requirements defined

### Planning
- [x] Epic broken down into Features by Feature Architect
- [x] All Features estimated (Function Points)
- [ ] Dependencies identified and documented
- [ ] Risks identified with mitigation plan
- [ ] Sprint allocation planned

### Team
- [x] Owner assigned (@eddie)
- [ ] Team capacity validated
- [ ] Required skills available
- [ ] External dependencies confirmed

### Documentation
- [ ] Epic description complete
- [x] User journey documented
- [ ] Technical design documented
- [ ] API contracts defined (if applicable)

---

**DoD Status:** ❌ INCOMPLETE (60% complete)
**Blockers:**
- Business: Success metrics not yet defined
- Architecture: Performance requirements missing
- Planning: Risks not documented
- Team: Team capacity not validated
- Documentation: Technical design incomplete

**Action Required:** Complete 5 remaining items before moving to IN PROGRESS
**Responsible:** @eddie
**Due:** 2025-11-15
```

**Automated Check:**
```python
def validate_epic_dod(epic_id: str) -> DoD_Result:
    """Validate Epic DoD before status change"""

    epic = load_epic(epic_id)
    checklist = epic["dod_checklist"]

    required_categories = [
        "Business Requirements",
        "Architecture",
        "Planning",
        "Team",
        "Documentation"
    ]

    results = {
        "total_items": 0,
        "completed_items": 0,
        "categories": {}
    }

    for category in required_categories:
        items = checklist[category]
        total = len(items)
        completed = sum(1 for item in items if item["checked"])

        results["categories"][category] = {
            "total": total,
            "completed": completed,
            "percentage": (completed / total * 100) if total > 0 else 0,
            "incomplete_items": [item["text"] for item in items if not item["checked"]]
        }

        results["total_items"] += total
        results["completed_items"] += completed

    results["percentage"] = (results["completed_items"] / results["total_items"] * 100)
    results["complete"] = results["percentage"] == 100

    return results
```

---

### Feature DoD (PLANNED → IN PROGRESS)

```markdown
---
id: FEATURE-001
parent_id: EPIC-001
status: PLANNED
dod_status: complete
dod_completion: 100
---

# FEATURE-001: Stripe API Integration

## ✅ Definition of Done

### Requirements
- [x] Functional requirements documented
- [x] Non-functional requirements defined (performance, security)
- [x] Acceptance criteria agreed with Product Owner
- [x] Edge cases identified

### Design
- [x] Technical design completed
- [x] API endpoints defined
- [x] Data models designed
- [x] Database schema changes planned (if applicable)
- [x] Architecture review passed

### Planning
- [x] Feature broken down into Stories
- [x] All Stories estimated (Story Points)
- [x] Sprint assigned (Sprint 15)
- [x] Dependencies on other Features identified
- [x] Test strategy defined

### Security & Compliance
- [x] Security review completed
- [x] PCI compliance requirements documented
- [x] Data privacy assessed (GDPR)
- [x] Authentication/authorization design approved

### Infrastructure
- [x] Required infrastructure identified
- [x] Third-party services documented (Stripe)
- [x] API keys/credentials process defined
- [x] Monitoring plan created

---

**DoD Status:** ✅ COMPLETE (100%)
**Ready to Start:** YES
**Approved By:** Software Architect Agent (2025-11-12)
```

---

### Story DoD (PLANNED → IN PROGRESS)

```markdown
---
id: STORY-001
parent_id: FEATURE-001
status: PLANNED
dod_status: complete
dod_completion: 100
---

# STORY-001: Setup Stripe SDK

## ✅ Definition of Done (Start)

### Story Ready
- [x] User story follows "As a... I want... So that..." format
- [x] Acceptance criteria defined (4 criteria)
- [x] Story points estimated (5 SP)
- [x] Sprint assigned (Sprint 15)
- [x] Assignee confirmed (@eddie)

### Technical
- [x] Technical approach agreed
- [x] Broken down into Tasks (4 tasks)
- [x] Dependencies identified (none)
- [x] Testability confirmed

### Resources
- [x] Developer available (40% capacity this sprint)
- [x] Required tools/access available (Stripe test account)
- [x] Documentation available (Stripe docs)

---

**DoD Status (Start):** ✅ COMPLETE (100%)
**Ready to Start:** YES
```

### Story DoD (IN PROGRESS → COMPLETED)

```markdown
## ✅ Definition of Done (Completion)

### Implementation
- [x] Code written and follows coding standards
- [x] Code reviewed by peer (@alice)
- [x] No code smells (SonarQube passed)
- [x] Cyclomatic complexity ≤15
- [x] No hardcoded secrets

### Testing
- [x] Unit tests written (5 tests)
- [x] Unit tests pass (100%)
- [x] Code coverage ≥80% (84% achieved)
- [x] Integration tests pass (if applicable)
- [x] Manual testing completed

### Documentation
- [x] Code documented (docstrings)
- [x] README updated (if needed)
- [x] API documentation updated (Swagger)
- [x] Changelog updated

### Quality Gates
- [x] All automated quality gates passed
- [x] No critical/high security vulnerabilities
- [x] Performance benchmarks within tolerance
- [x] Accessibility standards met (if UI)

### Deployment
- [x] Deployed to staging
- [x] Smoke tests passed on staging
- [x] Product Owner acceptance ✅
- [x] Ready for production deployment

---

**DoD Status (Completion):** ✅ COMPLETE (100%)
**Completed:** 2025-11-14
**Deployed to Production:** 2025-11-15
```

---

### Task DoD (TODO → IN PROGRESS → DONE)

**Start DoD (TODO → IN PROGRESS):**
```markdown
## ✅ Definition of Done (Start)

- [x] Task clearly defined
- [x] Estimated hours defined (2h)
- [x] Assignee has time available
- [x] Blockers resolved
- [x] Required access/tools available
```

**Completion DoD (IN PROGRESS → DONE):**
```markdown
## ✅ Definition of Done (Completion)

- [x] Implementation complete
- [x] Self-tested (works locally)
- [x] Committed to git
- [x] PR created (if applicable)
- [x] Actual hours tracked (2h)
```

---

## 🤖 Agent Integration

### 1. DoD Validator Agent

**Nieuw: Agent #10 - DoD Validator**

```python
class DoDValidatorAgent:
    """Validates Definition of Done checklists"""

    def __init__(self):
        self.rules = load_dod_rules()

    async def validate_transition(self, item_id: str, from_status: str, to_status: str) -> ValidationResult:
        """Validate if item can transition to next status"""

        # Get item
        item = await get_item(item_id)
        item_type = item["type"]

        # Get DoD checklist for transition
        dod_checklist = await get_dod_checklist(item_id)

        # Validate based on item type and transition
        if item_type == "epic" and to_status == "IN_PROGRESS":
            result = await self.validate_epic_start_dod(item, dod_checklist)

        elif item_type == "story" and to_status == "IN_PROGRESS":
            result = await self.validate_story_start_dod(item, dod_checklist)

        elif item_type == "story" and to_status == "COMPLETED":
            result = await self.validate_story_completion_dod(item, dod_checklist)

        # Check result
        if result["complete"]:
            return ValidationResult(
                allowed=True,
                message=f"✅ DoD complete ({result['percentage']}%). Transition allowed."
            )
        else:
            blockers = self.get_blockers(result)
            return ValidationResult(
                allowed=False,
                message=f"❌ DoD incomplete ({result['percentage']}%). Cannot transition.",
                blockers=blockers,
                required_actions=self.get_required_actions(blockers)
            )

    async def validate_epic_start_dod(self, epic: Dict, checklist: Dict) -> Dict:
        """Validate Epic start DoD"""

        checks = {
            "business_value_defined": await self.check_business_value(epic),
            "architecture_reviewed": await self.check_architecture_review(epic),
            "features_defined": await self.check_features_exist(epic),
            "features_estimated": await self.check_features_estimated(epic),
            "owner_assigned": epic.get("owner") is not None,
            "sprint_planned": await self.check_sprint_allocation(epic)
        }

        total = len(checks)
        completed = sum(1 for v in checks.values() if v)

        return {
            "complete": completed == total,
            "percentage": (completed / total * 100),
            "checks": checks,
            "incomplete": [k for k, v in checks.items() if not v]
        }

    async def check_architecture_review(self, epic: Dict) -> bool:
        """Check if architecture review was completed"""

        # Look for architecture review in epic metadata
        arch_review = epic.get("architecture_review")

        if not arch_review:
            return False

        # Must be approved and recent (within 30 days)
        if arch_review["status"] != "approved":
            return False

        review_date = arch_review["date"]
        age_days = (datetime.now() - review_date).days

        if age_days > 30:
            # Stale review, needs refresh
            return False

        return True

    def get_blockers(self, validation_result: Dict) -> List[str]:
        """Extract blockers from validation result"""

        blockers = []

        for check_name in validation_result["incomplete"]:
            blocker = self.rules[check_name]["blocker_message"]
            blockers.append(blocker)

        return blockers
```

---

### 2. Software Architect Agent - DoD Enforcement

**Update Software Architect Agent:**

```python
class SoftwareArchitectAgent:
    """Extended with DoD enforcement"""

    async def review_feature(self, feature_id: str) -> ArchitectureReview:
        """Architecture review creates DoD checklist items"""

        review = await self.perform_architecture_review(feature_id)

        # Update DoD checklist based on review
        dod_updates = []

        if review["layered_architecture_ok"]:
            dod_updates.append({
                "category": "Architecture",
                "item": "Architecture review passed",
                "checked": True,
                "reviewer": "Software Architect Agent",
                "date": datetime.now()
            })

        if review["adr_created"]:
            dod_updates.append({
                "category": "Architecture",
                "item": f"ADR created (ADR-{review['adr_number']})",
                "checked": True,
                "link": f"docs/architecture/decisions/ADR-{review['adr_number']}.md"
            })

        if review["security_approved"]:
            dod_updates.append({
                "category": "Security & Compliance",
                "item": "Security review completed",
                "checked": True
            })

        # Update feature's DoD checklist
        await update_dod_checklist(feature_id, dod_updates)

        # Calculate completion percentage
        completion = await calculate_dod_completion(feature_id)

        return {
            "review": review,
            "dod_updates": dod_updates,
            "dod_completion": completion
        }
```

---

### 3. Feature Architect Agent - DoD Initialization

**When Feature Architect creates Epic/Feature:**

```python
class FeatureArchitectAgent:
    """Extended with DoD checklist creation"""

    async def create_epic(self, epic_data: Dict) -> Epic:
        """Create epic with DoD checklist"""

        # Create epic
        epic = await self.generate_epic_breakdown(epic_data)

        # Initialize DoD checklist from template
        dod_checklist = self.load_dod_template("epic_start")

        # Auto-check items that are already done
        if epic.get("features"):
            dod_checklist["Planning"]["Epic broken down into Features"]["checked"] = True
            dod_checklist["Planning"]["Epic broken down into Features"]["date"] = datetime.now()

        if epic.get("owner"):
            dod_checklist["Team"]["Owner assigned"]["checked"] = True

        # Attach DoD to epic
        epic["dod_checklist"] = dod_checklist
        epic["dod_status"] = "incomplete"
        epic["dod_completion"] = self.calculate_completion(dod_checklist)

        # Save epic
        await save_epic(epic)

        # Notify user
        await notify(f"Epic {epic['id']} created. DoD: {epic['dod_completion']}% complete")

        return epic
```

---

## 📄 DoD Template Files

### Template: Epic Start DoD

**Bestand:** `templates/dod/epic_start.yml`

```yaml
# Epic Definition of Done - Start (PLANNED → IN PROGRESS)

Business Requirements:
  - text: "Business value clearly defined and quantified"
    checked: false
    required: true
    auto_checkable: false

  - text: "Success metrics defined (KPIs)"
    checked: false
    required: true
    auto_checkable: false

  - text: "Target date agreed with stakeholders"
    checked: false
    required: true
    auto_checkable: false

  - text: "Budget approved"
    checked: false
    required: true
    auto_checkable: false

  - text: "ROI calculated"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "epic.roi is not None"

Architecture:
  - text: "Architecture review completed by Software Architect Agent"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "epic.architecture_review.status == 'approved'"
    responsible_agent: "Software Architect"

  - text: "ADR created for major decisions"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "epic.adr_count > 0"
    responsible_agent: "Software Architect"

  - text: "Security implications assessed"
    checked: false
    required: true
    auto_checkable: true
    responsible_agent: "Software Architect"

  - text: "Performance requirements defined"
    checked: false
    required: true
    auto_checkable: false

  - text: "Scalability requirements defined"
    checked: false
    required: false  # Optional for small epics
    auto_checkable: false

Planning:
  - text: "Epic broken down into Features"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "len(epic.features) > 0"
    responsible_agent: "Feature Architect"

  - text: "All Features estimated (Function Points)"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "all(f.fp_total > 0 for f in epic.features)"
    responsible_agent: "Estimation Engine"

  - text: "Dependencies identified and documented"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "epic.dependencies is not None"

  - text: "Risks identified with mitigation plan"
    checked: false
    required: true
    auto_checkable: false

  - text: "Sprint allocation planned"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "epic.sprint_allocation is not None"

Team:
  - text: "Owner assigned"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "epic.owner is not None"

  - text: "Team capacity validated"
    checked: false
    required: true
    auto_checkable: false

  - text: "Required skills available"
    checked: false
    required: true
    auto_checkable: false

  - text: "External dependencies confirmed"
    checked: false
    required: false
    auto_checkable: false

Documentation:
  - text: "Epic description complete"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "len(epic.description) > 100"

  - text: "User journey documented"
    checked: false
    required: true
    auto_checkable: false

  - text: "Technical design documented"
    checked: false
    required: true
    auto_checkable: false

  - text: "API contracts defined (if applicable)"
    checked: false
    required: false
    auto_checkable: false
```

---

### Template: Story Completion DoD

**Bestand:** `templates/dod/story_completion.yml`

```yaml
# Story Definition of Done - Completion (IN PROGRESS → COMPLETED)

Implementation:
  - text: "Code written and follows coding standards"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "lint_passed"
    blocker: "Code does not meet coding standards"

  - text: "Code reviewed by peer"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "pr.reviews > 0 and pr.approved"
    blocker: "Code review not completed or not approved"

  - text: "No code smells"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "sonarqube.code_smells == 0"
    blocker: "Code smells detected in SonarQube"

  - text: "Cyclomatic complexity ≤15"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "max_complexity <= 15"
    blocker: "Cyclomatic complexity exceeds limit"

  - text: "No hardcoded secrets"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "security_scan.secrets == 0"
    blocker: "Hardcoded secrets detected"

Testing:
  - text: "Unit tests written"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "unit_tests.count > 0"
    blocker: "No unit tests found"

  - text: "Unit tests pass (100%)"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "unit_tests.pass_rate == 100"
    blocker: "Some unit tests failing"

  - text: "Code coverage ≥80%"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "coverage.percentage >= 80"
    blocker: "Code coverage below 80%"

  - text: "Integration tests pass (if applicable)"
    checked: false
    required: false
    auto_checkable: true
    auto_check_rule: "integration_tests.pass_rate == 100"

  - text: "Manual testing completed"
    checked: false
    required: true
    auto_checkable: false
    blocker: "Manual testing not completed"

Documentation:
  - text: "Code documented (docstrings)"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "doc_coverage >= 80"
    blocker: "Code documentation insufficient"

  - text: "README updated (if needed)"
    checked: false
    required: false
    auto_checkable: false

  - text: "API documentation updated"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "swagger_updated"
    blocker: "API documentation not updated"

  - text: "Changelog updated"
    checked: false
    required: true
    auto_checkable: false
    blocker: "Changelog not updated"

Quality Gates:
  - text: "All automated quality gates passed"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "ci_pipeline.status == 'passed'"
    blocker: "CI/CD pipeline failing"

  - text: "No critical/high security vulnerabilities"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "security_scan.critical == 0 and security_scan.high == 0"
    blocker: "Security vulnerabilities found"

  - text: "Performance benchmarks within tolerance"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "perf_benchmark.within_tolerance"
    blocker: "Performance degradation detected"

  - text: "Accessibility standards met (if UI)"
    checked: false
    required: false
    auto_checkable: true
    auto_check_rule: "lighthouse.accessibility >= 90"

Deployment:
  - text: "Deployed to staging"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "deployment.staging.status == 'success'"
    blocker: "Staging deployment failed"

  - text: "Smoke tests passed on staging"
    checked: false
    required: true
    auto_checkable: true
    auto_check_rule: "smoke_tests.staging.pass_rate == 100"
    blocker: "Smoke tests failing on staging"

  - text: "Product Owner acceptance"
    checked: false
    required: true
    auto_checkable: false
    blocker: "Product Owner has not accepted the story"

  - text: "Ready for production deployment"
    checked: false
    required: true
    auto_checkable: false
    blocker: "Not cleared for production"
```

---

## 🚦 Workflow Integration

### Status Transition Validation

```python
@router.put("/api/stories/{story_id}/status")
async def update_story_status(
    story_id: str,
    new_status: str,
    override: bool = False,
    override_reason: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Update story status with DoD validation"""

    # Get story
    story = await get_story(db, story_id)
    old_status = story.status

    # Validate DoD for transition
    dod_validator = DoDValidatorAgent()
    validation = await dod_validator.validate_transition(
        story_id,
        old_status,
        new_status
    )

    if not validation.allowed:
        if not override:
            # Block transition
            return {
                "success": False,
                "message": validation.message,
                "blockers": validation.blockers,
                "required_actions": validation.required_actions,
                "dod_completion": validation.dod_completion,
                "can_override": True  # Human can override
            }
        else:
            # Override with reason
            if not override_reason:
                raise HTTPException(
                    status_code=400,
                    detail="override_reason required when overriding DoD"
                )

            # Log override
            await log_dod_override(
                story_id=story_id,
                from_status=old_status,
                to_status=new_status,
                dod_completion=validation.dod_completion,
                blockers=validation.blockers,
                override_reason=override_reason,
                overridden_by=current_user.username
            )

            # Send notification
            await notify_team(
                f"⚠️ DoD override: {story_id} moved to {new_status} "
                f"with {validation.dod_completion}% DoD completion. "
                f"Reason: {override_reason}"
            )

    # Update status
    story.status = new_status
    await db.commit()

    # Sync to markdown
    await sync_engine.sync_from_database()

    # Broadcast event
    await websocket_manager.broadcast({
        "type": "StoryStatusChanged",
        "data": {
            "story_id": story_id,
            "old_status": old_status,
            "new_status": new_status,
            "dod_completion": validation.dod_completion
        }
    })

    return {
        "success": True,
        "message": f"Story {story_id} moved to {new_status}",
        "dod_completion": validation.dod_completion
    }
```

---

## 🎨 UI Updates

### DoD Progress Indicator

```html
<!-- In project-manager.html -->

<div class="story-card" data-story-id="STORY-001">
    <div class="story-header">
        <h3>STORY-001: Setup Stripe SDK</h3>
        <span class="status-badge in-progress">IN PROGRESS</span>
    </div>

    <div class="story-body">
        <p>Setup Stripe SDK in backend...</p>
    </div>

    <!-- DoD Progress -->
    <div class="dod-progress">
        <div class="dod-header">
            <span class="dod-label">Definition of Done</span>
            <span class="dod-percentage">85%</span>
        </div>
        <div class="dod-progress-bar">
            <div class="dod-progress-fill" style="width: 85%"></div>
        </div>
        <div class="dod-details">
            <span class="dod-complete">✅ 11/13 items complete</span>
            <button class="dod-view-btn" onclick="viewDoD('STORY-001')">
                View Checklist
            </button>
        </div>
    </div>

    <!-- Move to COMPLETED button -->
    <div class="story-actions">
        <button class="btn-move" onclick="moveToCompleted('STORY-001')" disabled>
            <span class="icon">❌</span> Move to COMPLETED
            <span class="tooltip">DoD not complete (85%)</span>
        </button>
    </div>
</div>

<style>
.dod-progress {
    margin: 10px 0;
    padding: 10px;
    background: #f5f5f5;
    border-radius: 5px;
}

.dod-progress-bar {
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    margin: 8px 0;
    overflow: hidden;
}

.dod-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    transition: width 0.3s ease;
}

.dod-progress-fill[style*="width: 100"] {
    background: #4CAF50;
}

.btn-move:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
</style>

<script>
async function moveToCompleted(storyId) {
    const response = await fetch(`/api/stories/${storyId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_status: 'COMPLETED' })
    });

    const result = await response.json();

    if (!result.success) {
        // DoD not complete - show modal
        showDoDModal(result);
    }
}

function showDoDModal(result) {
    const modal = `
        <div class="modal">
            <h2>❌ Definition of Done Incomplete</h2>
            <p>${result.message}</p>

            <div class="blockers">
                <h3>Blockers (${result.blockers.length}):</h3>
                <ul>
                    ${result.blockers.map(b => `<li>${b}</li>`).join('')}
                </ul>
            </div>

            <div class="required-actions">
                <h3>Required Actions:</h3>
                <ul>
                    ${result.required_actions.map(a => `<li>${a}</li>`).join('')}
                </ul>
            </div>

            <div class="modal-actions">
                <button onclick="closeModal()">Cancel</button>
                <button onclick="showOverrideForm()">Override (with reason)</button>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modal);
}

function showOverrideForm() {
    const form = `
        <div class="override-form">
            <h3>Override DoD</h3>
            <p>⚠️ Overriding DoD should only be done in exceptional circumstances.</p>

            <label>Reason for override:</label>
            <textarea id="override-reason" rows="4" required></textarea>

            <button onclick="submitOverride()">Confirm Override</button>
            <button onclick="closeModal()">Cancel</button>
        </div>
    `;

    document.querySelector('.modal').innerHTML = form;
}

async function submitOverride() {
    const reason = document.getElementById('override-reason').value;

    if (!reason) {
        alert('Reason required');
        return;
    }

    const response = await fetch(`/api/stories/${storyId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            new_status: 'COMPLETED',
            override: true,
            override_reason: reason
        })
    });

    const result = await response.json();

    if (result.success) {
        closeModal();
        refreshStory(storyId);
    }
}
</script>
```

---

### DoD Checklist Modal

```html
<div class="dod-modal" id="dod-modal">
    <div class="dod-modal-content">
        <div class="dod-modal-header">
            <h2>Definition of Done - STORY-001</h2>
            <button class="close-btn" onclick="closeDoDModal()">×</button>
        </div>

        <div class="dod-modal-body">
            <!-- Implementation Category -->
            <div class="dod-category">
                <h3>Implementation (4/5 complete)</h3>

                <div class="dod-item completed">
                    <input type="checkbox" checked disabled>
                    <label>Code written and follows coding standards</label>
                    <span class="auto-badge">🤖 Auto</span>
                    <span class="timestamp">2025-11-14 10:30</span>
                </div>

                <div class="dod-item completed">
                    <input type="checkbox" checked disabled>
                    <label>Code reviewed by peer (@alice)</label>
                    <span class="auto-badge">🤖 Auto</span>
                    <span class="timestamp">2025-11-14 14:20</span>
                </div>

                <div class="dod-item incomplete">
                    <input type="checkbox" disabled>
                    <label>No code smells</label>
                    <span class="auto-badge">🤖 Auto</span>
                    <span class="blocker">⚠️ 2 code smells detected</span>
                    <button class="fix-btn" onclick="viewCodeSmells()">View</button>
                </div>

                <div class="dod-item completed">
                    <input type="checkbox" checked disabled>
                    <label>Cyclomatic complexity ≤15</label>
                    <span class="auto-badge">🤖 Auto</span>
                    <span class="value">Max: 12</span>
                </div>

                <div class="dod-item completed">
                    <input type="checkbox" checked disabled>
                    <label>No hardcoded secrets</label>
                    <span class="auto-badge">🤖 Auto</span>
                </div>
            </div>

            <!-- Testing Category -->
            <div class="dod-category">
                <h3>Testing (5/5 complete)</h3>

                <div class="dod-item completed">
                    <input type="checkbox" checked disabled>
                    <label>Unit tests written (5 tests)</label>
                    <span class="auto-badge">🤖 Auto</span>
                </div>

                <div class="dod-item completed">
                    <input type="checkbox" checked disabled>
                    <label>Unit tests pass (100%)</label>
                    <span class="auto-badge">🤖 Auto</span>
                    <span class="value">5/5 passed</span>
                </div>

                <div class="dod-item completed">
                    <input type="checkbox" checked disabled>
                    <label>Code coverage ≥80% (84% achieved)</label>
                    <span class="auto-badge">🤖 Auto</span>
                    <span class="value">84%</span>
                </div>

                <div class="dod-item completed manual">
                    <input type="checkbox" checked onclick="toggleDoDItem(this)">
                    <label>Manual testing completed</label>
                    <span class="manual-badge">👤 Manual</span>
                    <span class="completed-by">By @eddie</span>
                </div>
            </div>

            <!-- More categories... -->
        </div>

        <div class="dod-modal-footer">
            <div class="dod-summary">
                <strong>Overall:</strong> 11/13 complete (85%)
            </div>
            <button class="btn-refresh" onclick="refreshDoD()">
                🔄 Refresh
            </button>
        </div>
    </div>
</div>
```

---

## 📊 Metrics & Reporting

### DoD Compliance Dashboard

```markdown
# Definition of Done - Compliance Report

**Week 45, 2025**

## Summary

- **Overall DoD Compliance:** 92% (target: >90%)
- **Items Blocked by DoD:** 3 (2 Stories, 1 Feature)
- **DoD Overrides This Week:** 2 (both justified)
- **Average DoD Completion at Transition:** 96%

## DoD Compliance by Item Type

| Item Type | Avg DoD% at Transition | Blocked Items | Override Rate |
|-----------|------------------------|---------------|---------------|
| Epic      | 98%                    | 0             | 0%            |
| Feature   | 95%                    | 1             | 5%            |
| Story     | 94%                    | 2             | 8%            |
| Task      | 99%                    | 0             | 0%            |

## Blocked Items

### STORY-045: Refactor UserService
**Status:** IN PROGRESS → COMPLETED (blocked)
**DoD Completion:** 85%
**Blockers:**
- Testing: Code coverage 72% (target: ≥80%)
- Documentation: API documentation not updated

**Action:** Assigned to @eddie, due 2025-11-16

### STORY-046: Refactor ProjectController
**Status:** PLANNED → IN PROGRESS (blocked)
**DoD Completion:** 60%
**Blockers:**
- Architecture: Architecture review not completed
- Planning: Stories not defined

**Action:** Waiting for Software Architect Agent review

## DoD Overrides This Week

### Override #1: STORY-042
**From:** IN PROGRESS → COMPLETED
**DoD Completion:** 88% (2 items incomplete)
**Reason:** "Urgent hotfix for production issue. Missing items: integration tests and changelog update. Will be completed in follow-up story STORY-043."
**Overridden By:** @eddie
**Approved By:** Product Owner
**Status:** ✅ Follow-up story created

### Override #2: FEATURE-008
**From:** PLANNED → IN PROGRESS
**DoD Completion:** 92% (1 item incomplete)
**Reason:** "Risk mitigation plan not documented yet, but feature is low-risk and we need to start immediately to meet deadline."
**Overridden By:** @alice
**Approved By:** Tech Lead
**Status:** ✅ Risk plan documented during sprint

## Recommendations

1. **Focus on Testing:** 2 stories blocked due to insufficient test coverage. Consider pairing with Test Engineer Agent.

2. **Architecture Reviews:** 1 feature blocked waiting for architecture review. Software Architect Agent has capacity this week.

3. **Documentation:** Common blocker across 3 items. Add documentation time to estimates.

---

**Generated by:** DoD Validator Agent
**Next Review:** 2025-11-19
```

---

## 🎯 Implementation Roadmap

### Fase 1.5: DoD System (Week 2-3)

**Week 2:**
1. Create DoD templates (epic_start.yml, story_completion.yml, etc.)
2. Implement DoDValidatorAgent
3. Add DoD checklist to markdown files (frontmatter + body section)
4. Update database schema (dod_status, dod_completion columns)

**Week 3:**
5. Integrate DoD validation into API endpoints
6. Add DoD progress indicators to UI
7. Implement DoD modal for viewing/editing checklists
8. Add override functionality with reason logging

### Integration with Agents

**Software Architect Agent (Week 3):**
- Auto-check architecture review items
- Create ADRs that auto-complete DoD items
- Block transitions if critical architecture items missing

**Test Engineer Agent (Week 4):**
- Auto-check test coverage items
- Auto-check test pass rate
- Update DoD when tests written/passed

**Estimation Engine (Week 3):**
- Auto-check estimation complete items
- Validate all Features/Stories estimated before Epic starts

---

## ✅ Success Criteria

- ✅ DoD templates voor alle item types
- ✅ DoD Validator Agent werkend
- ✅ 90%+ DoD compliance rate
- ✅ Blocked transitions logged
- ✅ Override functionality met audit trail
- ✅ UI shows DoD progress in real-time
- ✅ Agents auto-complete DoD items waar mogelijk

---

**🎉 Result: Quality gates voorkomen incomplete work van naar volgende fase te gaan!**
