"""
UI Layer Extraction Service - Fase 26: Migration Execution

Week 140-141: Maps legacy UI components to modern equivalents.
Extracts design tokens, component patterns, and generates UI specs.

Agent: Vicky (Visual Designer)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4
import re
import logging

logger = logging.getLogger(__name__)


# ==================== Enums ====================

class UIFramework(Enum):
    """Target UI frameworks"""
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    BLAZOR = "blazor"
    NEXTJS = "nextjs"
    SVELTE = "svelte"


class LegacyUIType(Enum):
    """Legacy UI technology types"""
    ASP_WEBFORMS = "asp_webforms"
    ASP_MVC = "asp_mvc"
    WINFORMS = "winforms"
    WPF = "wpf"
    VB6_FORMS = "vb6_forms"
    CLASSIC_ASP = "classic_asp"


class ComponentType(Enum):
    """UI component types"""
    FORM = "form"
    GRID = "grid"
    TABLE = "table"
    MODAL = "modal"
    MENU = "menu"
    NAVIGATION = "navigation"
    INPUT = "input"
    BUTTON = "button"
    LIST = "list"
    CARD = "card"
    LAYOUT = "layout"
    CHART = "chart"
    CALENDAR = "calendar"
    TREE = "tree"
    TAB = "tab"
    ACCORDION = "accordion"
    DIALOG = "dialog"
    NOTIFICATION = "notification"
    BREADCRUMB = "breadcrumb"
    PAGINATION = "pagination"
    OTHER = "other"


class DesignTokenType(Enum):
    """Design token categories"""
    COLOR = "color"
    TYPOGRAPHY = "typography"
    SPACING = "spacing"
    BORDER = "border"
    SHADOW = "shadow"
    ANIMATION = "animation"
    BREAKPOINT = "breakpoint"
    Z_INDEX = "z_index"


# ==================== Data Classes ====================

@dataclass
class LegacyUIComponent:
    """Detected legacy UI component"""
    id: str
    name: str
    component_type: ComponentType
    legacy_type: LegacyUIType
    source_file: str
    source_lines: Tuple[int, int]
    html_elements: List[str]
    css_classes: List[str]
    event_handlers: List[str]
    data_bindings: List[str]
    child_components: List[str]
    parent_component: Optional[str]
    properties: Dict[str, Any] = field(default_factory=dict)
    styles: Dict[str, str] = field(default_factory=dict)


@dataclass
class ModernComponent:
    """Modern component equivalent"""
    name: str
    framework: UIFramework
    library: Optional[str]  # e.g., "Material UI", "Ant Design"
    import_statement: str
    component_template: str
    props_mapping: Dict[str, str]
    event_mapping: Dict[str, str]
    migration_notes: str = ""
    complexity: str = "low"  # low, medium, high


@dataclass
class DesignToken:
    """Design token definition"""
    name: str
    token_type: DesignTokenType
    value: str
    css_variable: str
    tailwind_class: Optional[str] = None
    description: str = ""
    source_styles: List[str] = field(default_factory=list)


@dataclass
class StyleExtraction:
    """Extracted styles from legacy code"""
    colors: List[DesignToken]
    typography: List[DesignToken]
    spacing: List[DesignToken]
    borders: List[DesignToken]
    shadows: List[DesignToken]
    raw_css_rules: List[str]


@dataclass
class ComponentMapping:
    """Mapping from legacy to modern component"""
    legacy: LegacyUIComponent
    modern_equivalents: Dict[UIFramework, List[ModernComponent]]
    design_tokens: List[DesignToken]
    migration_effort: str  # "trivial", "low", "medium", "high"
    estimated_hours: float
    notes: str = ""


@dataclass
class PageLayout:
    """Page-level layout extraction"""
    page_id: str
    page_name: str
    source_file: str
    layout_type: str  # "master-detail", "sidebar", "grid", "single-column"
    header_component: Optional[str]
    footer_component: Optional[str]
    navigation_component: Optional[str]
    main_components: List[str]
    responsive_breakpoints: List[str]


@dataclass
class UIExtractionResult:
    """Complete UI extraction result"""
    id: UUID
    project_path: str
    legacy_type: LegacyUIType
    scan_timestamp: datetime
    components: List[LegacyUIComponent]
    mappings: List[ComponentMapping]
    style_extraction: StyleExtraction
    pages: List[PageLayout]
    component_count: int
    unique_patterns: int


# ==================== Built-in Mappings ====================

COMPONENT_MAPPINGS: Dict[str, Dict[str, Any]] = {
    # ASP.NET WebForms to React/Vue mappings
    "asp:GridView": {
        "type": ComponentType.GRID,
        "react": [
            {"name": "DataGrid", "library": "@mui/x-data-grid", "complexity": "medium"},
            {"name": "Table", "library": "@tanstack/react-table", "complexity": "medium"},
        ],
        "vue": [
            {"name": "v-data-table", "library": "Vuetify", "complexity": "low"},
        ],
    },
    "asp:Button": {
        "type": ComponentType.BUTTON,
        "react": [
            {"name": "Button", "library": "@mui/material", "complexity": "low"},
            {"name": "button", "library": None, "complexity": "trivial"},
        ],
        "vue": [
            {"name": "v-btn", "library": "Vuetify", "complexity": "low"},
        ],
    },
    "asp:TextBox": {
        "type": ComponentType.INPUT,
        "react": [
            {"name": "TextField", "library": "@mui/material", "complexity": "low"},
            {"name": "input", "library": None, "complexity": "trivial"},
        ],
        "vue": [
            {"name": "v-text-field", "library": "Vuetify", "complexity": "low"},
        ],
    },
    "asp:DropDownList": {
        "type": ComponentType.INPUT,
        "react": [
            {"name": "Select", "library": "@mui/material", "complexity": "low"},
            {"name": "Autocomplete", "library": "@mui/material", "complexity": "medium"},
        ],
        "vue": [
            {"name": "v-select", "library": "Vuetify", "complexity": "low"},
        ],
    },
    "asp:Repeater": {
        "type": ComponentType.LIST,
        "react": [
            {"name": "List + map()", "library": "@mui/material", "complexity": "low"},
        ],
        "vue": [
            {"name": "v-for", "library": None, "complexity": "trivial"},
        ],
    },
    "asp:DataList": {
        "type": ComponentType.LIST,
        "react": [
            {"name": "List", "library": "@mui/material", "complexity": "low"},
        ],
        "vue": [
            {"name": "v-list", "library": "Vuetify", "complexity": "low"},
        ],
    },
    "asp:Panel": {
        "type": ComponentType.LAYOUT,
        "react": [
            {"name": "Box", "library": "@mui/material", "complexity": "trivial"},
            {"name": "div", "library": None, "complexity": "trivial"},
        ],
        "vue": [
            {"name": "div", "library": None, "complexity": "trivial"},
        ],
    },
    "asp:Menu": {
        "type": ComponentType.MENU,
        "react": [
            {"name": "Menu", "library": "@mui/material", "complexity": "medium"},
        ],
        "vue": [
            {"name": "v-menu", "library": "Vuetify", "complexity": "medium"},
        ],
    },
    "asp:TreeView": {
        "type": ComponentType.TREE,
        "react": [
            {"name": "TreeView", "library": "@mui/lab", "complexity": "medium"},
        ],
        "vue": [
            {"name": "v-treeview", "library": "Vuetify", "complexity": "medium"},
        ],
    },
    "asp:Calendar": {
        "type": ComponentType.CALENDAR,
        "react": [
            {"name": "DatePicker", "library": "@mui/x-date-pickers", "complexity": "medium"},
        ],
        "vue": [
            {"name": "v-date-picker", "library": "Vuetify", "complexity": "medium"},
        ],
    },
    "asp:ModalPopupExtender": {
        "type": ComponentType.MODAL,
        "react": [
            {"name": "Dialog", "library": "@mui/material", "complexity": "medium"},
            {"name": "Modal", "library": "@mui/material", "complexity": "low"},
        ],
        "vue": [
            {"name": "v-dialog", "library": "Vuetify", "complexity": "medium"},
        ],
    },
    "asp:TabContainer": {
        "type": ComponentType.TAB,
        "react": [
            {"name": "Tabs", "library": "@mui/material", "complexity": "medium"},
        ],
        "vue": [
            {"name": "v-tabs", "library": "Vuetify", "complexity": "medium"},
        ],
    },
    "asp:Wizard": {
        "type": ComponentType.FORM,
        "react": [
            {"name": "Stepper", "library": "@mui/material", "complexity": "high"},
        ],
        "vue": [
            {"name": "v-stepper", "library": "Vuetify", "complexity": "high"},
        ],
    },
    "asp:FormView": {
        "type": ComponentType.FORM,
        "react": [
            {"name": "Form + useForm", "library": "react-hook-form", "complexity": "medium"},
        ],
        "vue": [
            {"name": "v-form", "library": "Vuetify", "complexity": "medium"},
        ],
    },
    "asp:DetailsView": {
        "type": ComponentType.FORM,
        "react": [
            {"name": "Card + List", "library": "@mui/material", "complexity": "low"},
        ],
        "vue": [
            {"name": "v-card + v-list", "library": "Vuetify", "complexity": "low"},
        ],
    },
}


# ==================== Service ====================

class UILayerExtractionService:
    """
    Extracts and maps legacy UI components to modern frameworks.

    Features:
    - ASP.NET WebForms/MVC component detection
    - Design token extraction (colors, typography, spacing)
    - Component-to-component mapping
    - Page layout analysis
    - CSS extraction and conversion
    """

    def __init__(self):
        self.component_mappings = COMPONENT_MAPPINGS
        self.extraction_results: Dict[UUID, UIExtractionResult] = {}

    # ==================== Component Detection ====================

    async def extract_ui_components(
        self,
        project_path: str,
        legacy_type: LegacyUIType = LegacyUIType.ASP_WEBFORMS
    ) -> UIExtractionResult:
        """Extract UI components from legacy codebase."""
        import os

        result_id = uuid4()
        components: List[LegacyUIComponent] = []
        pages: List[PageLayout] = []

        # File extensions for different legacy types
        extensions = {
            LegacyUIType.ASP_WEBFORMS: [".aspx", ".ascx", ".master"],
            LegacyUIType.ASP_MVC: [".cshtml", ".vbhtml"],
            LegacyUIType.CLASSIC_ASP: [".asp"],
            LegacyUIType.WINFORMS: [".designer.cs", ".designer.vb"],
            LegacyUIType.WPF: [".xaml"],
        }

        target_extensions = extensions.get(legacy_type, [".aspx"])

        try:
            for root, _, files in os.walk(project_path):
                for filename in files:
                    if not any(filename.endswith(ext) for ext in target_extensions):
                        continue

                    file_path = os.path.join(root, filename)

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        # Extract components based on legacy type
                        if legacy_type in [LegacyUIType.ASP_WEBFORMS, LegacyUIType.ASP_MVC]:
                            file_components = await self._extract_aspnet_components(
                                content, file_path, legacy_type
                            )
                            components.extend(file_components)

                            # Extract page layout
                            page_layout = await self._extract_page_layout(
                                content, file_path, filename
                            )
                            if page_layout:
                                pages.append(page_layout)

                        elif legacy_type == LegacyUIType.WPF:
                            file_components = await self._extract_xaml_components(
                                content, file_path
                            )
                            components.extend(file_components)

                    except Exception as e:
                        logger.debug(f"Error processing {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error scanning UI: {e}")

        # Extract styles
        style_extraction = await self.extract_design_tokens(project_path)

        # Generate mappings
        mappings = await self.generate_component_mappings(components)

        # Count unique patterns
        unique_patterns = len(set(c.component_type for c in components))

        result = UIExtractionResult(
            id=result_id,
            project_path=project_path,
            legacy_type=legacy_type,
            scan_timestamp=datetime.now(),
            components=components,
            mappings=mappings,
            style_extraction=style_extraction,
            pages=pages,
            component_count=len(components),
            unique_patterns=unique_patterns,
        )

        self.extraction_results[result_id] = result
        logger.info(f"Extracted {len(components)} UI components, {len(pages)} pages")

        return result

    async def _extract_aspnet_components(
        self,
        content: str,
        file_path: str,
        legacy_type: LegacyUIType
    ) -> List[LegacyUIComponent]:
        """Extract ASP.NET WebForms/MVC components."""
        components = []
        component_id = 0

        # ASP.NET control patterns
        asp_pattern = r'<(asp:\w+)\s+([^>]*)/?>'
        ajax_pattern = r'<(ajax:\w+)\s+([^>]*)/?>'

        for pattern in [asp_pattern, ajax_pattern]:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                tag_name = match.group(1)
                attributes_str = match.group(2)

                # Parse attributes
                attributes = {}
                for attr_match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', attributes_str):
                    attributes[attr_match.group(1).lower()] = attr_match.group(2)

                # Determine component type
                comp_type = self._determine_component_type(tag_name)

                # Extract event handlers
                event_handlers = [
                    attr for attr in attributes
                    if attr.startswith("on") or "click" in attr.lower()
                ]

                # Extract data bindings
                data_bindings = [
                    f"{k}={v}" for k, v in attributes.items()
                    if "<%#" in v or "Bind(" in v or "Eval(" in v
                ]

                component_id += 1
                components.append(LegacyUIComponent(
                    id=f"ui-{component_id:04d}",
                    name=attributes.get("id", tag_name),
                    component_type=comp_type,
                    legacy_type=legacy_type,
                    source_file=file_path,
                    source_lines=(match.start(), match.end()),
                    html_elements=[tag_name],
                    css_classes=attributes.get("cssclass", "").split(),
                    event_handlers=event_handlers,
                    data_bindings=data_bindings,
                    child_components=[],
                    parent_component=None,
                    properties=attributes,
                ))

        # Also extract HTML5 elements with runat="server"
        runat_pattern = r'<(\w+)\s+[^>]*runat\s*=\s*["\']server["\'][^>]*>'
        for match in re.finditer(runat_pattern, content, re.IGNORECASE):
            tag_name = match.group(1)
            if tag_name.lower() not in ['asp', 'ajax']:
                component_id += 1
                components.append(LegacyUIComponent(
                    id=f"ui-{component_id:04d}",
                    name=f"ServerControl-{tag_name}",
                    component_type=ComponentType.OTHER,
                    legacy_type=legacy_type,
                    source_file=file_path,
                    source_lines=(match.start(), match.end()),
                    html_elements=[tag_name],
                    css_classes=[],
                    event_handlers=[],
                    data_bindings=[],
                    child_components=[],
                    parent_component=None,
                ))

        return components

    async def _extract_xaml_components(
        self,
        content: str,
        file_path: str
    ) -> List[LegacyUIComponent]:
        """Extract WPF XAML components."""
        components = []
        component_id = 0

        # Common WPF controls
        wpf_controls = [
            "Button", "TextBox", "Label", "ComboBox", "ListBox", "DataGrid",
            "TreeView", "TabControl", "Menu", "ToolBar", "StatusBar",
            "CheckBox", "RadioButton", "Slider", "ProgressBar", "Calendar",
            "DatePicker", "Expander", "GroupBox", "ScrollViewer", "Grid",
            "StackPanel", "WrapPanel", "DockPanel", "Canvas", "Border"
        ]

        for control in wpf_controls:
            pattern = rf'<{control}\s+([^>]*)/?>'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                attributes_str = match.group(1)

                # Parse attributes
                attributes = {}
                for attr_match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', attributes_str):
                    attributes[attr_match.group(1).lower()] = attr_match.group(2)

                comp_type = self._determine_component_type(control)

                component_id += 1
                components.append(LegacyUIComponent(
                    id=f"ui-{component_id:04d}",
                    name=attributes.get("x:name", attributes.get("name", control)),
                    component_type=comp_type,
                    legacy_type=LegacyUIType.WPF,
                    source_file=file_path,
                    source_lines=(match.start(), match.end()),
                    html_elements=[control],
                    css_classes=[],
                    event_handlers=[k for k in attributes if k.startswith("on")],
                    data_bindings=[f"{k}={v}" for k, v in attributes.items() if "{Binding" in v],
                    child_components=[],
                    parent_component=None,
                    properties=attributes,
                ))

        return components

    def _determine_component_type(self, tag_name: str) -> ComponentType:
        """Determine component type from tag name."""
        tag_lower = tag_name.lower()

        type_mappings = {
            "gridview": ComponentType.GRID,
            "datagrid": ComponentType.GRID,
            "repeater": ComponentType.LIST,
            "datalist": ComponentType.LIST,
            "listview": ComponentType.LIST,
            "listbox": ComponentType.LIST,
            "button": ComponentType.BUTTON,
            "linkbutton": ComponentType.BUTTON,
            "imagebutton": ComponentType.BUTTON,
            "textbox": ComponentType.INPUT,
            "dropdownlist": ComponentType.INPUT,
            "combobox": ComponentType.INPUT,
            "checkbox": ComponentType.INPUT,
            "radiobutton": ComponentType.INPUT,
            "menu": ComponentType.MENU,
            "treeview": ComponentType.TREE,
            "calendar": ComponentType.CALENDAR,
            "datepicker": ComponentType.CALENDAR,
            "modal": ComponentType.MODAL,
            "panel": ComponentType.LAYOUT,
            "placeholder": ComponentType.LAYOUT,
            "contentplaceholder": ComponentType.LAYOUT,
            "tab": ComponentType.TAB,
            "tabcontainer": ComponentType.TAB,
            "tabcontrol": ComponentType.TAB,
            "wizard": ComponentType.FORM,
            "formview": ComponentType.FORM,
            "detailsview": ComponentType.FORM,
            "table": ComponentType.TABLE,
            "chart": ComponentType.CHART,
        }

        for key, comp_type in type_mappings.items():
            if key in tag_lower:
                return comp_type

        return ComponentType.OTHER

    async def _extract_page_layout(
        self,
        content: str,
        file_path: str,
        filename: str
    ) -> Optional[PageLayout]:
        """Extract page-level layout information."""
        # Check for master page reference
        master_match = re.search(r'MasterPageFile\s*=\s*["\']([^"\']+)["\']', content)

        # Check for layout components
        header = None
        footer = None
        nav = None

        # Common patterns
        if re.search(r'<(asp:)?Header|id=["\']header["\']', content, re.IGNORECASE):
            header = "header"
        if re.search(r'<(asp:)?Footer|id=["\']footer["\']', content, re.IGNORECASE):
            footer = "footer"
        if re.search(r'<(asp:)?Menu|<nav|id=["\']nav', content, re.IGNORECASE):
            nav = "navigation"

        # Determine layout type
        layout_type = "single-column"
        if re.search(r'sidebar|aside|left-panel|right-panel', content, re.IGNORECASE):
            layout_type = "sidebar"
        elif re.search(r'master.*detail|list.*detail', content, re.IGNORECASE):
            layout_type = "master-detail"
        elif re.search(r'grid-container|row.*col', content, re.IGNORECASE):
            layout_type = "grid"

        return PageLayout(
            page_id=filename.replace(".", "_"),
            page_name=filename,
            source_file=file_path,
            layout_type=layout_type,
            header_component=header,
            footer_component=footer,
            navigation_component=nav,
            main_components=[],
            responsive_breakpoints=[],
        )

    # ==================== Design Token Extraction ====================

    async def extract_design_tokens(
        self,
        project_path: str
    ) -> StyleExtraction:
        """Extract design tokens from CSS and inline styles."""
        import os

        colors = []
        typography = []
        spacing = []
        borders = []
        shadows = []
        raw_css = []

        # Find CSS files
        css_extensions = [".css", ".less", ".scss", ".sass"]

        try:
            for root, _, files in os.walk(project_path):
                for filename in files:
                    if not any(filename.endswith(ext) for ext in css_extensions):
                        continue

                    file_path = os.path.join(root, filename)

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            css_content = f.read()

                        raw_css.append(f"/* {filename} */")
                        raw_css.append(css_content[:1000])  # First 1000 chars

                        # Extract colors
                        color_patterns = [
                            (r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b', 'hex'),
                            (r'rgb\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)', 'rgb'),
                            (r'rgba\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)', 'rgba'),
                        ]

                        for pattern, color_type in color_patterns:
                            for match in re.finditer(pattern, css_content):
                                color_value = match.group(0)
                                token_name = f"color-{len(colors)+1}"
                                colors.append(DesignToken(
                                    name=token_name,
                                    token_type=DesignTokenType.COLOR,
                                    value=color_value,
                                    css_variable=f"--{token_name}",
                                    source_styles=[file_path],
                                ))

                        # Extract font families
                        font_pattern = r'font-family\s*:\s*([^;]+);'
                        for match in re.finditer(font_pattern, css_content):
                            font_value = match.group(1).strip()
                            token_name = f"font-family-{len(typography)+1}"
                            typography.append(DesignToken(
                                name=token_name,
                                token_type=DesignTokenType.TYPOGRAPHY,
                                value=font_value,
                                css_variable=f"--{token_name}",
                                source_styles=[file_path],
                            ))

                        # Extract spacing values
                        spacing_pattern = r'(?:margin|padding)\s*:\s*([^;]+);'
                        for match in re.finditer(spacing_pattern, css_content):
                            spacing_value = match.group(1).strip()
                            token_name = f"spacing-{len(spacing)+1}"
                            spacing.append(DesignToken(
                                name=token_name,
                                token_type=DesignTokenType.SPACING,
                                value=spacing_value,
                                css_variable=f"--{token_name}",
                                source_styles=[file_path],
                            ))

                        # Extract border styles
                        border_pattern = r'border\s*:\s*([^;]+);'
                        for match in re.finditer(border_pattern, css_content):
                            border_value = match.group(1).strip()
                            token_name = f"border-{len(borders)+1}"
                            borders.append(DesignToken(
                                name=token_name,
                                token_type=DesignTokenType.BORDER,
                                value=border_value,
                                css_variable=f"--{token_name}",
                                source_styles=[file_path],
                            ))

                        # Extract box shadows
                        shadow_pattern = r'box-shadow\s*:\s*([^;]+);'
                        for match in re.finditer(shadow_pattern, css_content):
                            shadow_value = match.group(1).strip()
                            token_name = f"shadow-{len(shadows)+1}"
                            shadows.append(DesignToken(
                                name=token_name,
                                token_type=DesignTokenType.SHADOW,
                                value=shadow_value,
                                css_variable=f"--{token_name}",
                                source_styles=[file_path],
                            ))

                    except Exception as e:
                        logger.debug(f"Error processing CSS {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error extracting design tokens: {e}")

        # Deduplicate tokens
        colors = self._deduplicate_tokens(colors)
        typography = self._deduplicate_tokens(typography)
        spacing = self._deduplicate_tokens(spacing)
        borders = self._deduplicate_tokens(borders)
        shadows = self._deduplicate_tokens(shadows)

        return StyleExtraction(
            colors=colors,
            typography=typography,
            spacing=spacing,
            borders=borders,
            shadows=shadows,
            raw_css_rules=raw_css,
        )

    def _deduplicate_tokens(self, tokens: List[DesignToken]) -> List[DesignToken]:
        """Remove duplicate tokens based on value."""
        seen_values = set()
        unique = []

        for token in tokens:
            if token.value not in seen_values:
                seen_values.add(token.value)
                unique.append(token)

        return unique

    # ==================== Component Mapping ====================

    async def generate_component_mappings(
        self,
        components: List[LegacyUIComponent],
        target_frameworks: Optional[List[UIFramework]] = None
    ) -> List[ComponentMapping]:
        """Generate mappings from legacy to modern components."""
        if target_frameworks is None:
            target_frameworks = [UIFramework.REACT, UIFramework.VUE]

        mappings = []

        for component in components:
            modern_equivalents: Dict[UIFramework, List[ModernComponent]] = {}

            # Look up in component mappings
            for tag in component.html_elements:
                mapping_key = tag if tag in self.component_mappings else None

                # Try partial match
                if not mapping_key:
                    for key in self.component_mappings:
                        if key.lower() in tag.lower():
                            mapping_key = key
                            break

                if mapping_key:
                    mapping_data = self.component_mappings[mapping_key]

                    for framework in target_frameworks:
                        framework_key = framework.value.lower()
                        if framework_key in mapping_data:
                            modern_equivalents[framework] = []

                            for eq in mapping_data[framework_key]:
                                modern_comp = ModernComponent(
                                    name=eq["name"],
                                    framework=framework,
                                    library=eq.get("library"),
                                    import_statement=self._generate_import(eq["name"], eq.get("library")),
                                    component_template=self._generate_template(eq["name"], component),
                                    props_mapping=self._generate_props_mapping(component, eq["name"]),
                                    event_mapping=self._generate_event_mapping(component, framework),
                                    complexity=eq.get("complexity", "low"),
                                )
                                modern_equivalents[framework].append(modern_comp)

            # Calculate migration effort
            effort = self._calculate_effort(component, modern_equivalents)

            mappings.append(ComponentMapping(
                legacy=component,
                modern_equivalents=modern_equivalents,
                design_tokens=[],
                migration_effort=effort,
                estimated_hours=self._estimate_hours(effort, component),
            ))

        return mappings

    def _generate_import(self, component_name: str, library: Optional[str]) -> str:
        """Generate import statement."""
        if library:
            return f"import {{ {component_name} }} from '{library}';"
        return ""

    def _generate_template(self, component_name: str, legacy: LegacyUIComponent) -> str:
        """Generate component template."""
        props = []
        if legacy.properties.get("id"):
            props.append(f'id="{legacy.properties["id"]}"')
        if legacy.css_classes:
            props.append(f'className="{" ".join(legacy.css_classes)}"')

        props_str = " ".join(props)
        return f"<{component_name} {props_str} />"

    def _generate_props_mapping(
        self,
        legacy: LegacyUIComponent,
        modern_name: str
    ) -> Dict[str, str]:
        """Map legacy properties to modern props."""
        mapping = {}

        common_mappings = {
            "text": "label",
            "cssclass": "className",
            "onclick": "onClick",
            "onchange": "onChange",
            "visible": "visible",
            "enabled": "disabled",  # Inverted
            "datasource": "data",
            "datavaluefield": "valueField",
            "datatextfield": "labelField",
        }

        for legacy_prop, value in legacy.properties.items():
            modern_prop = common_mappings.get(legacy_prop.lower(), legacy_prop)
            mapping[legacy_prop] = modern_prop

        return mapping

    def _generate_event_mapping(
        self,
        legacy: LegacyUIComponent,
        framework: UIFramework
    ) -> Dict[str, str]:
        """Map legacy events to modern framework events."""
        mapping = {}

        event_mappings = {
            UIFramework.REACT: {
                "onclick": "onClick",
                "onchange": "onChange",
                "onblur": "onBlur",
                "onfocus": "onFocus",
                "onsubmit": "onSubmit",
                "onload": "useEffect",
            },
            UIFramework.VUE: {
                "onclick": "@click",
                "onchange": "@change",
                "onblur": "@blur",
                "onfocus": "@focus",
                "onsubmit": "@submit",
                "onload": "mounted",
            },
        }

        framework_events = event_mappings.get(framework, {})

        for handler in legacy.event_handlers:
            handler_lower = handler.lower()
            if handler_lower in framework_events:
                mapping[handler] = framework_events[handler_lower]

        return mapping

    def _calculate_effort(
        self,
        legacy: LegacyUIComponent,
        modern_equivalents: Dict[UIFramework, List[ModernComponent]]
    ) -> str:
        """Calculate migration effort level."""
        if not modern_equivalents:
            return "high"

        # Check for complex components
        if legacy.component_type in [ComponentType.GRID, ComponentType.CHART, ComponentType.CALENDAR]:
            return "medium"

        if len(legacy.data_bindings) > 3:
            return "medium"

        if len(legacy.event_handlers) > 3:
            return "medium"

        return "low"

    def _estimate_hours(self, effort: str, component: LegacyUIComponent) -> float:
        """Estimate migration hours."""
        base_hours = {
            "trivial": 0.5,
            "low": 2,
            "medium": 8,
            "high": 24,
        }

        hours = base_hours.get(effort, 4)

        # Adjust for complexity
        if len(component.data_bindings) > 5:
            hours *= 1.5
        if len(component.event_handlers) > 5:
            hours *= 1.25

        return round(hours, 1)

    # ==================== Export ====================

    def to_design_tokens_json(self, extraction: StyleExtraction) -> Dict[str, Any]:
        """Export design tokens as JSON."""
        return {
            "colors": {
                t.name: {"value": t.value, "cssVariable": t.css_variable}
                for t in extraction.colors
            },
            "typography": {
                t.name: {"value": t.value, "cssVariable": t.css_variable}
                for t in extraction.typography
            },
            "spacing": {
                t.name: {"value": t.value, "cssVariable": t.css_variable}
                for t in extraction.spacing
            },
            "borders": {
                t.name: {"value": t.value, "cssVariable": t.css_variable}
                for t in extraction.borders
            },
            "shadows": {
                t.name: {"value": t.value, "cssVariable": t.css_variable}
                for t in extraction.shadows
            },
        }

    def to_css_variables(self, extraction: StyleExtraction) -> str:
        """Generate CSS variables file."""
        lines = [":root {"]

        all_tokens = (
            extraction.colors + extraction.typography +
            extraction.spacing + extraction.borders + extraction.shadows
        )

        for token in all_tokens:
            lines.append(f"  {token.css_variable}: {token.value};")

        lines.append("}")
        return "\n".join(lines)

    def to_markdown_report(self, result: UIExtractionResult) -> str:
        """Generate markdown UI migration report."""
        lines = [
            f"# UI Layer Extraction Report",
            f"",
            f"**Project:** {result.project_path}",
            f"**Legacy Type:** {result.legacy_type.value}",
            f"**Scanned:** {result.scan_timestamp.isoformat()}",
            f"**Components Found:** {result.component_count}",
            f"**Unique Patterns:** {result.unique_patterns}",
            f"",
            f"## Component Summary",
            f"",
            f"| Type | Count |",
            f"|------|-------|",
        ]

        # Count by type
        type_counts: Dict[str, int] = {}
        for comp in result.components:
            type_name = comp.component_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        for type_name, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {type_name} | {count} |")

        # Component mappings
        lines.extend([
            f"",
            f"## Component Mappings",
            f"",
            f"| Legacy Component | Type | React Equivalent | Effort | Hours |",
            f"|------------------|------|------------------|--------|-------|",
        ])

        for mapping in result.mappings[:50]:  # First 50
            react_equiv = "Custom"
            if UIFramework.REACT in mapping.modern_equivalents and mapping.modern_equivalents[UIFramework.REACT]:
                react_equiv = mapping.modern_equivalents[UIFramework.REACT][0].name

            lines.append(
                f"| {mapping.legacy.name} | {mapping.legacy.component_type.value} | "
                f"{react_equiv} | {mapping.migration_effort} | {mapping.estimated_hours}h |"
            )

        # Design tokens
        lines.extend([
            f"",
            f"## Design Tokens",
            f"",
            f"### Colors ({len(result.style_extraction.colors)})",
            f"",
        ])

        for token in result.style_extraction.colors[:10]:
            lines.append(f"- `{token.css_variable}`: `{token.value}`")

        lines.extend([
            f"",
            f"### Typography ({len(result.style_extraction.typography)})",
            f"",
        ])

        for token in result.style_extraction.typography[:5]:
            lines.append(f"- `{token.css_variable}`: `{token.value}`")

        # Pages
        if result.pages:
            lines.extend([
                f"",
                f"## Page Layouts ({len(result.pages)})",
                f"",
                f"| Page | Layout Type | Header | Footer | Nav |",
                f"|------|-------------|--------|--------|-----|",
            ])

            for page in result.pages:
                lines.append(
                    f"| {page.page_name} | {page.layout_type} | "
                    f"{'✓' if page.header_component else '-'} | "
                    f"{'✓' if page.footer_component else '-'} | "
                    f"{'✓' if page.navigation_component else '-'} |"
                )

        return "\n".join(lines)
