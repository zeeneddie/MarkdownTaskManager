# Code Generation Order - Implementation Sequence
# MarQed.ai Platform - Week 101

## Standard Feature Implementation Order

When implementing a new feature, follow this order to ensure proper layering
and testability:

```
┌─────────────────────────────────────────────────────────────────┐
│                     IMPLEMENTATION ORDER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DOMAIN LAYER                                                 │
│     └── Entities, Value Objects, Domain Events                  │
│                                                                  │
│  2. SPECIFICATIONS (if applicable)                               │
│     └── Business rules as specification patterns                 │
│                                                                  │
│  3. REPOSITORY / DATA LAYER                                      │
│     └── Database operations, Migrations                          │
│                                                                  │
│  4. SERVICE LAYER                                                │
│     └── Business logic, Orchestration, Use cases                 │
│                                                                  │
│  5. API LAYER                                                    │
│     └── Controllers, Routes, Request/Response DTOs               │
│                                                                  │
│  6. UI LAYER                                                     │
│     └── Components, Pages, State management                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer Descriptions

### 1. Domain Layer

**Purpose:** Define the core business entities and their behavior.

**Components:**
- **Entities**: Objects with identity (e.g., User, Order)
- **Value Objects**: Immutable objects defined by attributes (e.g., Email, Money)
- **Domain Events**: Record of something that happened (e.g., OrderPlaced)
- **Aggregate Roots**: Entry points to entity clusters

**Example:**
```python
# backend/app/models/user.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Email:
    """Value object for email addresses."""
    value: str

    def __post_init__(self):
        if "@" not in self.value:
            raise ValueError("Invalid email format")

