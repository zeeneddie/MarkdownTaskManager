"""
Frontend Analyzer Service

Week 65 Day 5: Specialized analyzer for frontend legacy code.
Detects AngularJS, Vue 2, React class components, and jQuery patterns.

Features:
- AngularJS pattern detection ($scope, ng-directives, controllers)
- Vue 2 Options API detection (data(), computed, watch)
- React class component detection (extends Component, this.state)
- jQuery legacy pattern detection ($.ajax, event handlers)
- Module dependency analysis
- Migration recommendations to modern frameworks

Author: Claude Code (Week 65)
Date: 2025-12-12
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.migration_analysis import (
    MigrationAnalysis,
    MigrationModule,
    LegacyPattern,
    FPBreakdown
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AngularJSModule:
    """Represents an AngularJS module"""
    file_path: str
    module_name: str
    controllers: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    factories: List[str] = field(default_factory=list)
    directives: List[str] = field(default_factory=list)
    filters: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    scope_usages: int = 0
    http_calls: int = 0
    loc: int = 0
    complexity: float = 0.0


@dataclass
class VueComponent:
    """Represents a Vue 2 component"""
    file_path: str
    component_name: str
    is_sfc: bool = False  # Single File Component (.vue)
    options_api: bool = True  # Options API vs Composition API
    data_properties: List[str] = field(default_factory=list)
    computed_properties: List[str] = field(default_factory=list)
    watchers: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    lifecycle_hooks: List[str] = field(default_factory=list)
    props: List[str] = field(default_factory=list)
    emits: List[str] = field(default_factory=list)
    vuex_usage: bool = False
    loc: int = 0
    complexity: float = 0.0


@dataclass
class ReactComponent:
    """Represents a React component"""
    file_path: str
    component_name: str
    is_class: bool = True  # Class vs Functional
    state_properties: List[str] = field(default_factory=list)
    lifecycle_methods: List[str] = field(default_factory=list)
    event_handlers: List[str] = field(default_factory=list)
    redux_connected: bool = False
    hooks_used: List[str] = field(default_factory=list)
    loc: int = 0
    complexity: float = 0.0


@dataclass 
class JQueryUsage:
    """Represents jQuery usage in a file"""
    file_path: str
    selector_count: int = 0
    ajax_calls: int = 0
    event_bindings: int = 0
    dom_manipulations: int = 0
    animations: int = 0
    plugins: List[str] = field(default_factory=list)
    loc: int = 0


@dataclass
class FrontendPatternMatch:
    """A detected frontend legacy pattern"""
    pattern_name: str
    pattern_category: str
    file_path: str
    line_number: int
    code_snippet: str
    risk_level: str
    migration_note: str
    migration_target: str
    fp_multiplier: float = 1.0
    is_security_issue: bool = False


@dataclass
class FrontendAnalysisResult:
    """Complete frontend analysis result"""
    angularjs_modules: List[AngularJSModule] = field(default_factory=list)
    vue_components: List[VueComponent] = field(default_factory=list)
    react_components: List[ReactComponent] = field(default_factory=list)
    jquery_usages: List[JQueryUsage] = field(default_factory=list)
    legacy_patterns: List[FrontendPatternMatch] = field(default_factory=list)
    total_js_files: int = 0
    total_ts_files: int = 0
    total_vue_files: int = 0
    total_jsx_files: int = 0
    total_loc: int = 0
    primary_framework: Optional[str] = None
    migration_difficulty: str = "medium"


# ============================================================================
# PATTERN DEFINITIONS
# ============================================================================

# AngularJS patterns (1.x)
ANGULARJS_PATTERNS = {
    "scope_usage": {
        "pattern": r'\$scope\.',
        "risk": "high",
        "note": "$scope is deprecated, two-way binding causes performance issues",
        "target": "Angular signals or Vue 3 reactive refs",
        "multiplier": 1.4,
    },
    "rootscope": {
        "pattern": r'\$rootScope',
        "risk": "high", 
        "note": "$rootScope creates global state pollution",
        "target": "State management (NgRx, Pinia, Redux)",
        "multiplier": 1.5,
    },
    "ng_controller": {
        "pattern": r'\.controller\s*\(|ng-controller',
        "risk": "medium",
        "note": "Controllers need conversion to components",
        "target": "Angular standalone components or Vue 3 components",
        "multiplier": 1.3,
    },
    "ng_directive": {
        "pattern": r'\.directive\s*\(',
        "risk": "medium",
        "note": "Directives need conversion to modern syntax",
        "target": "Angular directives or Vue 3 directives",
        "multiplier": 1.3,
    },
    "ng_service": {
        "pattern": r'\.service\s*\(|\.factory\s*\(',
        "risk": "low",
        "note": "Services can often be converted directly",
        "target": "Angular injectable services or composables",
        "multiplier": 1.1,
    },
    "ng_http": {
        "pattern": r'\$http\.',
        "risk": "medium",
        "note": "$http needs conversion to modern HTTP client",
        "target": "HttpClient, Axios, or fetch API",
        "multiplier": 1.2,
    },
    "ng_resource": {
        "pattern": r'\$resource\(',
        "risk": "medium",
        "note": "$resource is deprecated, use modern REST clients",
        "target": "Angular HttpClient or RTK Query",
        "multiplier": 1.3,
    },
    "ng_watch": {
        "pattern": r'\$watch\s*\(|\$watchCollection',
        "risk": "high",
        "note": "Watchers cause digest cycle issues",
        "target": "Computed properties or reactive effects",
        "multiplier": 1.4,
    },
    "ng_apply_digest": {
        "pattern": r'\$apply\s*\(|\$digest\s*\(',
        "risk": "high",
        "note": "Manual digest triggers indicate integration issues",
        "target": "Zone.js or framework-native reactivity",
        "multiplier": 1.5,
    },
    "ng_compile": {
        "pattern": r'\$compile\s*\(',
        "risk": "critical",
        "note": "Dynamic compilation is a security risk",
        "target": "Dynamic components with sanitization",
        "multiplier": 2.0,
        "security": True,
    },
    "ng_template_binding": {
        "pattern": r'ng-bind-html|ng-bind-unsafe',
        "risk": "critical",
        "note": "HTML binding without sanitization is XSS risk",
        "target": "DomSanitizer or v-html with sanitization",
        "multiplier": 1.8,
        "security": True,
    },
}

# Vue 2 Options API patterns
VUE2_PATTERNS = {
    "options_data": {
        "pattern": r'data\s*\(\s*\)\s*{\s*return|data:\s*function\s*\(\)',
        "risk": "low",
        "note": "Options API data() needs conversion to Composition API",
        "target": "Vue 3 ref() or reactive()",
        "multiplier": 1.1,
    },
    "options_computed": {
        "pattern": r'computed\s*:\s*{',
        "risk": "low",
        "note": "Computed properties map to computed()",
        "target": "Vue 3 computed()",
        "multiplier": 1.0,
    },
    "options_watch": {
        "pattern": r'watch\s*:\s*{',
        "risk": "low",
        "note": "Watchers map to watch() or watchEffect()",
        "target": "Vue 3 watch() or watchEffect()",
        "multiplier": 1.1,
    },
    "vue_extend": {
        "pattern": r'Vue\.extend\s*\(',
        "risk": "medium",
        "note": "Vue.extend is deprecated in Vue 3",
        "target": "defineComponent() or <script setup>",
        "multiplier": 1.3,
    },
    "vue_set_delete": {
        "pattern": r'Vue\.\$set|Vue\.\$delete|this\.\$set|this\.\$delete',
        "risk": "medium",
        "note": "$set/$delete not needed with Proxy-based reactivity",
        "target": "Direct property assignment in Vue 3",
        "multiplier": 1.2,
    },
    "this_emit": {
        "pattern": r'this\.\$emit\s*\(',
        "risk": "low",
        "note": "$emit works but defineEmits is preferred",
        "target": "defineEmits() macro",
        "multiplier": 1.0,
    },
    "this_refs": {
        "pattern": r'this\.\$refs\.',
        "risk": "medium",
        "note": "$refs access pattern changes in Composition API",
        "target": "Template refs with ref()",
        "multiplier": 1.2,
    },
    "vuex_mapstate": {
        "pattern": r'mapState\(|mapGetters\(|mapMutations\(|mapActions\(',
        "risk": "medium",
        "note": "Vuex helpers need Pinia migration",
        "target": "Pinia stores with storeToRefs()",
        "multiplier": 1.3,
    },
    "event_bus": {
        "pattern": r'EventBus\.\$emit|EventBus\.\$on|\$bus\.',
        "risk": "high",
        "note": "Event bus pattern removed in Vue 3",
        "target": "Pinia stores or provide/inject",
        "multiplier": 1.5,
    },
    "filters": {
        "pattern": r'Vue\.filter\(|filters\s*:\s*{',
        "risk": "medium",
        "note": "Filters removed in Vue 3",
        "target": "Computed properties or methods",
        "multiplier": 1.3,
    },
}

# React class component patterns
REACT_CLASS_PATTERNS = {
    "class_component": {
        "pattern": r'class\s+\w+\s+extends\s+(React\.)?Component',
        "risk": "medium",
        "note": "Class components should be converted to functional",
        "target": "Functional components with hooks",
        "multiplier": 1.3,
    },
    "pure_component": {
        "pattern": r'extends\s+(React\.)?PureComponent',
        "risk": "low",
        "note": "PureComponent can use React.memo()",
        "target": "React.memo() with functional component",
        "multiplier": 1.1,
    },
    "constructor_state": {
        "pattern": r'this\.state\s*=\s*{',
        "risk": "medium",
        "note": "Constructor state init converts to useState",
        "target": "useState() hook",
        "multiplier": 1.2,
    },
    "set_state": {
        "pattern": r'this\.setState\s*\(',
        "risk": "medium",
        "note": "setState converts to useState setter",
        "target": "useState() setter function",
        "multiplier": 1.2,
    },
    "component_did_mount": {
        "pattern": r'componentDidMount\s*\(',
        "risk": "medium",
        "note": "componentDidMount converts to useEffect",
        "target": "useEffect(() => {}, [])",
        "multiplier": 1.2,
    },
    "component_will_unmount": {
        "pattern": r'componentWillUnmount\s*\(',
        "risk": "medium",
        "note": "componentWillUnmount is useEffect cleanup",
        "target": "useEffect cleanup function",
        "multiplier": 1.2,
    },
    "component_did_update": {
        "pattern": r'componentDidUpdate\s*\(',
        "risk": "medium",
        "note": "componentDidUpdate converts to useEffect with deps",
        "target": "useEffect with dependency array",
        "multiplier": 1.3,
    },
    "deprecated_lifecycle": {
        "pattern": r'componentWillMount|componentWillReceiveProps|componentWillUpdate',
        "risk": "high",
        "note": "Deprecated lifecycle methods must be removed",
        "target": "useEffect or getDerivedStateFromProps",
        "multiplier": 1.5,
    },
    "create_ref": {
        "pattern": r'React\.createRef\s*\(\)|createRef\s*\(',
        "risk": "low",
        "note": "createRef converts to useRef",
        "target": "useRef() hook",
        "multiplier": 1.1,
    },
    "redux_connect": {
        "pattern": r'connect\s*\(\s*mapStateToProps',
        "risk": "medium",
        "note": "connect() HOC replaced by hooks",
        "target": "useSelector() and useDispatch()",
        "multiplier": 1.3,
    },
    "hoc_pattern": {
        "pattern": r'withRouter\(|withStyles\(|withTheme\(',
        "risk": "medium",
        "note": "HOC patterns replaced by hooks",
        "target": "useNavigate(), useTheme() hooks",
        "multiplier": 1.3,
    },
    "dangerous_html": {
        "pattern": r'dangerouslySetInnerHTML',
        "risk": "high",
        "note": "innerHTML is XSS risk, needs sanitization",
        "target": "DOMPurify or sanitize-html",
        "multiplier": 1.4,
        "security": True,
    },
}

# jQuery patterns
JQUERY_PATTERNS = {
    "selector": {
        "pattern": r'\$\s*\([\'"][^"\']+[\'"]\)',
        "risk": "medium",
        "note": "jQuery selectors should use native DOM or framework",
        "target": "document.querySelector or framework refs",
        "multiplier": 1.2,
    },
    "ajax": {
        "pattern": r'\$\.ajax\s*\(|\$\.get\s*\(|\$\.post\s*\(',
        "risk": "medium",
        "note": "jQuery AJAX replaced by fetch or axios",
        "target": "fetch API or axios",
        "multiplier": 1.2,
    },
    "event_binding": {
        "pattern": r'\.(click|change|submit|focus|blur|keyup|keydown)\s*\(',
        "risk": "medium",
        "note": "Event binding should use framework events",
        "target": "@click, onClick, or addEventListener",
        "multiplier": 1.2,
    },
    "on_delegate": {
        "pattern": r'\.on\s*\([\'"][^"\']+[\'"]',
        "risk": "medium",
        "note": "Event delegation needs framework equivalent",
        "target": "Event delegation in framework",
        "multiplier": 1.3,
    },
    "dom_manipulation": {
        "pattern": r'\.(append|prepend|after|before|html|text|val|attr|css|addClass|removeClass)\s*\(',
        "risk": "high",
        "note": "DOM manipulation conflicts with virtual DOM",
        "target": "Reactive data binding",
        "multiplier": 1.4,
    },
    "animation": {
        "pattern": r'\.(animate|fadeIn|fadeOut|slideUp|slideDown|show|hide)\s*\(',
        "risk": "medium",
        "note": "jQuery animations replaced by CSS or libraries",
        "target": "CSS transitions or Framer Motion",
        "multiplier": 1.2,
    },
    "ready": {
        "pattern": r'\$\s*\(\s*document\s*\)\s*\.ready|\$\s*\(\s*function',
        "risk": "low",
        "note": "Document ready not needed with frameworks",
        "target": "Framework lifecycle hooks",
        "multiplier": 1.0,
    },
    "global_jquery": {
        "pattern": r'window\.\$|window\.jQuery',
        "risk": "medium",
        "note": "Global jQuery should be modular import",
        "target": "ES module import",
        "multiplier": 1.1,
    },
}


# ============================================================================
# FRONTEND ANALYZER SERVICE
# ============================================================================

class FrontendAnalyzerService:
    """
    Specialized analyzer for frontend legacy code.
    
    Analyzes:
    - AngularJS 1.x (.js with angular patterns)
    - Vue 2 Options API (.vue, .js)
    - React class components (.jsx, .tsx)
    - jQuery usage (.js)
    """

    JS_EXTENSIONS = {".js", ".mjs"}
    TS_EXTENSIONS = {".ts"}
    JSX_EXTENSIONS = {".jsx", ".tsx"}
    VUE_EXTENSIONS = {".vue"}
    
    SKIP_DIRS = {"node_modules", "vendor", "dist", "build", ".git", "coverage"}

    def __init__(self, db: AsyncSession):
        """Initialize with database session"""
        self.db = db
        self.result = FrontendAnalysisResult()

    async def analyze(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> FrontendAnalysisResult:
        """
        Perform complete frontend analysis.
        
        Args:
            analysis: Parent MigrationAnalysis record
            repo_path: Path to repository
            
        Returns:
            FrontendAnalysisResult with all findings
        """
        logger.info(f"Starting frontend analysis for {repo_path}")

        # Phase 1: Scan for AngularJS
        await self._analyze_angularjs(analysis, repo_path)

        # Phase 2: Scan for Vue components
        await self._analyze_vue(analysis, repo_path)

        # Phase 3: Scan for React components
        await self._analyze_react(analysis, repo_path)

        # Phase 4: Scan for jQuery usage
        await self._analyze_jquery(analysis, repo_path)

        # Phase 5: Detect all legacy patterns
        await self._detect_legacy_patterns(analysis, repo_path)

        # Phase 6: Determine primary framework and difficulty
        self._calculate_metrics()

        logger.info(
            f"Frontend analysis complete: {len(self.result.angularjs_modules)} AngularJS, "
            f"{len(self.result.vue_components)} Vue, {len(self.result.react_components)} React, "
            f"{len(self.result.jquery_usages)} jQuery files"
        )

        return self.result

    async def _analyze_angularjs(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze AngularJS modules and controllers"""
        logger.info("Analyzing AngularJS...")

        for js_path in repo_path.rglob("*.js"):
            if self._should_skip(js_path):
                continue

            try:
                content = js_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Check if this is an AngularJS file
            if not self._is_angularjs_file(content):
                continue

            module = self._parse_angularjs_module(js_path, content, repo_path)
            if module:
                self.result.angularjs_modules.append(module)

                # Create module record
                db_module = MigrationModule(
                    analysis_id=analysis.id,
                    name=module.module_name,
                    module_type="angularjs_module",
                    stack_type="angularjs",
                    file_path=str(js_path.relative_to(repo_path)),
                    loc=module.loc,
                    cyclomatic_complexity=module.complexity,
                    migration_difficulty=self._assess_angularjs_difficulty(module),
                    migration_target="Angular standalone or Vue 3",
                    dependencies=module.dependencies,
                )
                self.db.add(db_module)

        await self.db.commit()

    def _is_angularjs_file(self, content: str) -> bool:
        """Check if content is AngularJS"""
        indicators = [
            "angular.module",
            ".controller(",
            ".directive(",
            ".service(",
            ".factory(",
            "$scope",
            "ng-app",
            "ng-controller",
        ]
        return any(ind in content for ind in indicators)

    def _parse_angularjs_module(
        self,
        file_path: Path,
        content: str,
        repo_path: Path
    ) -> Optional[AngularJSModule]:
        """Parse an AngularJS file"""
        # Extract module name
        module_match = re.search(r"angular\.module\s*\(\s*['\"]([^'\"]+)['\"]", content)
        module_name = module_match.group(1) if module_match else file_path.stem

        module = AngularJSModule(
            file_path=str(file_path.relative_to(repo_path)),
            module_name=module_name,
            loc=len([l for l in content.splitlines() if l.strip()]),
        )

        # Extract components
        module.controllers = re.findall(r"\.controller\s*\(\s*['\"]([^'\"]+)['\"]", content)
        module.services = re.findall(r"\.service\s*\(\s*['\"]([^'\"]+)['\"]", content)
        module.factories = re.findall(r"\.factory\s*\(\s*['\"]([^'\"]+)['\"]", content)
        module.directives = re.findall(r"\.directive\s*\(\s*['\"]([^'\"]+)['\"]", content)
        module.filters = re.findall(r"\.filter\s*\(\s*['\"]([^'\"]+)['\"]", content)

        # Extract dependencies
        deps_match = re.search(r"angular\.module\s*\(\s*['\"][^'\"]+['\"]\s*,\s*\[([^\]]*)\]", content)
        if deps_match:
            module.dependencies = re.findall(r"['\"]([^'\"]+)['\"]", deps_match.group(1))

        # Count patterns
        module.scope_usages = len(re.findall(r"\$scope\.", content))
        module.http_calls = len(re.findall(r"\$http\.", content))

        # Estimate complexity
        module.complexity = (
            len(module.controllers) * 2 +
            len(module.directives) * 3 +
            module.scope_usages * 0.5 +
            module.http_calls * 0.3
        )

        return module

    async def _analyze_vue(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze Vue components"""
        logger.info("Analyzing Vue components...")

        # Scan .vue files (SFCs)
        for vue_path in repo_path.rglob("*.vue"):
            if self._should_skip(vue_path):
                continue

            try:
                content = vue_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            component = self._parse_vue_component(vue_path, content, repo_path, is_sfc=True)
            if component:
                self.result.vue_components.append(component)
                self.result.total_vue_files += 1

                # Create module record
                db_module = MigrationModule(
                    analysis_id=analysis.id,
                    name=component.component_name,
                    module_type="vue_sfc" if component.is_sfc else "vue_component",
                    stack_type="vue2" if component.options_api else "vue3",
                    file_path=str(vue_path.relative_to(repo_path)),
                    loc=component.loc,
                    cyclomatic_complexity=component.complexity,
                    migration_difficulty=self._assess_vue_difficulty(component),
                    migration_target="Vue 3 Composition API",
                )
                self.db.add(db_module)

        await self.db.commit()

    def _parse_vue_component(
        self,
        file_path: Path,
        content: str,
        repo_path: Path,
        is_sfc: bool = False
    ) -> Optional[VueComponent]:
        """Parse a Vue component"""
        component = VueComponent(
            file_path=str(file_path.relative_to(repo_path)),
            component_name=file_path.stem,
            is_sfc=is_sfc,
            loc=len([l for l in content.splitlines() if l.strip()]),
        )

        # Check for Composition API (Vue 3)
        if "<script setup>" in content or "defineComponent" in content:
            component.options_api = False

        # Extract script content for SFC
        script_match = re.search(r"<script[^>]*>(.*?)</script>", content, re.DOTALL)
        script_content = script_match.group(1) if script_match else content

        # Extract data properties
        data_match = re.search(r"data\s*\(\s*\)\s*{\s*return\s*{([^}]*)}", script_content, re.DOTALL)
        if data_match:
            component.data_properties = re.findall(r"(\w+)\s*:", data_match.group(1))

        # Extract computed properties
        computed_match = re.search(r"computed\s*:\s*{([^}]*)}", script_content, re.DOTALL)
        if computed_match:
            component.computed_properties = re.findall(r"(\w+)\s*\(|(\w+)\s*:", computed_match.group(1))
            component.computed_properties = [p[0] or p[1] for p in component.computed_properties if p[0] or p[1]]

        # Extract methods
        methods_match = re.search(r"methods\s*:\s*{", script_content)
        if methods_match:
            component.methods = re.findall(r"(\w+)\s*\(", script_content[methods_match.end():])

        # Detect Vuex usage
        component.vuex_usage = bool(re.search(r"mapState|mapGetters|mapMutations|mapActions|\$store", content))

        # Lifecycle hooks
        hooks = ["created", "mounted", "beforeMount", "beforeCreate", "updated", "beforeUpdate", "destroyed", "beforeDestroy"]
        component.lifecycle_hooks = [h for h in hooks if re.search(rf"{h}\s*\(", script_content)]

        # Props
        props_match = re.search(r"props\s*:\s*[\[{]([^\]}]*)", script_content)
        if props_match:
            component.props = re.findall(r"['\"]?(\w+)['\"]?", props_match.group(1))

        # Complexity estimation
        component.complexity = (
            len(component.data_properties) * 0.5 +
            len(component.computed_properties) * 1 +
            len(component.methods) * 1.5 +
            len(component.lifecycle_hooks) * 1 +
            (5 if component.vuex_usage else 0)
        )

        return component

    async def _analyze_react(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze React components"""
        logger.info("Analyzing React components...")

        for ext in [".jsx", ".tsx", ".js"]:
            for file_path in repo_path.rglob(f"*{ext}"):
                if self._should_skip(file_path):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                # Check if this is a React file
                if not self._is_react_file(content):
                    continue

                component = self._parse_react_component(file_path, content, repo_path)
                if component:
                    self.result.react_components.append(component)
                    if ext in [".jsx", ".tsx"]:
                        self.result.total_jsx_files += 1

                    # Create module record
                    db_module = MigrationModule(
                        analysis_id=analysis.id,
                        name=component.component_name,
                        module_type="react_class" if component.is_class else "react_functional",
                        stack_type="react_class" if component.is_class else "react_hooks",
                        file_path=str(file_path.relative_to(repo_path)),
                        loc=component.loc,
                        cyclomatic_complexity=component.complexity,
                        migration_difficulty=self._assess_react_difficulty(component),
                        migration_target="React functional component with hooks",
                    )
                    self.db.add(db_module)

        await self.db.commit()

    def _is_react_file(self, content: str) -> bool:
        """Check if content is React"""
        indicators = [
            "import React",
            "from 'react'",
            'from "react"',
            "extends Component",
            "extends React.Component",
            "useState(",
            "useEffect(",
            "React.createElement",
        ]
        return any(ind in content for ind in indicators)

    def _parse_react_component(
        self,
        file_path: Path,
        content: str,
        repo_path: Path
    ) -> Optional[ReactComponent]:
        """Parse a React component"""
        # Extract component name
        class_match = re.search(r"class\s+(\w+)\s+extends", content)
        func_match = re.search(r"(?:export\s+)?(?:default\s+)?function\s+(\w+)", content)
        const_match = re.search(r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=])\s*=>", content)
        
        component_name = file_path.stem
        if class_match:
            component_name = class_match.group(1)
        elif func_match:
            component_name = func_match.group(1)
        elif const_match:
            component_name = const_match.group(1)

        component = ReactComponent(
            file_path=str(file_path.relative_to(repo_path)),
            component_name=component_name,
            is_class=bool(class_match),
            loc=len([l for l in content.splitlines() if l.strip()]),
        )

        # Extract state properties (class components)
        state_match = re.search(r"this\.state\s*=\s*{([^}]*)}", content)
        if state_match:
            component.state_properties = re.findall(r"(\w+)\s*:", state_match.group(1))

        # Lifecycle methods
        lifecycles = ["componentDidMount", "componentWillUnmount", "componentDidUpdate", 
                     "shouldComponentUpdate", "componentWillMount", "componentWillReceiveProps"]
        component.lifecycle_methods = [lc for lc in lifecycles if lc in content]

        # Hooks used
        hooks = ["useState", "useEffect", "useContext", "useReducer", "useCallback", 
                "useMemo", "useRef", "useLayoutEffect"]
        component.hooks_used = [h for h in hooks if f"{h}(" in content]

        # Redux connected
        component.redux_connected = bool(re.search(r"connect\s*\(|useSelector\(|useDispatch\(", content))

        # Event handlers
        component.event_handlers = re.findall(r"handle(\w+)|on(\w+)\s*=", content)

        # Complexity
        component.complexity = (
            len(component.state_properties) * 1 +
            len(component.lifecycle_methods) * 2 +
            len(component.hooks_used) * 0.5 +
            (5 if component.redux_connected else 0) +
            (3 if component.is_class else 0)
        )

        return component

    async def _analyze_jquery(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze jQuery usage"""
        logger.info("Analyzing jQuery usage...")

        for js_path in repo_path.rglob("*.js"):
            if self._should_skip(js_path):
                continue

            try:
                content = js_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Check if jQuery is used
            if not self._has_jquery(content):
                continue

            usage = self._parse_jquery_usage(js_path, content, repo_path)
            if usage:
                self.result.jquery_usages.append(usage)

        await self.db.commit()

    def _has_jquery(self, content: str) -> bool:
        """Check if content uses jQuery"""
        indicators = [
            "jQuery(",
            "$(",
            "$.ajax",
            "$.get",
            "$.post",
            ".ready(",
        ]
        return any(ind in content for ind in indicators)

    def _parse_jquery_usage(
        self,
        file_path: Path,
        content: str,
        repo_path: Path
    ) -> Optional[JQueryUsage]:
        """Parse jQuery usage in a file"""
        usage = JQueryUsage(
            file_path=str(file_path.relative_to(repo_path)),
            loc=len([l for l in content.splitlines() if l.strip()]),
        )

        # Count selectors
        usage.selector_count = len(re.findall(r"\$\s*\(['\"][^'\"]+['\"]\)", content))

        # Count AJAX calls
        usage.ajax_calls = len(re.findall(r"\$\.(ajax|get|post|getJSON)\s*\(", content))

        # Count event bindings
        usage.event_bindings = len(re.findall(r"\.(on|click|change|submit|keyup|keydown|focus|blur)\s*\(", content))

        # Count DOM manipulations
        usage.dom_manipulations = len(re.findall(
            r"\.(append|prepend|after|before|html|text|val|attr|css|addClass|removeClass|remove|empty)\s*\(",
            content
        ))

        # Count animations
        usage.animations = len(re.findall(
            r"\.(animate|fadeIn|fadeOut|slideUp|slideDown|show|hide|toggle)\s*\(",
            content
        ))

        # Detect plugins
        plugins = re.findall(r"\$\.[a-z]+\(|\$\.fn\.(\w+)", content.lower())
        usage.plugins = list(set(plugins))[:10]

        return usage if usage.selector_count > 0 else None

    async def _detect_legacy_patterns(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Detect legacy patterns across all frontend files"""
        logger.info("Detecting frontend legacy patterns...")

        all_patterns = {
            **{f"angularjs_{k}": {**v, "category": "angularjs"} for k, v in ANGULARJS_PATTERNS.items()},
            **{f"vue2_{k}": {**v, "category": "vue2"} for k, v in VUE2_PATTERNS.items()},
            **{f"react_{k}": {**v, "category": "react_class"} for k, v in REACT_CLASS_PATTERNS.items()},
            **{f"jquery_{k}": {**v, "category": "jquery"} for k, v in JQUERY_PATTERNS.items()},
        }

        extensions = [".js", ".jsx", ".ts", ".tsx", ".vue"]

        for ext in extensions:
            for file_path in repo_path.rglob(f"*{ext}"):
                if self._should_skip(file_path):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                # Count file types
                if ext == ".js":
                    self.result.total_js_files += 1
                elif ext == ".ts":
                    self.result.total_ts_files += 1

                for pattern_name, pattern_def in all_patterns.items():
                    matches = list(re.finditer(pattern_def["pattern"], content, re.IGNORECASE))

                    for match in matches[:3]:  # Limit per pattern per file
                        line_num = content[:match.start()].count('\n') + 1

                        # Create pattern match
                        pattern_match = FrontendPatternMatch(
                            pattern_name=pattern_name,
                            pattern_category=pattern_def["category"],
                            file_path=str(file_path.relative_to(repo_path)),
                            line_number=line_num,
                            code_snippet=match.group()[:100],
                            risk_level=pattern_def["risk"],
                            migration_note=pattern_def["note"],
                            migration_target=pattern_def["target"],
                            fp_multiplier=pattern_def.get("multiplier", 1.0),
                            is_security_issue=pattern_def.get("security", False),
                        )
                        self.result.legacy_patterns.append(pattern_match)

                        # Store in database
                        db_pattern = LegacyPattern(
                            analysis_id=analysis.id,
                            pattern_name=pattern_name,
                            pattern_category=pattern_def["category"],
                            file_path=str(file_path.relative_to(repo_path)),
                            line_number=line_num,
                            code_snippet=match.group()[:200],
                            risk_level=pattern_def["risk"],
                            fp_multiplier=pattern_def.get("multiplier", 1.0),
                            migration_note=pattern_def["note"],
                            migration_target=pattern_def["target"],
                            is_security_issue=pattern_def.get("security", False),
                        )
                        self.db.add(db_pattern)

        await self.db.commit()

    def _calculate_metrics(self) -> None:
        """Calculate overall metrics and determine primary framework"""
        # Total LOC
        self.result.total_loc = (
            sum(m.loc for m in self.result.angularjs_modules) +
            sum(c.loc for c in self.result.vue_components) +
            sum(c.loc for c in self.result.react_components) +
            sum(u.loc for u in self.result.jquery_usages)
        )

        # Determine primary framework
        framework_scores = {
            "angularjs": len(self.result.angularjs_modules) * 3,
            "vue2": len(self.result.vue_components) * 3,
            "react": len(self.result.react_components) * 3,
            "jquery": len(self.result.jquery_usages),
        }

        if any(framework_scores.values()):
            self.result.primary_framework = max(framework_scores.items(), key=lambda x: x[1])[0]

        # Migration difficulty
        critical_patterns = sum(1 for p in self.result.legacy_patterns if p.risk_level == "critical")
        high_patterns = sum(1 for p in self.result.legacy_patterns if p.risk_level == "high")
        security_issues = sum(1 for p in self.result.legacy_patterns if p.is_security_issue)

        if critical_patterns > 5 or security_issues > 10:
            self.result.migration_difficulty = "complex"
        elif high_patterns > 20 or critical_patterns > 0:
            self.result.migration_difficulty = "hard"
        elif high_patterns > 5:
            self.result.migration_difficulty = "medium"
        else:
            self.result.migration_difficulty = "easy"

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        return any(skip in file_path.parts for skip in self.SKIP_DIRS)

    def _assess_angularjs_difficulty(self, module: AngularJSModule) -> str:
        """Assess migration difficulty for AngularJS module"""
        score = module.scope_usages + len(module.directives) * 2
        if score > 20:
            return "complex"
        elif score > 10:
            return "hard"
        elif score > 5:
            return "medium"
        return "easy"

    def _assess_vue_difficulty(self, component: VueComponent) -> str:
        """Assess migration difficulty for Vue component"""
        if component.vuex_usage:
            return "medium"
        if len(component.lifecycle_hooks) > 3:
            return "medium"
        return "easy"

    def _assess_react_difficulty(self, component: ReactComponent) -> str:
        """Assess migration difficulty for React component"""
        if component.is_class and len(component.lifecycle_methods) > 2:
            return "medium"
        if component.redux_connected and component.is_class:
            return "hard"
        if component.is_class:
            return "medium"
        return "easy"


def get_frontend_analyzer_service(db: AsyncSession) -> FrontendAnalyzerService:
    """Factory function to create FrontendAnalyzerService instance"""
    return FrontendAnalyzerService(db)
