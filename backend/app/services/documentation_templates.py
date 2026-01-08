"""
Documentation Templates for Project Intake

Week 57: Standardized documentation templates for all projects.

These templates ensure:
1. Consistent structure across all projects
2. Clear sections for agents to consume
3. Easy customization per project type
4. Standard headers and navigation
"""

from typing import Dict, Any, List
from datetime import datetime


# ============================================================================
# TEMPLATE: README.md
# ============================================================================

README_TEMPLATE = """# {name} - Documentatie Index

**Project:** {name}
**Type:** {application_type}
**Status:** Geregistreerd in Platform
**Registratie Datum:** {registration_date}

---

## Snel Navigeren

| Document | Doel | Wanneer Lezen |
|----------|------|---------------|
| [PROJECT_GOAL.md](PROJECT_GOAL.md) | Waarom bestaat dit systeem? | Start hier voor context |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Hoe werkt het technisch? | Voor technische beslissingen |
| [PROJECT_INTAKE.md](PROJECT_INTAKE.md) | Stack detectie & analyse | Voor agent configuratie |

---

## Project Locatie

```
{root_path}/
├── doc/                    # <-- Je bent hier
│   ├── README.md           # Dit bestand (entry point)
│   ├── PROJECT_GOAL.md     # Business context & doelen
│   ├── ARCHITECTURE.md     # Technische architectuur
│   └── PROJECT_INTAKE.md   # Platform intake analyse
│
└── src/                    # Broncode
{component_tree}
```

---

## Voor Agents

### Context Laden
1. **Eerst**: Lees `PROJECT_GOAL.md` - begrijp het domein
2. **Dan**: Lees `ARCHITECTURE.md` - begrijp de techniek
3. **Optioneel**: `PROJECT_INTAKE.md` voor details

### Belangrijke Feiten

| Feit | Waarde |
|------|--------|
| **Primaire talen** | {primary_stacks} |
| **Componenten** | {component_count} |
| **Type** | {application_type} |

### Code Conventies

> **TODO:** Voeg project-specifieke code conventies toe.

---

## Kritieke Waarschuwingen

{warnings}

---

## Contact & Eigenaarschap

| Rol | Verantwoordelijkheid |
|-----|---------------------|
| **Beheerder** | TODO: Vul in |
| **Platform** | Multi-Stack AI Agent Platform |
| **Registratie** | {registration_date} |

---

*Dit document is het startpunt voor alle agents en developers die met {name} werken.*
"""


# ============================================================================
# TEMPLATE: PROJECT_GOAL.md
# ============================================================================

PROJECT_GOAL_TEMPLATE = """# {name} - Project Doelen & Context

**Status:** {goal_status}

---

## 1. Missie

{mission}

---

## 2. Domein

### Wat is het domein?

{domain_description}

### Gebruikers van het Systeem

| Gebruiker | Rol | Gebruik |
|-----------|-----|---------|
{user_table}

---

## 3. Kernfunctionaliteit

{core_functionality}

---

## 4. Wettelijke Context (indien van toepassing)

{legal_context}

---

## 5. Business Drivers

### Waarom Bestaat Dit Systeem?

{business_drivers}

### Key Performance Indicators

| KPI | Doel |
|-----|------|
{kpi_table}

---

## 6. Stakeholders

| Stakeholder | Belang | Prioriteit |
|-------------|--------|------------|
{stakeholder_table}

---

## 7. Strategische Richting

### Huidige Staat

{current_state}

### Gewenste Staat

{desired_state}

### Randvoorwaarden

{constraints}

---

## 8. Glossary

| Term | Betekenis |
|------|-----------|
{glossary_table}

---

*Dit document geeft agents de business context om zinvolle beslissingen te nemen.*
"""


# ============================================================================
# TEMPLATE: ARCHITECTURE.md
# ============================================================================

ARCHITECTURE_TEMPLATE = """# {name} - Technische Architectuur

**Generated:** {generation_date}
**Type:** {application_type}

---

## 1. Systeemoverzicht

```
{system_diagram}
```

---

## 2. Technology Stack

### Detected Technologies

| Stack | Beschrijving | Componenten |
|-------|--------------|-------------|
{stack_table}

### Frameworks & Libraries

{frameworks_section}

---

## 3. Component Architectuur

{component_details}

---

## 4. Data Architectuur

### Database Schema (indien van toepassing)

{database_section}

### Data Flow

{data_flow}

---

## 5. Integratie Architectuur

### Externe Systemen

{integration_table}

### Integratie Methodes

{integration_methods}

---

## 6. Security Architectuur

### Authenticatie & Autorisatie

{security_section}

### Privacy Maatregelen

{privacy_section}

---

## 7. Deployment Architectuur

{deployment_section}

---

## 8. Performance Karakteristieken

{performance_section}

---

## 9. Bekende Technische Schuld

| Issue | Impact | Prioriteit |
|-------|--------|------------|
{tech_debt_table}

---

*Dit document geeft agents de technische context voor code-gerelateerde beslissingen.*
"""