class User:
    """User entity (aggregate root)."""
    def __init__(
        self,
        id: int,
        email: Email,
        name: str,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.email = email
        self.name = name
        self.created_at = created_at or datetime.utcnow()

    def change_email(self, new_email: Email) -> None:
        """Domain method with business logic."""
        self.email = new_email
        # Could emit UserEmailChanged event here
```

---

### 2. Specifications (Optional)

**Purpose:** Encapsulate business rules as reusable, composable objects.

**When to use:**
- Complex filtering/querying logic
- Business rules that need to be reused
- Rules that need to be composed (AND, OR, NOT)

**Example:**
```python
# backend/app/specifications/user_specs.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")

class Specification(ABC, Generic[T]):
    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        pass

    def __and__(self, other: "Specification[T]") -> "Specification[T]":
        return AndSpecification(self, other)

    def __or__(self, other: "Specification[T]") -> "Specification[T]":
        return OrSpecification(self, other)

class ActiveUserSpecification(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.is_active and not user.is_deleted

class PremiumUserSpecification(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.subscription_tier == "premium"

# Compose specifications
active_premium = ActiveUserSpecification() & PremiumUserSpecification()
```

---

### 3. Repository / Data Layer

**Purpose:** Abstract data persistence operations.

**Components:**
- **Repositories**: Collection-like interfaces for entities
- **Database Migrations**: Schema changes
- **Query Builders**: Complex query construction

**Order within this layer:**
1. Create database migration
2. Implement repository interface
3. Implement concrete repository

**Example:**
```python
# backend/app/repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.user import User
from ..utils.result import Result

class UserRepository(ABC):
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[User]:
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def save(self, user: User) -> Result[User]:
        pass

    @abstractmethod
    def delete(self, id: int) -> Result[bool]:
        pass

# Concrete implementation
class SQLUserRepository(UserRepository):
    def __init__(self, db_session):
        self._session = db_session

    def find_by_id(self, id: int) -> Optional[User]:
        return self._session.query(UserModel).filter_by(id=id).first()

    # ... other implementations
```

---

### 4. Service Layer

**Purpose:** Implement use cases and orchestrate domain operations.

**Components:**
- **Application Services**: Coordinate work between domain objects
- **Use Cases**: Specific business operations
- **Event Handlers**: React to domain events

**Example:**
```python
# backend/app/services/user_service.py
from typing import Optional
from ..repositories.user_repository import UserRepository
from ..models.user import User, Email
from ..utils.result import Result
from ..utils.guard import Guard

class UserService:
    def __init__(self, user_repository: UserRepository):
        self._repo = user_repository

    def create_user(
        self,
        email: str,
        name: str,
    ) -> Result[User]:
        """Create a new user."""
        # Guard clauses
        Guard.against_empty(email, "email")
        Guard.against_empty(name, "name")
        Guard.against_invalid_email(email, "email")

        # Check for duplicates
        existing = self._repo.find_by_email(email)
        if existing:
            return Result.fail("Email already exists", "DUPLICATE_EMAIL")

        # Create entity
        user = User(
            id=None,  # Will be assigned by DB
            email=Email(email),
            name=name,
        )

        # Persist
        return self._repo.save(user)

    def change_user_email(
        self,
        user_id: int,
        new_email: str,
    ) -> Result[User]:
        """Change a user's email address."""
        Guard.against_invalid_email(new_email, "new_email")

        user = self._repo.find_by_id(user_id)
        if not user:
            return Result.fail("User not found", "NOT_FOUND")

        # Domain logic
        user.change_email(Email(new_email))

        return self._repo.save(user)
```

---

### 5. API Layer

**Purpose:** Handle HTTP requests and responses.

**Components:**
- **Routes/Controllers**: HTTP endpoint handlers
- **Request DTOs**: Validate incoming data
- **Response DTOs**: Structure outgoing data
- **Middleware**: Cross-cutting concerns (auth, logging)

**Example:**
```python
# backend/app/api/users.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from ..services.user_service import UserService
from ..schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])

class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: str

@router.post("/", response_model=UserResponse)
def create_user(
    request: UserCreateRequest,
    service: UserService = Depends(get_user_service),
):
    result = service.create_user(
        email=request.email,
        name=request.name,
    )

    if result.is_failure:
        raise HTTPException(
            status_code=400 if result.error_code == "DUPLICATE_EMAIL" else 500,
            detail=result.error,
        )

    user = result.value
    return UserResponse(
        id=user.id,
        email=user.email.value,
        name=user.name,
        created_at=user.created_at.isoformat(),
    )
```

---

### 6. UI Layer

**Purpose:** User interface components and interactions.

**Components:**
- **Pages**: Full page components
- **Components**: Reusable UI elements
- **State Management**: Client-side state
- **API Clients**: HTTP service wrappers

**Example (HTML/JavaScript):**
```html
<!-- frontend/users.html -->
<div id="user-form">
    <input type="email" id="email" placeholder="Email">
    <input type="text" id="name" placeholder="Name">
    <button onclick="createUser()">Create User</button>
</div>

<script>
async function createUser() {
    const response = await fetch('/api/users/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            email: document.getElementById('email').value,
            name: document.getElementById('name').value,
        }),
    });

    if (response.ok) {
        const user = await response.json();
        alert(`User created: ${user.name}`);
    } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
    }
}
</script>
```

---

## Testing Order

Write tests alongside or immediately after each layer:

| Layer | Test Type | Coverage Target |
|-------|-----------|-----------------|
| Domain | Unit tests | 100% |
| Specifications | Unit tests | 100% |
| Repository | Integration tests | 80% |
| Service | Unit + Integration | 90% |
| API | Integration/E2E | 80% |
| UI | E2E tests | Key flows |

---

## Anti-Patterns to Avoid

### ❌ Starting with API/UI
- Leads to anemic domain models
- Business logic leaks into controllers
- Hard to test

### ❌ Skipping Repository abstraction
- Tight coupling to database
- Difficult to mock for testing
- Hard to change data source

### ❌ Business logic in Controllers
- Violates single responsibility
- Code duplication across endpoints
- Harder to maintain

---

## Checklist

Before moving to the next layer:

- [ ] Current layer has tests
- [ ] No coupling to layers above
- [ ] Clear interfaces defined
- [ ] Documentation/docstrings added
- [ ] Naming conventions followed

---

**Version:** 1.0.0
**Updated:** 2024-12-24
