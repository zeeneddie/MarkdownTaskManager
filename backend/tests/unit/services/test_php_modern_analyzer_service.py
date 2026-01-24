"""
Unit tests for PHPModernAnalyzerService - B6 (Fase 24 GAP).

Tests cover:
- Service initialization
- PHP 8.x feature detection (attributes, enums, readonly, match, etc.)
- Constructor property promotion detection
- Composer analysis
- Laravel modern pattern detection (Livewire, Actions)
- Symfony modern pattern detection (Messenger, Attributes)
- Migration recommendations
- Modernization score calculation

Author: Claude Code (Week 159)
Date: 2026-01-24
"""

import pytest
from pathlib import Path
import tempfile
import json

from app.services.php_modern_analyzer_service import (
    PHPModernAnalyzerService,
    PHPModernAnalysisResult,
    PHP8Feature,
    PHP8Enum,
    PHP8Attribute,
    ReadonlyProperty,
    ConstructorPromotion,
    ComposerAnalysis,
    ComposerPackage,
    LivewireComponent,
    LaravelAction,
    SymfonyMessengerHandler,
    PHPVersion,
    FrameworkType,
    DependencyStatus,
)


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """Create a fresh PHPModernAnalyzerService instance."""
    return PHPModernAnalyzerService()


@pytest.fixture
def sample_php8_attributes():
    """Sample PHP 8 code with attributes."""
    return '''<?php

#[Route('/api/users')]
#[Controller]
class UserController
{
    #[Get]
    #[Middleware('auth')]
    public function index(): Response
    {
        return new Response();
    }

    #[Post]
    #[Validate(UserDto::class)]
    public function store(Request $request): Response
    {
        return new Response();
    }
}
'''


@pytest.fixture
def sample_php8_enum():
    """Sample PHP 8.1 enum code."""
    return '''<?php

enum Status: string
{
    case PENDING = 'pending';
    case APPROVED = 'approved';
    case REJECTED = 'rejected';

    public function label(): string
    {
        return match($this) {
            self::PENDING => 'Awaiting Review',
            self::APPROVED => 'Approved',
            self::REJECTED => 'Rejected',
        };
    }

    public function color(): string
    {
        return match($this) {
            self::PENDING => 'yellow',
            self::APPROVED => 'green',
            self::REJECTED => 'red',
        };
    }
}

enum Priority: int implements HasLabel
{
    case LOW = 1;
    case MEDIUM = 2;
    case HIGH = 3;
}
'''


@pytest.fixture
def sample_readonly_properties():
    """Sample PHP 8.1 readonly properties."""
    return '''<?php

class User
{
    public readonly string $id;
    public readonly string $email;
    private readonly DateTime $createdAt;
    protected readonly int $status;

    public function __construct(
        string $id,
        string $email
    ) {
        $this->id = $id;
        $this->email = $email;
        $this->createdAt = new DateTime();
    }
}
'''


@pytest.fixture
def sample_constructor_promotion():
    """Sample PHP 8 constructor property promotion."""
    return '''<?php

class Order
{
    public function __construct(
        public readonly string $id,
        private string $customerName,
        protected int $quantity = 1,
        public ?DateTime $createdAt = null
    ) {
        $this->createdAt ??= new DateTime();
    }
}

class Product
{
    public function __construct(
        public string $name,
        public float $price,
        private readonly int $stock
    ) {}
}
'''


@pytest.fixture
def sample_match_expression():
    """Sample PHP 8 match expression."""
    return '''<?php

function getStatusLabel(int $status): string
{
    return match($status) {
        1 => 'Active',
        2 => 'Inactive',
        3 => 'Pending',
        default => 'Unknown',
    };
}

$result = match(true) {
    $age < 18 => 'minor',
    $age >= 18 && $age < 65 => 'adult',
    default => 'senior',
};
'''


@pytest.fixture
def sample_nullsafe_operator():
    """Sample PHP 8 nullsafe operator usage."""
    return '''<?php

$country = $user?->getAddress()?->getCountry()?->getName();

$result = $object?->method()?->property;
'''


@pytest.fixture
def sample_union_types():
    """Sample PHP 8 union types."""
    return '''<?php

function processInput(int|string $input): int|float
{
    return is_string($input) ? strlen($input) : $input;
}

function getValue(): string|null|false
{
    return false;
}
'''