# ============================================================================
# TEMPLATE: PROJECT_INTAKE.md
# ============================================================================

PROJECT_INTAKE_TEMPLATE = """# {name} - Project Intake

**Generated:** {generation_date}
**Platform:** Multi-Stack AI Agent Platform
**Status:** Intake Complete

---

## 1. Project Overview

| Property | Value |
|----------|-------|
| **Project Name** | {name} |
| **Location** | {root_path} |
| **Project Type** | {application_type} |
| **Primary Stacks** | {primary_stacks} |
| **Components** | {component_count} |

---

## 2. Technology Stack Analysis

### Primary Technologies

| Stack | Files | Confidence | Components Using |
|-------|-------|------------|------------------|
{stack_analysis_table}

### Detected Frameworks

{frameworks_table}

---

## 3. Component Structure

| ID | Name | Type | Stacks | Agents |
|----|------|------|--------|--------|
{component_table}

---

## 4. Agents Created

| Agent | Role | Component | Stack | Model |
|-------|------|-----------|-------|-------|
{agent_table}

---

## 5. Dependencies

### Component Dependencies

{dependency_section}

### External Dependencies

{external_deps}

---

## 6. Quality Metrics (Baseline)

| Metric | Value | Status |
|--------|-------|--------|
{quality_metrics}

---

## 7. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
{risk_table}

---

## 8. Recommended Next Steps

{next_steps}

---

*Generated by Multi-Stack AI Agent Platform*
"""


# ============================================================================
# DEFAULT VALUES FOR TEMPLATES
# ============================================================================

DEFAULT_VALUES = {
    # README defaults
    "warnings": "> **Let op:** Voeg hier project-specifieke waarschuwingen toe.",

    # PROJECT_GOAL defaults
    "goal_status": "TEMPLATE - Vul aan met project-specifieke informatie",
    "mission": "> **TODO:** Beschrijf in 2-3 zinnen wat dit systeem doet en waarom het bestaat.",
    "domain_description": "> **TODO:** Beschrijf het vakgebied/domein waarin dit systeem opereert.",
    "user_table": "| **TODO** | | |",
    "core_functionality": "> **TODO:** Beschrijf de belangrijkste features van het systeem.",
    "legal_context": "> **TODO:** Beschrijf relevante wetgeving indien van toepassing (bijv. AVG, branche-specifiek).",
    "business_drivers": "1. **TODO**\n2. \n3. ",
    "kpi_table": "| **TODO** | |",
    "stakeholder_table": "| **TODO** | | |",
    "current_state": "> **TODO:** Beschrijf de huidige staat van het systeem.",
    "desired_state": "> **TODO:** Beschrijf de gewenste toekomstige staat.",
    "constraints": "> **TODO:** Beschrijf randvoorwaarden voor wijzigingen.",
    "glossary_table": "| **TODO** | |",

    # ARCHITECTURE defaults
    "database_section": "> **TODO:** Beschrijf database schema indien van toepassing.",
    "data_flow": "> **TODO:** Beschrijf data flow door het systeem.",
    "security_section": "> **TODO:** Beschrijf security architectuur.",
    "privacy_section": "> **TODO:** Beschrijf privacy maatregelen.",
    "deployment_section": "> **TODO:** Beschrijf deployment architectuur.",
    "performance_section": "> **TODO:** Beschrijf performance karakteristieken.",
    "tech_debt_table": "| **TODO** | | |",

    # INTAKE defaults
    "external_deps": "*Geen externe dependencies gedetecteerd.*",
    "quality_metrics": "| Code Coverage | TBD | Pending |\n| Complexity | TBD | Pending |",
    "risk_table": "| Legacy Code | TBD | TBD |",
    "next_steps": """1. **Complete PROJECT_GOAL.md** - Add business context
2. **Review ARCHITECTURE.md** - Verify auto-generated architecture
3. **Configure agents** - Adjust agent parameters if needed
4. **Run quality scan** - Baseline code quality
5. **Setup CI/CD** - Integrate with platform""",
}


# ============================================================================
# DOMAIN-SPECIFIC TEMPLATES
# ============================================================================

