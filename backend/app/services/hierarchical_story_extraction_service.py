"""
Hierarchical Story Extraction Service - Week 84

Bottom-up extraction of user stories from code at multiple granularity levels:
- Function Level: Individual function behaviors
- Class Level: Class responsibilities and interactions
- Module Level: Module boundaries and integration points
- System Level: System-wide features and cross-cutting concerns

Integrates with Week 83's CodeAnalysisAggregatorService for code context.
Uses few-shot templates per technology stack for domain-specific extraction.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
import asyncio
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.deep_extraction import ExtractionTier, ItemType
from app.services.code_analysis_aggregator_service import (
    CodeAnalysisAggregatorService,
    AggregatedAnalysis,
    TechnologyProfile,
)
from app.providers.registry import get_registry, get_provider
from app.providers.base import LLMRequest

# Week 125: CiRA integration imports
from app.services.cira_service import CiRAService

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ExtractionLevel(str, Enum):
    """Hierarchical extraction levels (bottom-up)."""
    FUNCTION = "function"   # Individual functions/methods
    CLASS = "class"         # Classes and their responsibilities
    MODULE = "module"       # Modules and their boundaries
    SYSTEM = "system"       # System-wide features


class StoryConfidence(str, Enum):
    """Confidence level of extracted stories."""
    HIGH = "high"       # >= 80% confidence
    MEDIUM = "medium"   # 60-79% confidence
    LOW = "low"         # < 60% confidence


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class ExtractedStory:
    """A user story extracted from code at any level."""
    id: str = field(default_factory=lambda: str(uuid4()))
    level: ExtractionLevel = ExtractionLevel.FUNCTION
    item_type: ItemType = ItemType.STORY

    # Story content
    title: str = ""
    description: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)

    # Source context
    source_file: str = ""
    source_symbol: str = ""
    source_lines: Tuple[int, int] = (0, 0)

    # Hierarchy
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)

    # Metadata
    confidence: float = 0.0
    confidence_level: StoryConfidence = StoryConfidence.LOW
    complexity: str = "medium"  # low, medium, high, critical
    tags: List[str] = field(default_factory=list)

    # Estimation
    story_points: Optional[int] = None
    function_points: Optional[float] = None

    # Extraction info
    extracted_by: str = ""  # LLM that extracted this
    extracted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "level": self.level.value,
            "item_type": self.item_type.value,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "source_file": self.source_file,
            "source_symbol": self.source_symbol,
            "source_lines": list(self.source_lines),
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "complexity": self.complexity,
            "tags": self.tags,
            "story_points": self.story_points,
            "function_points": self.function_points,
            "extracted_by": self.extracted_by,
            "extracted_at": self.extracted_at.isoformat(),
        }


@dataclass
class LevelExtractionResult:
    """Result of extraction at a single level."""
    level: ExtractionLevel
    stories: List[ExtractedStory] = field(default_factory=list)
    epics: List[ExtractedStory] = field(default_factory=list)
    features: List[ExtractedStory] = field(default_factory=list)
    tasks: List[ExtractedStory] = field(default_factory=list)

    # Metrics
    total_items: int = 0
    avg_confidence: float = 0.0
    duration_ms: int = 0
    tokens_used: int = 0

    # Errors
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "stories": [s.to_dict() for s in self.stories],
            "epics": [e.to_dict() for e in self.epics],
            "features": [f.to_dict() for f in self.features],
            "tasks": [t.to_dict() for t in self.tasks],
            "total_items": self.total_items,
            "avg_confidence": self.avg_confidence,
            "duration_ms": self.duration_ms,
            "tokens_used": self.tokens_used,
            "errors": self.errors,
        }


@dataclass
class CausalDependencyInfo:
    """
    Week 125: Causal dependency information from CiRA analysis.

    Tracks causal relations between extracted stories/features/epics.
    """
    session_id: Optional[str] = None
    total_causal_sentences: int = 0
    total_relations: int = 0
    avg_confidence: float = 0.0

    # Graph information
    has_graph: bool = False
    node_count: int = 0
    edge_count: int = 0
    critical_path: List[str] = field(default_factory=list)
    root_nodes: List[str] = field(default_factory=list)
    leaf_nodes: List[str] = field(default_factory=list)
    suggested_sprint_order: List[str] = field(default_factory=list)
    cycles_detected: int = 0

    # Relations by source
    relations_by_story: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "total_causal_sentences": self.total_causal_sentences,
            "total_relations": self.total_relations,
            "avg_confidence": self.avg_confidence,
            "has_graph": self.has_graph,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "critical_path": self.critical_path,
            "root_nodes": self.root_nodes,
            "leaf_nodes": self.leaf_nodes,
            "suggested_sprint_order": self.suggested_sprint_order,
            "cycles_detected": self.cycles_detected,
            "relations_by_story": self.relations_by_story,
        }


@dataclass
class HierarchicalExtractionResult:
    """Complete hierarchical extraction result."""
    extraction_id: str = field(default_factory=lambda: str(uuid4()))
    project_id: int = 0
    repository_path: str = ""

    # Extraction results by level
    function_level: Optional[LevelExtractionResult] = None
    class_level: Optional[LevelExtractionResult] = None
    module_level: Optional[LevelExtractionResult] = None
    system_level: Optional[LevelExtractionResult] = None

    # Technology context
    primary_stack: Optional[str] = None
    few_shot_template: Optional[str] = None

    # Aggregated metrics
    total_epics: int = 0
    total_features: int = 0
    total_stories: int = 0
    total_tasks: int = 0
    overall_confidence: float = 0.0

    # Cost and performance
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_duration_ms: int = 0

    # Week 125: Causal dependencies
    causal_dependencies: Optional[CausalDependencyInfo] = None

    # Status
    tier: ExtractionTier = ExtractionTier.FREE
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)

    @property
    def is_successful(self) -> bool:
        """Check if extraction was successful."""
        return len(self.errors) == 0 and self.total_stories > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "extraction_id": self.extraction_id,
            "project_id": self.project_id,
            "repository_path": self.repository_path,
            "function_level": self.function_level.to_dict() if self.function_level else None,
            "class_level": self.class_level.to_dict() if self.class_level else None,
            "module_level": self.module_level.to_dict() if self.module_level else None,
            "system_level": self.system_level.to_dict() if self.system_level else None,
            "primary_stack": self.primary_stack,
            "few_shot_template": self.few_shot_template,
            "totals": {
                "epics": self.total_epics,
                "features": self.total_features,
                "stories": self.total_stories,
                "tasks": self.total_tasks,
            },
            "overall_confidence": self.overall_confidence,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "total_duration_ms": self.total_duration_ms,
            # Week 125: Include causal dependencies
            "causal_dependencies": self.causal_dependencies.to_dict() if self.causal_dependencies else None,
            "tier": self.tier.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "errors": self.errors,
            "is_successful": self.is_successful,
        }

    def to_llm_context(self) -> str:
        """Generate LLM-friendly context string."""
        lines = [
            "## Hierarchical Story Extraction Results",
            "",
            f"**Project**: {self.repository_path}",
            f"**Stack**: {self.primary_stack or 'Unknown'}",
            f"**Confidence**: {self.overall_confidence:.0%}",
            "",
            "### Summary",
            f"- **Epics**: {self.total_epics}",
            f"- **Features**: {self.total_features}",
            f"- **Stories**: {self.total_stories}",
            f"- **Tasks**: {self.total_tasks}",
            "",
        ]

        # Add level summaries
        for level_name, level_result in [
            ("Function", self.function_level),
            ("Class", self.class_level),
            ("Module", self.module_level),
            ("System", self.system_level),
        ]:
            if level_result:
                lines.append(f"### {level_name} Level ({level_result.total_items} items)")
                for story in level_result.stories[:5]:  # First 5 stories
                    lines.append(f"- {story.title}")
                if len(level_result.stories) > 5:
                    lines.append(f"  ... and {len(level_result.stories) - 5} more")
                lines.append("")

        return "\n".join(lines)


# =============================================================================
# FEW-SHOT TEMPLATES
# =============================================================================

class FewShotTemplates:
    """
    Few-shot learning templates for stack-specific story extraction.

    Each stack has domain-specific examples that help LLMs understand:
    - Common patterns in that stack
    - How to formulate stories from code
    - Typical acceptance criteria
    """

    PYTHON_TEMPLATE = """