@pytest.fixture
def sample_livewire_component():
    """Sample Laravel Livewire component."""
    return '''<?php

namespace App\\Http\\Livewire;

use Livewire\\Component;

class Counter extends Component
{
    public int $count = 0;
    public string $name = '';

    public function increment(): void
    {
        $this->count++;
    }

    public function decrement(): void
    {
        $this->count--;
    }

    public function render()
    {
        return view('livewire.counter');
    }
}
'''


@pytest.fixture
def sample_laravel_action():
    """Sample Laravel Action class."""
    return '''<?php

namespace App\\Actions;

use Lorisleiva\\Actions\\Concerns\\AsAction;
use Lorisleiva\\Actions\\Concerns\\AsController;
use Lorisleiva\\Actions\\Concerns\\AsJob;
use Lorisleiva\\Actions\\Concerns\\AsListener;

class CreateUser
{
    use AsAction;
    use AsController;
    use AsJob;

    public function handle(array $data): User
    {
        return User::create([
            'name' => $data['name'],
            'email' => $data['email'],
        ]);
    }
}
'''


@pytest.fixture
def sample_symfony_messenger():
    """Sample Symfony Messenger handler."""
    return '''<?php

namespace App\\MessageHandler;

use App\\Message\\SendNotification;
use Symfony\\Component\\Messenger\\Attribute\\AsMessageHandler;

#[AsMessageHandler]
class SendNotificationHandler
{
    public function __invoke(SendNotification $message): void
    {
        // Handle the message
        $this->notifier->send($message->getNotification());
    }
}
'''


@pytest.fixture
def sample_composer_json():
    """Sample composer.json content."""
    return {
        "name": "my-app/my-project",
        "description": "My PHP project",
        "require": {
            "php": "^8.1",
            "laravel/framework": "^10.0",
            "livewire/livewire": "^3.0",
            "swiftmailer/swiftmailer": "^6.0"  # Abandoned package
        },
        "require-dev": {
            "phpunit/phpunit": "^10.0",
            "pestphp/pest": "^2.0"
        },
        "autoload": {
            "psr-4": {
                "App\\\\": "src/"
            }
        }
    }


# ==================== Service Initialization Tests ====================

class TestServiceInitialization:
    """Tests for service initialization."""

    def test_service_initializes_successfully(self, service):
        """Service should initialize without errors."""
        assert service is not None

    def test_service_has_compiled_patterns(self, service):
        """Service should have compiled regex patterns."""
        assert hasattr(service, '_compiled_php8_patterns')
        assert len(service._compiled_php8_patterns) > 0

    def test_service_has_laravel_patterns(self, service):
        """Service should have Laravel patterns."""
        assert hasattr(service, '_compiled_laravel_patterns')
        assert len(service._compiled_laravel_patterns) > 0

    def test_service_has_symfony_patterns(self, service):
        """Service should have Symfony patterns."""
        assert hasattr(service, '_compiled_symfony_patterns')
        assert len(service._compiled_symfony_patterns) > 0


# ==================== PHP 8 Attribute Tests ====================

class TestPHP8Attributes:
    """Tests for PHP 8 attribute detection."""

    def test_detect_attributes(self, service, sample_php8_attributes):
        """Should detect PHP 8 attributes."""
        path = Path("/test/UserController.php")
        attributes = service._detect_attributes(path, sample_php8_attributes)

        assert len(attributes) >= 4
        names = {a.name for a in attributes}
        assert "Route" in names or any("Route" in n for n in names)

    def test_detect_attribute_arguments(self, service, sample_php8_attributes):
        """Should detect attribute arguments."""
        path = Path("/test/UserController.php")
        attributes = service._detect_attributes(path, sample_php8_attributes)

        # Find Route attribute with argument
        route_attrs = [a for a in attributes if "Route" in a.name]
        assert len(route_attrs) >= 1

    def test_detect_attribute_target(self, service, sample_php8_attributes):
        """Should detect attribute target (class, method, property)."""
        path = Path("/test/UserController.php")
        attributes = service._detect_attributes(path, sample_php8_attributes)

        targets = {a.target for a in attributes}
        assert "class" in targets or "method" in targets