DOMAIN_TEMPLATES = {
    "healthcare": {
        "legal_context": """### Relevante Wetgeving

| Wet | Impact op Systeem |
|-----|-------------------|
| **AVG/GDPR** | Privacy, data minimalisatie, inzagerecht |
| **WGBO** | Dossierplicht, bewaartermijnen |
| **Wvggz** | Verplichte zorg (indien GGZ) |
| **NZa** | Declaratieregels, tarieven |

### Compliance Eisen

| Eis | Implementatie |
|-----|---------------|
| **Logging** | Alle toegang wordt gelogd |
| **Autorisatie** | Rolgebaseerde toegangscontrole |
| **Encryptie** | Data at rest en in transit |
| **Audit trail** | Wie wijzigde wat wanneer |""",

        "privacy_section": """### Privacy Maatregelen

| Maatregel | Implementatie |
|-----------|---------------|
| **Access Logging** | Elke data-view gelogd |
| **Data Minimization** | Alleen noodzakelijke data |
| **Encryption** | TLS + database encryptie |
| **Pseudonimization** | Export functies |
| **Retention** | Automatische opschoning |""",

        "warnings": """> **HEALTHCARE DATA** - Dit systeem bevat patientgegevens.
> - Strikte privacy regels van toepassing
> - Alle wijzigingen vereisen compliance review
> - Logging en audit trail verplicht""",
    },

    "finance": {
        "legal_context": """### Relevante Wetgeving

| Wet | Impact op Systeem |
|-----|-------------------|
| **AVG/GDPR** | Privacy, data minimalisatie |
| **Wwft** | Anti-witwas, KYC |
| **PSD2** | Betalingsdiensten |

### Compliance Eisen

| Eis | Implementatie |
|-----|---------------|
| **Audit trail** | Complete transactie logging |
| **Data retention** | Wettelijke bewaartermijnen |
| **Access control** | Strikte autorisatie |""",

        "warnings": """> **FINANCIELE DATA** - Dit systeem verwerkt financiele gegevens.
> - Strikte audit eisen van toepassing
> - Wijzigingen vereisen compliance review""",
    },

    "ecommerce": {
        "legal_context": """### Relevante Wetgeving

| Wet | Impact op Systeem |
|-----|-------------------|
| **AVG/GDPR** | Privacy, consent management |
| **Consumentenwet** | Herroepingsrecht, garantie |
| **PSD2** | Betalingsverwerking |""",
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_template(template_name: str) -> str:
    """Get a template by name."""
    templates = {
        "README": README_TEMPLATE,
        "PROJECT_GOAL": PROJECT_GOAL_TEMPLATE,
        "ARCHITECTURE": ARCHITECTURE_TEMPLATE,
        "PROJECT_INTAKE": PROJECT_INTAKE_TEMPLATE,
    }
    return templates.get(template_name, "")


def get_default(key: str) -> str:
    """Get a default value for a template placeholder."""
    return DEFAULT_VALUES.get(key, "")


def get_domain_overrides(domain: str) -> Dict[str, str]:
    """Get domain-specific template overrides."""
    return DOMAIN_TEMPLATES.get(domain, {})


def render_template(template: str, values: Dict[str, Any]) -> str:
    """
    Render a template with values.

    Missing values are replaced with defaults.
    """
    # Merge with defaults
    final_values = {**DEFAULT_VALUES, **values}

    # Simple string formatting
    try:
        return template.format(**final_values)
    except KeyError as e:
        # Return template with placeholder for missing key
        return template.replace(f"{{{e.args[0]}}}", f"[MISSING: {e.args[0]}]")


def detect_domain(stacks: List[str], frameworks: Dict[str, List[str]]) -> str:
    """
    Detect the likely domain based on stacks and frameworks.

    Returns: Domain name or 'general'
    """
    all_frameworks = []
    for fw_list in frameworks.values():
        all_frameworks.extend(fw_list)

    # Healthcare indicators
    healthcare_indicators = [
        "medmij", "zib", "fhir", "hl7", "healthcare", "patient",
        "koppeltaal", "zorgmail", "vecozo", "nza"
    ]
    if any(ind in str(all_frameworks).lower() for ind in healthcare_indicators):
        return "healthcare"

    # Finance indicators
    finance_indicators = [
        "payment", "stripe", "mollie", "ideal", "banking", "finance"
    ]
    if any(ind in str(all_frameworks).lower() for ind in finance_indicators):
        return "finance"

    # E-commerce indicators
    ecommerce_indicators = [
        "shopify", "woocommerce", "magento", "cart", "checkout"
    ]
    if any(ind in str(all_frameworks).lower() for ind in ecommerce_indicators):
        return "ecommerce"

    return "general"