## Python Story Extraction Examples

### Example 1: FastAPI Endpoint
**Code**:
```python
@app.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == user.email))
    if existing.scalar():
        raise HTTPException(400, "Email already registered")
    new_user = User(**user.dict())
    db.add(new_user)
    await db.commit()
    return new_user
```

**Extracted Story**:
- **Title**: User Registration with Duplicate Check
- **Description**: As a new user, I want to register with my email so that I can access the system
- **Acceptance Criteria**:
  1. POST /users creates a new user
  2. Returns 400 if email already registered
  3. Persists user to database
- **Level**: function
- **Tags**: authentication, api, user-management

### Example 2: Service Class
**Code**:
```python
class PaymentService:
    def __init__(self, stripe_client, db):
        self.stripe = stripe_client
        self.db = db

    async def process_payment(self, order_id: int, amount: Decimal):
        order = await self.get_order(order_id)
        charge = await self.stripe.create_charge(amount)
        await self.record_transaction(order, charge)
        return charge
```

**Extracted Story**:
- **Title**: Payment Processing Integration
- **Description**: As a customer, I want to pay for my order so that it can be fulfilled
- **Acceptance Criteria**:
  1. Retrieves order by ID
  2. Creates Stripe charge for amount
  3. Records transaction in database
  4. Returns charge confirmation
- **Level**: class
- **Tags**: payments, stripe, transactions
"""

    JAVASCRIPT_TEMPLATE = """
## JavaScript/TypeScript Story Extraction Examples

### Example 1: React Component
**Code**:
```typescript
export const ShoppingCart: React.FC<CartProps> = ({ items, onCheckout }) => {
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const sum = items.reduce((acc, item) => acc + item.price * item.quantity, 0);
    setTotal(sum);
  }, [items]);

  return (
    <div>
      {items.map(item => <CartItem key={item.id} item={item} />)}
      <Button onClick={() => onCheckout(total)}>Checkout ${total}</Button>
    </div>
  );
};
```

**Extracted Story**:
- **Title**: Shopping Cart with Dynamic Total
- **Description**: As a shopper, I want to see my cart items and total so that I can review before checkout
- **Acceptance Criteria**:
  1. Displays all cart items
  2. Calculates total automatically when items change
  3. Checkout button shows current total
  4. Calls onCheckout with total amount
- **Level**: function
- **Tags**: shopping, cart, checkout, react

### Example 2: Express Middleware
**Code**:
```javascript
const authMiddleware = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = await User.findById(decoded.userId);
    next();
  } catch (err) {
    return res.status(403).json({ error: 'Invalid token' });
  }
};
```

**Extracted Story**:
- **Title**: JWT Authentication Middleware
- **Description**: As a protected endpoint, I need to verify user identity before processing requests
- **Acceptance Criteria**:
  1. Extracts token from Authorization header
  2. Returns 401 if no token provided
  3. Verifies token with JWT secret
  4. Attaches user object to request
  5. Returns 403 if token invalid
- **Level**: function
- **Tags**: authentication, jwt, middleware, security
"""

    CSHARP_TEMPLATE = """
## C#/.NET Story Extraction Examples

### Example 1: Controller Action
**Code**:
```csharp
[HttpPost("orders")]
[Authorize]
public async Task<ActionResult<OrderDto>> CreateOrder([FromBody] CreateOrderRequest request)
{
    var user = await _userService.GetCurrentUser();
    var order = await _orderService.CreateAsync(user.Id, request.Items);
    await _eventBus.Publish(new OrderCreatedEvent(order.Id));
    return CreatedAtAction(nameof(GetOrder), new { id = order.Id }, order.ToDto());
}
```

**Extracted Story**:
- **Title**: Order Creation with Event Publishing
- **Description**: As an authenticated customer, I want to create an order so that my purchase is processed
- **Acceptance Criteria**:
  1. Requires authentication (Authorize attribute)
  2. Creates order for current user with requested items
  3. Publishes OrderCreatedEvent for downstream processing
  4. Returns 201 Created with order details
  5. Includes location header for order retrieval
- **Level**: function
- **Tags**: orders, api, events, authorization