# ==================== PHP 8.1 Enum Tests ====================

class TestPHP8Enums:
    """Tests for PHP 8.1 enum detection."""

    def test_detect_enums(self, service, sample_php8_enum):
        """Should detect PHP 8.1 enums."""
        path = Path("/test/Status.php")
        enums = service._detect_enums(path, sample_php8_enum)

        assert len(enums) >= 1

    def test_detect_backed_enum(self, service, sample_php8_enum):
        """Should detect backed enum type."""
        path = Path("/test/Status.php")
        enums = service._detect_enums(path, sample_php8_enum)

        status_enum = next((e for e in enums if e.enum_name == "Status"), None)
        assert status_enum is not None
        assert status_enum.backed_type == "string"

    def test_detect_enum_cases(self, service, sample_php8_enum):
        """Should detect enum cases."""
        path = Path("/test/Status.php")
        enums = service._detect_enums(path, sample_php8_enum)

        status_enum = next((e for e in enums if e.enum_name == "Status"), None)
        assert status_enum is not None
        assert len(status_enum.cases) >= 3

    def test_detect_enum_methods(self, service, sample_php8_enum):
        """Should detect enum methods."""
        path = Path("/test/Status.php")
        enums = service._detect_enums(path, sample_php8_enum)

        status_enum = next((e for e in enums if e.enum_name == "Status"), None)
        assert status_enum is not None
        # Should detect at least one method
        assert len(status_enum.methods) >= 1


# ==================== Readonly Property Tests ====================

class TestReadonlyProperties:
    """Tests for readonly property detection."""

    def test_detect_readonly_properties(self, service, sample_readonly_properties):
        """Should detect readonly properties."""
        path = Path("/test/User.php")
        properties = service._detect_readonly_properties(path, sample_readonly_properties)

        assert len(properties) >= 3

    def test_detect_property_types(self, service, sample_readonly_properties):
        """Should detect property types."""
        path = Path("/test/User.php")
        properties = service._detect_readonly_properties(path, sample_readonly_properties)

        types = {p.property_type for p in properties}
        assert "string" in types


# ==================== Constructor Promotion Tests ====================

class TestConstructorPromotion:
    """Tests for constructor property promotion detection."""

    def test_detect_constructor_promotion(self, service, sample_constructor_promotion):
        """Should detect constructor property promotion."""
        path = Path("/test/Order.php")
        promotions = service._detect_constructor_promotion(path, sample_constructor_promotion)

        assert len(promotions) >= 1

    def test_detect_promoted_properties(self, service, sample_constructor_promotion):
        """Should detect promoted property details."""
        path = Path("/test/Order.php")
        promotions = service._detect_constructor_promotion(path, sample_constructor_promotion)

        assert len(promotions) >= 1
        # First promotion should have multiple properties
        if promotions:
            assert len(promotions[0].promoted_properties) >= 1


# ==================== Match Expression Tests ====================

class TestMatchExpression:
    """Tests for PHP 8 match expression detection."""

    def test_detect_match_expressions(self, service, sample_match_expression):
        """Should detect match expressions."""
        path = Path("/test/helpers.php")
        result = PHPModernAnalysisResult()

        # Use the internal analysis method
        # Match expression is detected via pattern matching
        for name, pattern in service._compiled_php8_patterns.items():
            if name == "match_expression":
                matches = pattern.findall(sample_match_expression)
                assert len(matches) >= 1


# ==================== Nullsafe Operator Tests ====================

class TestNullsafeOperator:
    """Tests for PHP 8 nullsafe operator detection."""

    def test_detect_nullsafe_operator(self, service, sample_nullsafe_operator):
        """Should detect nullsafe operator usage."""
        for name, pattern in service._compiled_php8_patterns.items():
            if name == "nullsafe_operator":
                matches = pattern.findall(sample_nullsafe_operator)
                assert len(matches) >= 2


# ==================== Union Types Tests ====================

class TestUnionTypes:
    """Tests for PHP 8 union type detection."""

    def test_detect_union_types(self, service, sample_union_types):
        """Should detect union type declarations."""
        for name, pattern in service._compiled_php8_patterns.items():
            if name == "union_types":
                matches = pattern.findall(sample_union_types)
                assert len(matches) >= 1


# ==================== Composer Analysis Tests ====================

class TestComposerAnalysis:
    """Tests for Composer dependency analysis."""

    @pytest.mark.asyncio
    async def test_analyze_composer_json(self, service, sample_composer_json):
        """Should analyze composer.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer_file = Path(tmpdir) / "composer.json"
            composer_file.write_text(json.dumps(sample_composer_json))

            analysis = await service._analyze_composer(Path(tmpdir))

            assert analysis is not None
            assert analysis.project_name == "my-app/my-project"
            assert analysis.php_version_required == "^8.1"

    @pytest.mark.asyncio
    async def test_detect_abandoned_packages(self, service, sample_composer_json):
        """Should detect abandoned packages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer_file = Path(tmpdir) / "composer.json"
            composer_file.write_text(json.dumps(sample_composer_json))

            analysis = await service._analyze_composer(Path(tmpdir))

            assert analysis is not None
            assert analysis.abandoned_packages >= 1

            # swiftmailer should be marked as abandoned
            abandoned = [p for p in analysis.packages if p.is_abandoned]
            assert len(abandoned) >= 1

    @pytest.mark.asyncio
    async def test_detect_psr4_compliance(self, service, sample_composer_json):
        """Should detect PSR-4 autoloading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer_file = Path(tmpdir) / "composer.json"
            composer_file.write_text(json.dumps(sample_composer_json))

            analysis = await service._analyze_composer(Path(tmpdir))

            assert analysis is not None
            assert analysis.psr4_compliant is True

    @pytest.mark.asyncio
    async def test_detect_framework(self, service, sample_composer_json):
        """Should detect Laravel framework."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer_file = Path(tmpdir) / "composer.json"
            composer_file.write_text(json.dumps(sample_composer_json))

            analysis = await service._analyze_composer(Path(tmpdir))
            framework = service._detect_framework_from_composer(analysis)

            assert framework == FrameworkType.LARAVEL


# ==================== Laravel Pattern Tests ====================

class TestLaravelPatterns:
    """Tests for Laravel modern pattern detection."""

    def test_detect_livewire_component(self, service, sample_livewire_component):
        """Should detect Livewire component."""
        path = Path("/test/Counter.php")
        component = service._detect_livewire_component(path, sample_livewire_component)

        assert component is not None
        assert component.component_name == "Counter"

    def test_detect_livewire_properties(self, service, sample_livewire_component):
        """Should detect Livewire public properties."""
        path = Path("/test/Counter.php")
        component = service._detect_livewire_component(path, sample_livewire_component)

        assert component is not None
        assert len(component.properties) >= 2

    def test_detect_livewire_actions(self, service, sample_livewire_component):
        """Should detect Livewire action methods."""
        path = Path("/test/Counter.php")
        component = service._detect_livewire_component(path, sample_livewire_component)

        assert component is not None
        assert len(component.actions) >= 2

    def test_detect_laravel_action(self, service, sample_laravel_action):
        """Should detect Laravel Action class."""
        path = Path("/test/CreateUser.php")
        action = service._detect_laravel_action(path, sample_laravel_action)

        assert action is not None
        assert action.class_name == "CreateUser"
        assert action.handle_method is True
        assert action.as_controller is True
        assert action.as_job is True


# ==================== Symfony Pattern Tests ====================

class TestSymfonyPatterns:
    """Tests for Symfony modern pattern detection."""

    def test_detect_messenger_handler(self, service, sample_symfony_messenger):
        """Should detect Symfony Messenger handler."""
        path = Path("/test/SendNotificationHandler.php")
        handler = service._detect_messenger_handler(path, sample_symfony_messenger)

        assert handler is not None
        assert handler.handler_class == "SendNotificationHandler"


# ==================== Recommendations Tests ====================