### Example 2: Domain Entity
**Code**:
```csharp
public class Subscription : AggregateRoot
{
    public Guid UserId { get; private set; }
    public SubscriptionPlan Plan { get; private set; }
    public DateTime StartDate { get; private set; }
    public DateTime? EndDate { get; private set; }

    public void Upgrade(SubscriptionPlan newPlan)
    {
        if (newPlan.Tier <= Plan.Tier)
            throw new InvalidOperationException("Can only upgrade to higher tier");

        AddDomainEvent(new SubscriptionUpgradedEvent(Id, Plan, newPlan));
        Plan = newPlan;
    }

    public void Cancel()
    {
        if (EndDate.HasValue)
            throw new InvalidOperationException("Already cancelled");

        EndDate = DateTime.UtcNow;
        AddDomainEvent(new SubscriptionCancelledEvent(Id));
    }
}
```

**Extracted Story**:
- **Title**: Subscription Management Domain Logic
- **Description**: As a subscription system, I need to enforce business rules for upgrades and cancellations
- **Acceptance Criteria**:
  1. Upgrade only allowed to higher tier plans
  2. Upgrade publishes SubscriptionUpgradedEvent
  3. Cancel sets end date to current time
  4. Cancel prevents double-cancellation
  5. Cancel publishes SubscriptionCancelledEvent
- **Level**: class
- **Tags**: subscription, domain, ddd, events
"""

    GO_TEMPLATE = """
## Go Story Extraction Examples

### Example 1: HTTP Handler
**Code**:
```go
func (h *UserHandler) CreateUser(w http.ResponseWriter, r *http.Request) {
    var req CreateUserRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request body", http.StatusBadRequest)
        return
    }

    if err := h.validator.Validate(req); err != nil {
        http.Error(w, err.Error(), http.StatusUnprocessableEntity)
        return
    }

    user, err := h.userService.Create(r.Context(), req)
    if err != nil {
        h.logger.Error("Failed to create user", "error", err)
        http.Error(w, "Internal error", http.StatusInternalServerError)
        return
    }

    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(user)
}
```

**Extracted Story**:
- **Title**: User Creation Endpoint with Validation
- **Description**: As an API consumer, I want to create users with proper validation and error handling
- **Acceptance Criteria**:
  1. Parses JSON request body
  2. Returns 400 for invalid JSON
  3. Validates request fields
  4. Returns 422 for validation errors
  5. Creates user via service layer
  6. Logs errors for debugging
  7. Returns 201 with created user
- **Level**: function
- **Tags**: api, users, validation, http

### Example 2: Repository Pattern
**Code**:
```go
type OrderRepository struct {
    db *sql.DB
}

func (r *OrderRepository) GetByID(ctx context.Context, id uuid.UUID) (*Order, error) {
    query := `SELECT id, user_id, status, total, created_at FROM orders WHERE id = $1`

    var order Order
    err := r.db.QueryRowContext(ctx, query, id).Scan(
        &order.ID, &order.UserID, &order.Status, &order.Total, &order.CreatedAt,
    )
    if err == sql.ErrNoRows {
        return nil, ErrOrderNotFound
    }
    if err != nil {
        return nil, fmt.Errorf("failed to get order: %w", err)
    }

    return &order, nil
}
```

**Extracted Story**:
- **Title**: Order Retrieval by ID
- **Description**: As a system component, I need to fetch orders by their unique identifier
- **Acceptance Criteria**:
  1. Queries database with parameterized query (SQL injection safe)
  2. Returns ErrOrderNotFound for missing orders
  3. Wraps database errors with context
  4. Uses context for cancellation support
- **Level**: function
- **Tags**: repository, database, orders, postgresql
"""

    JAVA_TEMPLATE = """
## Java Story Extraction Examples

### Example 1: Spring Service
**Code**:
```java
@Service
@Transactional
public class InventoryService {
    private final ProductRepository productRepo;
    private final WarehouseClient warehouseClient;
    private final EventPublisher eventPublisher;

    public void reserveStock(Long productId, int quantity) {
        Product product = productRepo.findById(productId)
            .orElseThrow(() -> new ProductNotFoundException(productId));

        if (product.getStock() < quantity) {
            throw new InsufficientStockException(productId, product.getStock(), quantity);
        }

        product.setStock(product.getStock() - quantity);
        productRepo.save(product);

        warehouseClient.notifyReservation(productId, quantity);
        eventPublisher.publish(new StockReservedEvent(productId, quantity));
    }
}
```

**Extracted Story**:
- **Title**: Stock Reservation with External Notification
- **Description**: As an order system, I need to reserve inventory when orders are placed
- **Acceptance Criteria**:
  1. Validates product exists
  2. Checks sufficient stock available
  3. Reduces stock by requested quantity
  4. Persists updated product
  5. Notifies warehouse system
  6. Publishes StockReservedEvent
  7. Runs within transaction (rollback on failure)
- **Level**: function
- **Tags**: inventory, transactions, events, integration

### Example 2: JPA Entity
**Code**:
```java
@Entity
@Table(name = "customers")
public class Customer {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String email;

    @Embedded
    private Address shippingAddress;

    @OneToMany(mappedBy = "customer", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Order> orders = new ArrayList<>();

    public void addOrder(Order order) {
        orders.add(order);
        order.setCustomer(this);
    }

    public BigDecimal getTotalSpent() {
        return orders.stream()
            .filter(o -> o.getStatus() == OrderStatus.COMPLETED)
            .map(Order::getTotal)
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}
```

**Extracted Story**:
- **Title**: Customer Domain Entity with Order Aggregation
- **Description**: As a CRM system, I need to track customer orders and spending history
- **Acceptance Criteria**:
  1. Email is unique and required
  2. Supports embedded shipping address
  3. Manages order collection with bidirectional mapping
  4. Calculates total spending from completed orders
  5. Cascades operations to orders
- **Level**: class
- **Tags**: customer, jpa, domain, orders
"""

    @classmethod
    def get_template_for_stack(cls, stack: str) -> str:
        """Get the few-shot template for a technology stack."""
        templates = {
            "python": cls.PYTHON_TEMPLATE,
            "javascript": cls.JAVASCRIPT_TEMPLATE,
            "typescript": cls.JAVASCRIPT_TEMPLATE,
            "csharp": cls.CSHARP_TEMPLATE,
            "go": cls.GO_TEMPLATE,
            "java": cls.JAVA_TEMPLATE,
        }

        # Normalize stack name
        normalized = stack.lower().strip()

        return templates.get(normalized, cls.PYTHON_TEMPLATE)  # Default to Python

    @classmethod
    def get_all_stacks(cls) -> List[str]:
        """Get list of all supported stacks."""
        return ["python", "javascript", "typescript", "csharp", "go", "java"]


# =============================================================================
# PROMPT BUILDERS
# =============================================================================

class HierarchicalPromptBuilder:
    """Builds prompts for hierarchical story extraction."""

    @staticmethod
    def build_function_level_prompt(
        code: str,
        file_path: str,
        few_shot_template: str,
        context: Optional[str] = None,
    ) -> str:
        """Build prompt for function-level extraction."""
        prompt = f"""You are a senior software analyst extracting user stories from code.