class TestRecommendations:
    """Tests for migration recommendations."""

    def test_generate_php_version_recommendation(self, service):
        """Should generate PHP version upgrade recommendation."""
        result = PHPModernAnalysisResult()
        result.detected_php_version = PHPVersion.UNKNOWN

        recommendations = service._generate_recommendations(result)

        php_recs = [r for r in recommendations if r["category"] == "php_version"]
        assert len(php_recs) >= 1

    def test_generate_abandoned_package_recommendation(self, service):
        """Should generate abandoned package recommendation."""
        result = PHPModernAnalysisResult()
        result.composer_analysis = ComposerAnalysis()
        result.composer_analysis.abandoned_packages = 2
        result.composer_analysis.psr4_compliant = True

        recommendations = service._generate_recommendations(result)

        dep_recs = [r for r in recommendations if r["category"] == "dependencies"]
        assert len(dep_recs) >= 1

    def test_generate_psr4_recommendation(self, service):
        """Should generate PSR-4 recommendation when not compliant."""
        result = PHPModernAnalysisResult()
        result.composer_analysis = ComposerAnalysis()
        result.composer_analysis.psr4_compliant = False
        result.composer_analysis.abandoned_packages = 0

        recommendations = service._generate_recommendations(result)

        autoload_recs = [r for r in recommendations if r["category"] == "autoloading"]
        assert len(autoload_recs) >= 1


# ==================== Modernization Score Tests ====================

class TestModernizationScore:
    """Tests for modernization score calculation."""

    def test_score_with_php8_features(self, service):
        """Should increase score for PHP 8 features."""
        result = PHPModernAnalysisResult()
        result.php8_features = [PHP8Feature(
            feature_name="match_expression",
            php_version_required="8.0",
            file_path="/test.php",
            line_number=10,
            code_snippet="match($x) {}",
            description="Match expression"
        ) for _ in range(5)]

        service._calculate_metrics(result)

        assert result.modernization_score > 0

    def test_score_with_composer_setup(self, service):
        """Should increase score for good Composer setup."""
        result = PHPModernAnalysisResult()
        result.composer_analysis = ComposerAnalysis()
        result.composer_analysis.psr4_compliant = True
        result.composer_analysis.has_lock_file = True
        result.composer_analysis.abandoned_packages = 0

        service._calculate_metrics(result)

        assert result.modernization_score >= 20


# ==================== Integration Tests ====================

class TestFullAnalysis:
    """Integration tests for full project analysis."""

    @pytest.mark.asyncio
    async def test_analyze_empty_path_returns_result(self, service):
        """Analyzing empty path should return empty result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await service.analyze(tmpdir)
            assert isinstance(result, PHPModernAnalysisResult)
            assert result.total_files_scanned == 0

    @pytest.mark.asyncio
    async def test_analyze_project_with_php_files(self, service, sample_php8_enum):
        """Should analyze project with PHP files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            php_file = Path(tmpdir) / "Status.php"
            php_file.write_text(sample_php8_enum)

            result = await service.analyze(tmpdir, include_composer=False)

            assert result.total_files_scanned >= 1
            assert len(result.php8_enums) >= 1

    @pytest.mark.asyncio
    async def test_get_summary(self, service, sample_php8_enum, sample_composer_json):
        """Should generate proper summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            php_file = Path(tmpdir) / "Status.php"
            php_file.write_text(sample_php8_enum)

            composer_file = Path(tmpdir) / "composer.json"
            composer_file.write_text(json.dumps(sample_composer_json))

            result = await service.analyze(tmpdir)
            summary = service.get_summary(result)

            assert "php_version" in summary
            assert "framework" in summary
            assert "php8_features" in summary
            assert "composer" in summary
            assert "metrics" in summary


# ==================== Edge Cases ====================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_file_content(self, service):
        """Should handle empty file content."""
        path = Path("/test/empty.php")
        enums = service._detect_enums(path, "")
        assert enums == []

    def test_invalid_php_content(self, service):
        """Should handle invalid PHP content gracefully."""
        invalid_content = "This is not valid PHP code {{ random symbols }}"
        path = Path("/test/invalid.php")
        enums = service._detect_enums(path, invalid_content)
        assert isinstance(enums, list)

    @pytest.mark.asyncio
    async def test_missing_composer_json(self, service):
        """Should handle missing composer.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analysis = await service._analyze_composer(Path(tmpdir))
            assert analysis is None

    def test_is_abandoned_package(self, service):
        """Should correctly identify abandoned packages."""
        assert service._is_abandoned_package("swiftmailer/swiftmailer") is True
        assert service._is_abandoned_package("laravel/framework") is False