## Task
Analyze the following function/method and extract user stories that describe its behavior from a user's perspective.

## Few-Shot Examples
{few_shot_template}

## Guidelines
1. Focus on WHAT the function does, not HOW it does it
2. Use the format: "As a [role], I want [goal] so that [benefit]"
3. List specific, testable acceptance criteria
4. Estimate complexity: low (simple CRUD), medium (business logic), high (complex flow), critical (core algorithm)
5. Assign confidence 0.0-1.0 based on how clear the behavior is

## Code to Analyze
**File**: {file_path}

```
{code}
```

{f"## Additional Context{chr(10)}{context}" if context else ""}

## Output Format (JSON)
{{
  "stories": [
    {{
      "title": "Descriptive title",
      "description": "As a..., I want..., so that...",
      "acceptance_criteria": ["Criterion 1", "Criterion 2"],
      "complexity": "low|medium|high|critical",
      "confidence": 0.85,
      "tags": ["tag1", "tag2"]
    }}
  ]
}}

Extract the user stories:"""
        return prompt

    @staticmethod
    def build_class_level_prompt(
        class_code: str,
        class_name: str,
        file_path: str,
        few_shot_template: str,
        method_stories: List[ExtractedStory],
    ) -> str:
        """Build prompt for class-level extraction."""
        method_summary = "\n".join([
            f"- {s.title}: {s.description[:100]}..."
            for s in method_stories[:10]
        ])

        prompt = f"""You are a senior software analyst extracting features from a class.

## Task
Analyze this class and extract features that group related user stories.
Consider the class's overall responsibility and how its methods work together.

## Method Stories Already Extracted
{method_summary}

## Few-Shot Examples
{few_shot_template}

## Guidelines
1. Identify the class's main responsibility (Single Responsibility Principle)
2. Group related method stories into features
3. Identify cross-cutting concerns (logging, caching, error handling)
4. Features should represent cohesive functionality from a user perspective

## Class to Analyze
**File**: {file_path}
**Class**: {class_name}

```
{class_code}
```

## Output Format (JSON)
{{
  "features": [
    {{
      "title": "Feature title",
      "description": "Feature description",
      "child_story_ids": ["story-id-1", "story-id-2"],
      "acceptance_criteria": ["Criterion 1", "Criterion 2"],
      "complexity": "low|medium|high|critical",
      "confidence": 0.85,
      "tags": ["tag1", "tag2"]
    }}
  ]
}}

Extract the features:"""
        return prompt

    @staticmethod
    def build_module_level_prompt(
        module_files: List[str],
        class_features: List[ExtractedStory],
        module_name: str,
        dependencies: List[str],
    ) -> str:
        """Build prompt for module-level extraction."""
        feature_summary = "\n".join([
            f"- {f.title}: {f.description[:80]}..."
            for f in class_features[:15]
        ])

        files_list = "\n".join([f"- {f}" for f in module_files[:20]])
        deps_list = "\n".join([f"- {d}" for d in dependencies[:10]])

        prompt = f"""You are a senior software architect extracting epics from a module.

## Task
Analyze this module and extract epics that represent major functional areas.
Consider the module's boundaries, integration points, and overall purpose.

## Features Already Extracted from Classes
{feature_summary}

## Module Structure
**Module**: {module_name}

**Files**:
{files_list}

**Dependencies**:
{deps_list}

## Guidelines
1. Epics represent large bodies of work (multiple features)
2. Consider module boundaries as natural epic boundaries
3. Identify integration points as potential epic scope
4. Think about release planning - what ships together?

## Output Format (JSON)
{{
  "epics": [
    {{
      "title": "Epic title",
      "description": "Epic description from business perspective",
      "child_feature_ids": ["feature-id-1", "feature-id-2"],
      "integration_points": ["external-system-1"],
      "complexity": "high|critical",
      "confidence": 0.80,
      "tags": ["tag1", "tag2"]
    }}
  ]
}}

Extract the epics:"""
        return prompt

    @staticmethod
    def build_system_level_prompt(
        module_epics: List[ExtractedStory],
        technology_profile: TechnologyProfile,
        system_name: str,
    ) -> str:
        """Build prompt for system-level extraction."""
        epic_summary = "\n".join([
            f"- {e.title}: {e.description[:100]}..."
            for e in module_epics
        ])

        tech_summary = f"""
- Primary Stack: {technology_profile.primary_stack or 'Unknown'}
- Secondary: {', '.join(technology_profile.secondary_stacks or [])}
- Database: {technology_profile.database_type or 'Unknown'}
- Files: {technology_profile.total_files}
- Lines: {technology_profile.total_loc:,}
"""

        prompt = f"""You are a senior technical product manager synthesizing system-level features.

## Task
Analyze all extracted epics and identify system-wide themes and cross-cutting concerns.
Create a product hierarchy that represents the full system from a business perspective.

## Epics Extracted from Modules
{epic_summary}

## Technology Profile
{tech_summary}

## Guidelines
1. Identify cross-module themes (security, observability, data management)
2. Group epics into product areas
3. Consider deployment and operational concerns
4. Think about user journeys that span multiple epics
5. Identify potential technical debt and modernization opportunities

## Output Format (JSON)
{{
  "product_areas": [
    {{
      "title": "Product Area Name",
      "description": "Business description of this product area",
      "epic_ids": ["epic-id-1", "epic-id-2"],
      "cross_cutting_concerns": ["security", "performance"],
      "confidence": 0.75,
      "tags": ["tag1", "tag2"]
    }}
  ],
  "cross_cutting_features": [
    {{
      "title": "Cross-cutting feature",
      "description": "Feature that spans multiple areas",
      "affected_epics": ["epic-id-1", "epic-id-3"],
      "priority": "high|medium|low",
      "confidence": 0.80
    }}
  ]
}}

Extract the system-level analysis:"""
        return prompt


# =============================================================================
# MAIN SERVICE
# =============================================================================

class HierarchicalStoryExtractionService:
    """
    Service for hierarchical extraction of user stories from code.

    Extraction Flow (Bottom-Up):
    1. Function Level: Extract stories from individual functions/methods
    2. Class Level: Group stories into features based on class responsibility
    3. Module Level: Group features into epics based on module boundaries
    4. System Level: Identify cross-cutting concerns and product areas

    Usage:
        service = HierarchicalStoryExtractionService(db)

        result = await service.extract_hierarchical(
            project_id=1,
            repository_path="/path/to/repo",
            tier=ExtractionTier.STANDARD,
        )

        print(f"Extracted {result.total_stories} stories")
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.aggregator = CodeAnalysisAggregatorService(db)
        self.prompt_builder = HierarchicalPromptBuilder()
        # Week 125: CiRA integration for causal dependency analysis
        self.cira_service = CiRAService(db)

    async def extract_hierarchical(
        self,
        project_id: int,
        repository_path: str,
        tier: ExtractionTier = ExtractionTier.FREE,
        levels: Optional[List[ExtractionLevel]] = None,
        max_files: int = 100,
        aggregation_id: Optional[UUID] = None,
        include_cira_analysis: bool = True,  # Week 125: CiRA causal analysis
    ) -> HierarchicalExtractionResult:
        """
        Perform hierarchical story extraction.

        Args:
            project_id: Database project ID
            repository_path: Path to repository
            tier: Extraction tier for LLM selection
            levels: Which levels to extract (default: all)
            max_files: Maximum files to analyze
            aggregation_id: Optional existing analysis to use
            include_cira_analysis: Whether to run CiRA causality analysis (Week 125)

        Returns:
            HierarchicalExtractionResult with extracted stories at all levels
        """
        import time
        start_time = time.time()

        result = HierarchicalExtractionResult(
            project_id=project_id,
            repository_path=repository_path,
            tier=tier,
        )

        levels = levels or [
            ExtractionLevel.FUNCTION,
            ExtractionLevel.CLASS,
            ExtractionLevel.MODULE,
            ExtractionLevel.SYSTEM,
        ]

        try:
            # Step 1: Get code analysis (Week 83 integration)
            print(f"[DEBUG] Starting extraction for project {project_id} at {repository_path}")
            analysis = await self._get_or_create_analysis(
                project_id, repository_path, aggregation_id
            )
            print(f"[DEBUG] Analysis complete: is_successful={analysis.is_successful}, errors={analysis.errors}")

            if not analysis.is_successful:
                result.errors.append(f"Code analysis failed: {analysis.errors}")
                print(f"[DEBUG] Analysis failed with errors: {analysis.errors}")
                return result

            result.primary_stack = analysis.technology.primary_stack
            print(f"[DEBUG] Primary stack detected: {result.primary_stack}")

            # Get few-shot template for the stack
            template = FewShotTemplates.get_template_for_stack(
                result.primary_stack or "python"
            )
            result.few_shot_template = result.primary_stack

            # Step 2: Function-level extraction
            if ExtractionLevel.FUNCTION in levels:
                result.function_level = await self._extract_function_level(
                    repository_path, template, tier, max_files
                )
                result.total_stories += len(result.function_level.stories)
                result.total_tasks += len(result.function_level.tasks)
                result.total_tokens += result.function_level.tokens_used

            # Step 3: Class-level extraction (depends on function level)
            if ExtractionLevel.CLASS in levels and result.function_level:
                result.class_level = await self._extract_class_level(
                    repository_path, template, tier,
                    result.function_level.stories
                )
                result.total_features += len(result.class_level.features)
                result.total_tokens += result.class_level.tokens_used

            # Step 4: Module-level extraction (depends on class level)
            if ExtractionLevel.MODULE in levels and result.class_level:
                result.module_level = await self._extract_module_level(
                    repository_path, tier,
                    result.class_level.features,
                    analysis
                )
                result.total_epics += len(result.module_level.epics)
                result.total_tokens += result.module_level.tokens_used

            # Step 5: System-level extraction (depends on module level)
            if ExtractionLevel.SYSTEM in levels and result.module_level:
                result.system_level = await self._extract_system_level(
                    tier,
                    result.module_level.epics,
                    analysis.technology
                )
                result.total_tokens += result.system_level.tokens_used

            # Calculate overall confidence
            confidences = []
            for level in [result.function_level, result.class_level,
                         result.module_level, result.system_level]:
                if level and level.avg_confidence > 0:
                    confidences.append(level.avg_confidence)

            if confidences:
                result.overall_confidence = sum(confidences) / len(confidences)

            # Calculate cost based on tier
            result.total_cost_usd = self._calculate_cost(result.total_tokens, tier)

            # Week 125: Run CiRA causal dependency analysis
            if include_cira_analysis and result.total_stories > 0:
                try:
                    causal_info = await self._analyze_causal_dependencies(
                        project_id=project_id,
                        extraction_id=result.extraction_id,
                        stories=self._collect_all_stories(result),
                    )
                    result.causal_dependencies = causal_info
                    logger.info(
                        f"CiRA analysis complete: {causal_info.total_relations} relations, "
                        f"{causal_info.node_count} nodes"
                    )
                except Exception as cira_error:
                    logger.warning(f"CiRA analysis failed (non-fatal): {cira_error}")
                    result.errors.append(f"CiRA analysis warning: {cira_error}")

        except Exception as e:
            logger.exception("Hierarchical extraction failed")
            result.errors.append(str(e))

        result.completed_at = datetime.now(timezone.utc)
        result.total_duration_ms = int((time.time() - start_time) * 1000)

        return result

    async def _get_or_create_analysis(
        self,
        project_id: int,
        repository_path: str,
        aggregation_id: Optional[UUID],
    ) -> AggregatedAnalysis:
        """Get existing analysis or create new one."""
        if aggregation_id:
            # TODO: Load from database
            pass

        # Create new analysis using Week 83 aggregator
        return await self.aggregator.analyze(
            project_id=project_id,
            repository_path=repository_path,
            include_codewiki=False,  # Skip for speed
        )

    async def _extract_function_level(
        self,
        repository_path: str,
        few_shot_template: str,
        tier: ExtractionTier,
        max_files: int,
    ) -> LevelExtractionResult:
        """Extract stories at function level."""
        import time
        start_time = time.time()

        result = LevelExtractionResult(level=ExtractionLevel.FUNCTION)

        # Find Python/JS/TS files
        path = Path(repository_path)
        if not path.exists():
            result.errors.append(f"Path not found: {repository_path}")
            return result

        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.cs', '.go', '.java', '.vb', '.asp', '.aspx', '.ascx'}
        files = []
        for ext in extensions:
            files.extend(path.rglob(f"*{ext}"))

        # Filter out test files and limit
        files = [
            f for f in files
            if 'test' not in f.name.lower()
            and 'node_modules' not in str(f)
            and '__pycache__' not in str(f)
        ][:max_files]
        print(f"[DEBUG] Found {len(files)} source files to analyze (max_files={max_files})")

        # Get LLM provider for tier
        provider = await self._get_provider_for_tier(tier, "function")
        print(f"[DEBUG] Using LLM provider: {provider}")

        total_confidence = 0.0

        print(f"[DEBUG] Processing {min(10, len(files))} files...")
        for i, file_path in enumerate(files[:10]):  # Limit for demo
            try:
                code = file_path.read_text(errors='ignore')
                if len(code) < 50 or len(code) > 50000:
                    print(f"[DEBUG] Skipping {file_path.name}: code length {len(code)} out of range")
                    continue

                print(f"[DEBUG] Processing file {i+1}: {file_path.name} ({len(code)} chars)")
                prompt = self.prompt_builder.build_function_level_prompt(
                    code=code,
                    file_path=str(file_path.relative_to(path)),
                    few_shot_template=few_shot_template,
                )

                # Call LLM
                print(f"[DEBUG] Calling LLM for {file_path.name}...")
                response = await self._call_llm(provider, prompt)
                print(f"[DEBUG] LLM response: {len(response.get('content', ''))} chars, {response.get('tokens', 0)} tokens")
                result.tokens_used += response.get("tokens", 0)

                # Parse stories from response
                stories = self._parse_stories_from_response(
                    response.get("content", ""),
                    str(file_path.relative_to(path)),
                    ExtractionLevel.FUNCTION,
                )
                print(f"[DEBUG] Parsed {len(stories)} stories from {file_path.name}")

                for story in stories:
                    story.extracted_by = provider
                    result.stories.append(story)
                    total_confidence += story.confidence

            except Exception as e:
                logger.warning(f"Failed to extract from {file_path}: {e}")
                result.errors.append(str(e))

        result.total_items = len(result.stories)
        if result.stories:
            result.avg_confidence = total_confidence / len(result.stories)

        result.duration_ms = int((time.time() - start_time) * 1000)

        return result

    async def _extract_class_level(
        self,
        repository_path: str,
        few_shot_template: str,
        tier: ExtractionTier,
        function_stories: List[ExtractedStory],
    ) -> LevelExtractionResult:
        """Extract features at class level."""
        import time
        start_time = time.time()

        result = LevelExtractionResult(level=ExtractionLevel.CLASS)

        # Group stories by source file
        stories_by_file: Dict[str, List[ExtractedStory]] = {}
        for story in function_stories:
            file_key = story.source_file
            if file_key not in stories_by_file:
                stories_by_file[file_key] = []
            stories_by_file[file_key].append(story)

        provider = await self._get_provider_for_tier(tier, "class")
        total_confidence = 0.0

        for file_path, file_stories in list(stories_by_file.items())[:10]:
            try:
                full_path = Path(repository_path) / file_path
                if not full_path.exists():
                    continue

                code = full_path.read_text(errors='ignore')

                prompt = self.prompt_builder.build_class_level_prompt(
                    class_code=code,
                    class_name=file_path.rsplit('/', 1)[-1].rsplit('.', 1)[0],
                    file_path=file_path,
                    few_shot_template=few_shot_template,
                    method_stories=file_stories,
                )

                response = await self._call_llm(provider, prompt)
                result.tokens_used += response.get("tokens", 0)

                features = self._parse_features_from_response(
                    response.get("content", ""),
                    file_path,
                    file_stories,
                )

                for feature in features:
                    feature.extracted_by = provider
                    result.features.append(feature)
                    total_confidence += feature.confidence

            except Exception as e:
                logger.warning(f"Failed class extraction for {file_path}: {e}")
                result.errors.append(str(e))

        result.total_items = len(result.features)
        if result.features:
            result.avg_confidence = total_confidence / len(result.features)

        result.duration_ms = int((time.time() - start_time) * 1000)

        return result

    async def _extract_module_level(
        self,
        repository_path: str,
        tier: ExtractionTier,
        class_features: List[ExtractedStory],
        analysis: AggregatedAnalysis,
    ) -> LevelExtractionResult:
        """Extract epics at module level."""
        import time
        start_time = time.time()

        result = LevelExtractionResult(level=ExtractionLevel.MODULE)

        # Group features by directory (module)
        features_by_module: Dict[str, List[ExtractedStory]] = {}
        for feature in class_features:
            parts = feature.source_file.rsplit('/', 1)
            module = parts[0] if len(parts) > 1 else "root"
            if module not in features_by_module:
                features_by_module[module] = []
            features_by_module[module].append(feature)

        provider = await self._get_provider_for_tier(tier, "module")
        total_confidence = 0.0

        for module_name, module_features in features_by_module.items():
            try:
                module_path = Path(repository_path) / module_name
                module_files = [str(f.relative_to(module_path.parent))
                               for f in module_path.rglob("*.*")
                               if f.is_file()][:20]

                # Get dependencies from analysis
                deps = []
                if analysis.dependencies:
                    deps = analysis.dependencies.entry_points[:5]

                prompt = self.prompt_builder.build_module_level_prompt(
                    module_files=module_files,
                    class_features=module_features,
                    module_name=module_name,
                    dependencies=deps,
                )

                response = await self._call_llm(provider, prompt)
                result.tokens_used += response.get("tokens", 0)

                epics = self._parse_epics_from_response(
                    response.get("content", ""),
                    module_name,
                    module_features,
                )

                for epic in epics:
                    epic.extracted_by = provider
                    result.epics.append(epic)
                    total_confidence += epic.confidence

            except Exception as e:
                logger.warning(f"Failed module extraction for {module_name}: {e}")
                result.errors.append(str(e))

        result.total_items = len(result.epics)
        if result.epics:
            result.avg_confidence = total_confidence / len(result.epics)

        result.duration_ms = int((time.time() - start_time) * 1000)

        return result

    async def _extract_system_level(
        self,
        tier: ExtractionTier,
        module_epics: List[ExtractedStory],
        technology: TechnologyProfile,
    ) -> LevelExtractionResult:
        """Extract system-level features."""
        import time
        start_time = time.time()

        result = LevelExtractionResult(level=ExtractionLevel.SYSTEM)

        if not module_epics:
            return result

        provider = await self._get_provider_for_tier(tier, "system")

        try:
            prompt = self.prompt_builder.build_system_level_prompt(
                module_epics=module_epics,
                technology_profile=technology,
                system_name="System",
            )

            response = await self._call_llm(provider, prompt)
            result.tokens_used = response.get("tokens", 0)

            # Parse system-level items
            content = response.get("content", "")

            # Create system-level stories for product areas
            try:
                parsed = json.loads(self._extract_json(content))

                for area in parsed.get("product_areas", []):
                    story = ExtractedStory(
                        level=ExtractionLevel.SYSTEM,
                        item_type=ItemType.EPIC,
                        title=area.get("title", "Unknown Product Area"),
                        description=area.get("description", ""),
                        confidence=area.get("confidence", 0.7),
                        tags=area.get("tags", []),
                    )
                    story.confidence_level = self._get_confidence_level(story.confidence)
                    result.epics.append(story)

                for feature in parsed.get("cross_cutting_features", []):
                    story = ExtractedStory(
                        level=ExtractionLevel.SYSTEM,
                        item_type=ItemType.FEATURE,
                        title=feature.get("title", "Unknown Feature"),
                        description=feature.get("description", ""),
                        confidence=feature.get("confidence", 0.7),
                    )
                    story.confidence_level = self._get_confidence_level(story.confidence)
                    result.features.append(story)

            except (json.JSONDecodeError, TypeError):
                result.errors.append("Failed to parse system-level response")

        except Exception as e:
            logger.warning(f"Failed system extraction: {e}")
            result.errors.append(str(e))

        result.total_items = len(result.epics) + len(result.features)

        if result.epics:
            result.avg_confidence = sum(e.confidence for e in result.epics) / len(result.epics)

        result.duration_ms = int((time.time() - start_time) * 1000)

        return result

    async def _get_provider_for_tier(
        self,
        tier: ExtractionTier,
        level: str,
    ) -> str:
        """Get appropriate LLM provider for tier and level."""
        # Tier → Provider mapping
        tier_providers = {
            ExtractionTier.FREE: "ollama",
            ExtractionTier.BASIC: "groq",
            ExtractionTier.STANDARD: "gemini",
            ExtractionTier.PROFESSIONAL: "gemini",
            ExtractionTier.PREMIUM: "anthropic",
        }

        return tier_providers.get(tier, "ollama")

    async def _call_llm(
        self,
        provider_name: str,
        prompt: str,
    ) -> Dict[str, Any]:
        """Call LLM provider with prompt."""
        try:
            provider = get_provider(provider_name)
            print(f"[DEBUG] _call_llm: got provider {provider} for {provider_name}")

            if provider:
                # Create LLMRequest and call generate()
                request = LLMRequest(
                    prompt=prompt,
                    system="You are an expert software analyst. Extract user stories from code. Always respond with valid JSON.",
                    max_tokens=4096,
                    temperature=0.3,
                )
                print(f"[DEBUG] _call_llm: calling generate() with prompt length {len(prompt)}")
                response = await provider.generate(request)
                print(f"[DEBUG] _call_llm: response success={response.success}, error={response.error}, content_len={len(response.content)}")

                return {
                    "content": response.content if response.success else "",
                    "tokens": response.token_input + response.token_output,
                }

            # Fallback: Return mock response for testing
            print("[DEBUG] _call_llm: No provider, using fallback")
            return {
                "content": '{"stories": []}',
                "tokens": 100,
            }

        except Exception as e:
            print(f"[DEBUG] _call_llm: Exception: {e}")
            logger.warning(f"LLM call failed: {e}")
            return {"content": '{"stories": []}', "tokens": 0}

    def _parse_stories_from_response(
        self,
        content: str,
        source_file: str,
        level: ExtractionLevel,
    ) -> List[ExtractedStory]:
        """Parse stories from LLM response."""
        stories = []

        try:
            json_str = self._extract_json(content)
            parsed = json.loads(json_str)

            for item in parsed.get("stories", []):
                story = ExtractedStory(
                    level=level,
                    item_type=ItemType.STORY,
                    title=item.get("title", "Untitled Story"),
                    description=item.get("description", ""),
                    acceptance_criteria=item.get("acceptance_criteria", []),
                    source_file=source_file,
                    confidence=item.get("confidence", 0.5),
                    complexity=item.get("complexity", "medium"),
                    tags=item.get("tags", []),
                )
                story.confidence_level = self._get_confidence_level(story.confidence)
                stories.append(story)

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.debug(f"Failed to parse stories: {e}")

        return stories

    def _parse_features_from_response(
        self,
        content: str,
        source_file: str,
        child_stories: List[ExtractedStory],
    ) -> List[ExtractedStory]:
        """Parse features from LLM response."""
        features = []

        try:
            json_str = self._extract_json(content)
            parsed = json.loads(json_str)

            for item in parsed.get("features", []):
                feature = ExtractedStory(
                    level=ExtractionLevel.CLASS,
                    item_type=ItemType.FEATURE,
                    title=item.get("title", "Untitled Feature"),
                    description=item.get("description", ""),
                    acceptance_criteria=item.get("acceptance_criteria", []),
                    source_file=source_file,
                    confidence=item.get("confidence", 0.5),
                    complexity=item.get("complexity", "medium"),
                    tags=item.get("tags", []),
                    children_ids=[s.id for s in child_stories],
                )
                feature.confidence_level = self._get_confidence_level(feature.confidence)
                features.append(feature)

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.debug(f"Failed to parse features: {e}")

        return features

    def _parse_epics_from_response(
        self,
        content: str,
        module_name: str,
        child_features: List[ExtractedStory],
    ) -> List[ExtractedStory]:
        """Parse epics from LLM response."""
        epics = []

        try:
            json_str = self._extract_json(content)
            parsed = json.loads(json_str)

            for item in parsed.get("epics", []):
                epic = ExtractedStory(
                    level=ExtractionLevel.MODULE,
                    item_type=ItemType.EPIC,
                    title=item.get("title", "Untitled Epic"),
                    description=item.get("description", ""),
                    source_file=module_name,
                    confidence=item.get("confidence", 0.5),
                    complexity=item.get("complexity", "high"),
                    tags=item.get("tags", []),
                    children_ids=[f.id for f in child_features],
                )
                epic.confidence_level = self._get_confidence_level(epic.confidence)
                epics.append(epic)

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.debug(f"Failed to parse epics: {e}")

        return epics

    def _extract_json(self, content: str) -> str:
        """Extract JSON from content (handles markdown code blocks)."""
        content = content.strip()

        # Try to find JSON in code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        # Try to find JSON object directly
        if "{" in content:
            start = content.find("{")
            # Find matching closing brace
            depth = 0
            for i, c in enumerate(content[start:], start):
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        return content[start:i+1]

        return content

    def _get_confidence_level(self, confidence: float) -> StoryConfidence:
        """Convert confidence score to level."""
        if confidence >= 0.8:
            return StoryConfidence.HIGH
        elif confidence >= 0.6:
            return StoryConfidence.MEDIUM
        return StoryConfidence.LOW

    def _calculate_cost(self, tokens: int, tier: ExtractionTier) -> float:
        """Calculate extraction cost based on tier."""
        # Cost per 1M tokens (approximate)
        tier_costs = {
            ExtractionTier.FREE: 0.0,
            ExtractionTier.BASIC: 0.10,
            ExtractionTier.STANDARD: 0.50,
            ExtractionTier.PROFESSIONAL: 2.00,
            ExtractionTier.PREMIUM: 5.00,
        }

        cost_per_m = tier_costs.get(tier, 0.0)
        return (tokens / 1_000_000) * cost_per_m

    # =========================================================================
    # WEEK 125: CiRA INTEGRATION METHODS
    # =========================================================================

    def _collect_all_stories(
        self,
        result: HierarchicalExtractionResult,
    ) -> List[ExtractedStory]:
        """Collect all stories from all extraction levels."""
        all_stories = []

        if result.function_level:
            all_stories.extend(result.function_level.stories)
            all_stories.extend(result.function_level.tasks)

        if result.class_level:
            all_stories.extend(result.class_level.stories)
            all_stories.extend(result.class_level.features)

        if result.module_level:
            all_stories.extend(result.module_level.stories)
            all_stories.extend(result.module_level.epics)

        if result.system_level:
            all_stories.extend(result.system_level.stories)
            all_stories.extend(result.system_level.epics)
            all_stories.extend(result.system_level.features)

        return all_stories

    async def _analyze_causal_dependencies(
        self,
        project_id: int,
        extraction_id: str,
        stories: List[ExtractedStory],
    ) -> CausalDependencyInfo:
        """
        Analyze causal dependencies between extracted stories using CiRA.

        Week 125 Integration:
        1. Extract sentences from story descriptions and acceptance criteria
        2. Run CiRA classification on sentences
        3. Build dependency graph from causal relations
        4. Return suggested sprint ordering

        Args:
            project_id: The project ID
            extraction_id: The extraction session ID
            stories: List of all extracted stories

        Returns:
            CausalDependencyInfo with graph and ordering information
        """
        from uuid import UUID as UUIDType

        causal_info = CausalDependencyInfo()

        if not stories:
            return causal_info

        try:
            # Step 1: Create CiRA session
            session = await self.cira_service.create_session(
                project_id=project_id,
                extraction_id=UUIDType(extraction_id) if extraction_id else None,
                name=f"Hierarchical Extraction CiRA Analysis",
                description="Causality analysis for extracted user stories",
                source_type="stories",
                confidence_threshold=0.6,
            )
            causal_info.session_id = str(session.id)

            # Step 2: Collect sentences from stories
            sentences = []
            source_ids = []

            for story in stories:
                # Add story description
                if story.description:
                    sentences.append(story.description)
                    source_ids.append(story.id)

                # Add acceptance criteria (often contain causal statements)
                for criterion in story.acceptance_criteria:
                    if criterion:
                        sentences.append(criterion)
                        source_ids.append(story.id)

            if not sentences:
                return causal_info

            # Step 3: Run CiRA analysis
            analysis_result = await self.cira_service.analyze_sentences(
                session_id=session.id,
                sentences=sentences,
                source_ids=source_ids,
                source_type="story",
            )

            causal_info.total_causal_sentences = analysis_result.get("causal_count", 0)
            causal_info.total_relations = analysis_result.get("relation_count", 0)
            causal_info.avg_confidence = analysis_result.get("avg_confidence", 0.0)

            # Step 4: Build dependency graph if we have relations
            if causal_info.total_relations > 0:
                try:
                    graph = await self.cira_service.build_dependency_graph(session.id)

                    causal_info.has_graph = True
                    causal_info.node_count = graph.node_count or 0
                    causal_info.edge_count = graph.edge_count or 0
                    causal_info.critical_path = graph.critical_path or []
                    causal_info.root_nodes = graph.root_nodes or []
                    causal_info.leaf_nodes = graph.leaf_nodes or []
                    causal_info.suggested_sprint_order = graph.suggested_sprint_order or []
                    causal_info.cycles_detected = len(graph.cycles or [])

                except Exception as graph_error:
                    logger.warning(f"Graph building failed: {graph_error}")

            # Step 5: Build relations_by_story mapping
            if analysis_result.get("relations"):
                for rel in analysis_result.get("relations", []):
                    source_id = rel.get("source_id", "unknown")
                    if source_id not in causal_info.relations_by_story:
                        causal_info.relations_by_story[source_id] = []
                    causal_info.relations_by_story[source_id].append({
                        "cause": rel.get("cause", ""),
                        "effect": rel.get("effect", ""),
                        "confidence": str(rel.get("confidence", 0.0)),
                    })

        except Exception as e:
            logger.error(f"CiRA causal analysis failed: {e}")
            raise

        return causal_info


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_hierarchical_extraction_service(db: AsyncSession) -> HierarchicalStoryExtractionService:
    """Factory function to create HierarchicalStoryExtractionService."""
    return HierarchicalStoryExtractionService(db)
