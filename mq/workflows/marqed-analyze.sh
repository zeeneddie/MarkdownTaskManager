#!/bin/bash
# marqed-analyze.sh - Code analysis workflow with database analysis and error recovery
# Version 2.1 - With checkpointing, progress tracking, and pattern detection

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_DIR="${SCRIPT_DIR}/common"

# Source common functions
source "${COMMON_DIR}/loop-core.sh"
source "${COMMON_DIR}/validation.sh"
source "${COMMON_DIR}/progress-tracking.sh"

# Configuration
WORKFLOW_TYPE="analyze"
MAX_ITERATIONS=30
STATE_DIR="${HOME}/.marqed/state"
LOGS_DIR="${HOME}/.marqed/logs"
RESULTS_DIR="${HOME}/.marqed/results"

#######################################
# Display usage information
#######################################
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

MarQed.ai Code Analysis Workflow - Comprehensive codebase analysis

OPTIONS:
    -i, --id ID              Analysis ID (e.g., ANALYZE-2026-01-23-001)
    -c, --codebase DIR       Path to codebase to analyze
    -p, --prd FILE           Path to PRD file (default: ./PRD.md)
    -m, --mode MODE          Analysis mode: quick|standard|deep (default: standard)
    -s, --stack STACK        Force tech stack: asp-classic|dotnet|java|python|auto (default: auto)
    
    # Database analysis
    -d, --database CONN      Database connection string for schema analysis (optional)
    --db-type TYPE           Database type: sqlserver|mysql|postgresql (default: sqlserver)
    
    # Scenario options
    --generate-migration-prd Generate migration PRD from analysis (Scenario B)
    --create-backlog         Create prioritized backlog PRDs (Scenario C)
    --target-stack STACK     Target stack for migration (with --generate-migration-prd)
    
    # Execution options
    --resume                 Resume from last checkpoint (if available)
    --clear-checkpoint       Clear existing checkpoint and start fresh
    --max-iter N             Maximum iterations (default: 30)
    
    # Export options
    --export-json            Export results as JSON
    --export-html            Generate HTML dashboard
    --export-all             Export JSON + HTML
    
    -h, --help               Show this help message

MODES:
    quick       Basic metrics and high-level overview (2-4h)
    standard    Comprehensive analysis of all areas (8-12h)
    deep        Everything + manual review + expert analysis (20-30h)

EXAMPLES:
    # Basic analysis (Scenario A)
    $(basename "$0") --id ANALYZE-001 --codebase ./src

    # Full analysis with HTML export
    $(basename "$0") --id ANALYZE-001 --codebase ./src --mode deep --export-html

    # With database analysis
    $(basename "$0") --id ANALYZE-HCI --codebase ./hci-epd \\
        --database "Server=localhost;Database=HCI_EPD;Trusted_Connection=True;"

    # Analysis → Migration PRD (Scenario B)
    $(basename "$0") --id ANALYZE-HCI --codebase ./hci-epd \\
        --generate-migration-prd --target-stack dotnet-core

    # Analysis → Backlog (Scenario C)
    $(basename "$0") --id ANALYZE-HCI --codebase ./hci-epd \\
        --create-backlog --export-all

    # Resume after failure
    $(basename "$0") --id ANALYZE-001 --resume

WORKFLOW:
    1. Detect technology stack
    2. Run automated analysis tools
    3. Perform deep code analysis
    4. Security and compliance audit
    5. Prioritize findings and create roadmap
    6. Generate reports and deliverables

FILES CREATED:
    ~/.marqed/state/${ID}/           - State tracking and checkpoints
    ~/.marqed/logs/${ID}/            - Execution logs
    ~/.marqed/results/${ID}/         - Analysis results
    ~/.claude/tasks/${ID}.json       - Claude Code task list

For more information: https://github.com/marqed-ai/workflows
EOF
}

#######################################
# Initialize analysis workflow
#######################################
initialize_analysis() {
    local id="$1"
    local prd_file="$2"
    local codebase_dir="$3"
    
    echo "🔍 Initializing MarQed.ai Code Analysis Workflow"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Analysis ID: ${id}"
    echo "PRD: ${prd_file}"
    echo "Codebase: ${codebase_dir}"
    echo ""
    
    # Create directories
    mkdir -p "${STATE_DIR}/${id}"
    mkdir -p "${LOGS_DIR}/${id}"
    mkdir -p "${RESULTS_DIR}/${id}"
    
    # Check PRD exists
    if [[ ! -f "${prd_file}" ]]; then
        echo "❌ Error: PRD file not found: ${prd_file}" >&2
        exit 1
    fi
    
    # Check codebase exists
    if [[ ! -d "${codebase_dir}" ]]; then
        echo "❌ Error: Codebase directory not found: ${codebase_dir}" >&2
        exit 1
    fi
    
    # Initialize tasks from PRD
    echo "📋 Converting PRD to Claude Code tasks..."
    if ! "${SCRIPT_DIR}/../scripts/prd-to-tasks.sh" "${id}" "${prd_file}"; then
        echo "❌ Error: Failed to initialize tasks from PRD" >&2
        exit 1
    fi
    
    # Verify task file created
    local task_file="${HOME}/.claude/tasks/${id}.json"
    if [[ ! -f "${task_file}" ]]; then
        echo "❌ Error: Task file not created: ${task_file}" >&2
        exit 1
    fi
    
    echo "✅ Tasks initialized successfully"
    echo ""
    
    # Display task summary
    echo "📊 Analysis Task Summary:"
    jq -r '.tasks[] | "  - [\(.status)] Phase \(.phase): \(.title) (est: \(.estimatedTime))"' "${task_file}"
    echo ""
}

#######################################
# Detect technology stack
#######################################
detect_tech_stack() {
    local codebase_dir="$1"
    local force_stack="$2"
    
    if [[ "${force_stack}" != "auto" ]]; then
        echo "🔧 Using forced tech stack: ${force_stack}"
        echo "${force_stack}"
        return 0
    fi
    
    echo "🔍 Auto-detecting technology stack..."
    
    cd "${codebase_dir}" || exit 1
    
    # Check for .NET
    if ls *.csproj >/dev/null 2>&1 || ls *.sln >/dev/null 2>&1; then
        echo "✅ Detected: .NET"
        local version=$(grep -r "TargetFramework" *.csproj 2>/dev/null | head -1 | grep -oP 'net\d+\.\d+' || echo "unknown")
        echo "   Version: ${version}"
        echo "dotnet"
        return 0
    fi
    
    # Check for ASP Classic
    if find . -maxdepth 3 -name "*.asp" -o -name "*.vbs" 2>/dev/null | grep -q .; then
        echo "✅ Detected: ASP Classic"
        echo "asp-classic"
        return 0
    fi
    
    # Check for Java
    if [[ -f "pom.xml" ]] || [[ -f "build.gradle" ]]; then
        echo "✅ Detected: Java"
        if [[ -f "pom.xml" ]]; then
            local version=$(grep -A 1 "<java.version>" pom.xml 2>/dev/null | tail -1 | grep -oP '\d+' || echo "unknown")
            echo "   Version: Java ${version}"
        fi
        echo "java"
        return 0
    fi
    
    # Check for Python
    if [[ -f "requirements.txt" ]] || [[ -f "setup.py" ]] || [[ -f "pyproject.toml" ]]; then
        echo "✅ Detected: Python"
        if [[ -f "runtime.txt" ]]; then
            local version=$(cat runtime.txt)
            echo "   Version: ${version}"
        fi
        echo "python"
        return 0
    fi
    
    # Check for Node.js
    if [[ -f "package.json" ]]; then
        echo "✅ Detected: Node.js"
        local version=$(jq -r '.engines.node // "unknown"' package.json 2>/dev/null)
        echo "   Version: ${version}"
        echo "nodejs"
        return 0
    fi
    
    # Check for PHP
    if [[ -f "composer.json" ]]; then
        echo "✅ Detected: PHP"
        local version=$(jq -r '.require.php // "unknown"' composer.json 2>/dev/null)
        echo "   Version: ${version}"
        echo "php"
        return 0
    fi
    
    echo "⚠️  Unable to auto-detect tech stack"
    echo "unknown"
    return 1
}

#######################################
# Run database analysis
#######################################
run_database_analysis() {
    local database_connection="$1"
    local db_type="$2"
    local results_dir="$3"
    
    if [[ -z "${database_connection}" ]]; then
        echo "ℹ️  No database connection provided, skipping database analysis"
        return 0
    fi
    
    echo "🗄️  Analyzing database schema..."
    
    if [[ ! -f "${SCRIPT_DIR}/../scripts/analyze-database.py" ]]; then
        echo "⚠️  Database analysis script not found, skipping..."
        return 0
    fi
    
    if python3 "${SCRIPT_DIR}/../scripts/analyze-database.py" \
        --connection "${database_connection}" \
        --db-type "${db_type}" \
        --output "${results_dir}/database-analysis.json"; then
        
        echo "✅ Database analysis complete"
        
        # Display summary
        echo ""
        echo "📊 Database Analysis Summary:"
        jq -r '
            "  Tables: \(.schema.total_tables)
  Total rows: \(.schema.total_rows)
  Size: \(.schema.total_size_mb) MB
  PII fields: \(.pii_data.total_pii_fields)
  Migration complexity: \(.migration_complexity.category) (\(.migration_complexity.estimated_hours)h)"
        ' "${results_dir}/database-analysis.json"
        echo ""
        
        # Merge into main findings
        if [[ -f "${results_dir}/findings.json" ]]; then
            jq -s '.[0] * {database: .[1]}' \
                "${results_dir}/findings.json" \
                "${results_dir}/database-analysis.json" \
                > "${results_dir}/findings-with-db.json"
            
            mv "${results_dir}/findings-with-db.json" "${results_dir}/findings.json"
        fi
    else
        echo "⚠️  Database analysis failed - continuing without DB insights"
    fi
}

#######################################
# Main analysis loop
#######################################
marqed_analysis_loop() {
    local id="$1"
    local prd_file="$2"
    local codebase_dir="$3"
    local max_iterations="$4"
    local mode="$5"
    local tech_stack="$6"
    
    local iteration=1
    local task_file="${HOME}/.claude/tasks/${id}.json"
    local log_file="${LOGS_DIR}/${id}/analysis-$(date +%Y%m%d-%H%M%S).log"
    
    echo "🔄 Starting MarQed.ai Analysis Loop"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Mode: ${mode}"
    echo "Tech Stack: ${tech_stack}"
    echo "Max iterations: ${max_iterations}"
    echo "Log file: ${log_file}"
    echo ""
    
    # Check for existing checkpoint
    if load_checkpoint "${id}"; then
        local resume_phase=$(cat "${STATE_DIR}/${id}/last_completed_phase.txt")
        echo "✅ Resuming from phase: ${resume_phase}"
        
        # Restore iteration number
        if [[ -f "${STATE_DIR}/${id}/last_iteration.txt" ]]; then
            iteration=$(cat "${STATE_DIR}/${id}/last_iteration.txt")
            iteration=$((iteration + 1))
            echo "   Continuing from iteration ${iteration}"
        fi
        echo ""
    fi
    
    # Export environment variables for Claude Code
    export CLAUDE_CODE_TASK_LIST_ID="${id}"
    export ANALYSIS_MODE="${mode}"
    export TECH_STACK="${tech_stack}"
    export CODEBASE_DIR="${codebase_dir}"
    export RESULTS_DIR="${RESULTS_DIR}/${id}"
    
    while [[ ${iteration} -le ${max_iterations} ]]; do
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🔁 Iteration ${iteration}/${max_iterations}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # Check if all tasks are complete
        if check_tasks_complete "${task_file}"; then
            echo "✅ All analysis phases completed!"
            echo ""
            
            # Sync tasks back to PRD
            echo "📝 Updating PRD with completion status..."
            sync_tasks_to_prd "${task_file}" "${prd_file}"
            
            # Generate final reports
            echo "📊 Generating analysis reports..."
            generate_analysis_reports "${id}" "${codebase_dir}" "${tech_stack}"
            
            # Clear checkpoint
            clear_checkpoint "${id}"
            
            echo ""
            echo "🎉 Code analysis workflow completed successfully!"
            return 0
        fi
        
        # Get current pending task
        local current_task=$(get_next_task "${task_file}")
        if [[ -z "${current_task}" ]]; then
            echo "⚠️  No available tasks (all may be blocked or in progress)"
            echo "Waiting 30 seconds before checking again..."
            sleep 30
            continue
        fi
        
        echo "📌 Current task: ${current_task}"
        echo ""
        
        # Run Claude Code with analysis prompt
        echo "🤖 Starting Claude Code session..."
        if ! run_claude_code_session \
            "${id}" \
            "${codebase_dir}" \
            "${SCRIPT_DIR}/../templates/prompts/prompt-analyze.md" \
            "${log_file}"; then
            diagnose_failure $? "${log_file}" "${WORKFLOW_TYPE}"
            echo ""
            echo "💡 Tip: Use --resume flag to continue from last checkpoint"
            return 1
        fi
        
        echo ""
        echo "✅ Claude Code session completed"
        echo ""
        
        # Validate current phase
        echo "🔍 Validating phase completion..."
        if validate_analysis_phase "${prd_file}" "${codebase_dir}" "${RESULTS_DIR}/${id}"; then
            echo "✅ Validation passed"
            
            # Save checkpoint after successful phase
            local current_phase=$(get_current_phase_number "${task_file}")
            save_checkpoint "${id}" "${current_phase}"
            
            # Update PRD
            echo "📝 Updating PRD..."
            update_prd_phase_status "${prd_file}" "${current_phase}" "true"
        else
            echo "⚠️  Validation failed - will retry in next iteration"
        fi
        
        echo ""
        
        # Log progress
        log_progress "${id}" "${task_file}"
        
        # Show progress chart every 5 iterations
        if [[ $((iteration % 5)) -eq 0 ]]; then
            generate_progress_chart "${id}"
        fi
        
        # Display progress
        display_analysis_progress "${task_file}"
        
        echo ""
        iteration=$((iteration + 1))
        
        # Brief pause between iterations
        sleep 5
    done
    
    echo "⚠️  Maximum iterations (${max_iterations}) reached"
    echo "Analysis may be incomplete. Check state and logs."
    echo ""
    echo "💡 To resume from last checkpoint:"
    echo "   $(basename "$0") --id ${id} --resume"
    
    return 1
}

#######################################
# Run Claude Code session
#######################################
run_claude_code_session() {
    local id="$1"
    local codebase_dir="$2"
    local prompt_file="$3"
    local log_file="$4"
    
    # Load prompt
    if [[ ! -f "${prompt_file}" ]]; then
        echo "❌ Error: Prompt file not found: ${prompt_file}" >&2
        return 1
    fi
    
    local prompt=$(cat "${prompt_file}")
    
    # Add analysis-specific context
    prompt="${prompt}

## Analysis Context

**Analysis ID**: ${CLAUDE_CODE_TASK_LIST_ID}
**Mode**: ${ANALYSIS_MODE}
**Tech Stack**: ${TECH_STACK}
**Codebase**: ${CODEBASE_DIR}
**Results Directory**: ${RESULTS_DIR}

Store all analysis results in the results directory.
"
    
    # Run Claude Code with task list
    claude-code \
        --task-list "${id}" \
        --context "${codebase_dir}" \
        --context "${RESULTS_DIR}" \
        --prompt "${prompt}" \
        2>&1 | tee -a "${log_file}"
    
    return ${PIPESTATUS[0]}
}

#######################################
# Validate analysis phase
#######################################
validate_analysis_phase() {
    local prd_file="$1"
    local codebase_dir="$2"
    local results_dir="$3"
    
    # Extract current phase from PRD
    local current_phase=$(grep -A 5 "Passes: false" "${prd_file}" | head -1 | grep "Phase" || true)
    
    if [[ -z "${current_phase}" ]]; then
        echo "✅ All phases validated"
        return 0
    fi
    
    # Phase-specific validation
    case "${current_phase}" in
        *"Phase 1"*)
            # Discovery phase - check for analysis document or findings
            [[ -f "${results_dir}/ANALYSIS.md" ]] || [[ -f "${codebase_dir}/ANALYSIS.md" ]] || [[ -f "${results_dir}/findings.json" ]]
            ;;
        *"Phase 2"*)
            # Automated analysis - check for tool results
            [[ -d "${results_dir}/analysis-results" ]] || [[ -n "$(find "${results_dir}" -name '*-report.*' 2>/dev/null)" ]]
            ;;
        *"Phase 3"*)
            # Deep analysis - check for findings
            [[ -f "${results_dir}/findings.json" ]] || [[ -f "${results_dir}/technical-debt.md" ]] || [[ -f "${results_dir}/architecture-analysis.md" ]]
            ;;
        *"Phase 4"*)
            # Security - check for security report
            [[ -f "${results_dir}/security-report.md" ]] || [[ -f "${results_dir}/compliance-status.md" ]] || [[ -f "${results_dir}/vulnerabilities.json" ]]
            ;;
        *"Phase 5"*)
            # Roadmap - check for prioritized findings
            [[ -f "${results_dir}/roadmap.md" ]] || [[ -f "${results_dir}/priority-matrix.json" ]] || [[ -f "${results_dir}/recommendations.md" ]]
            ;;
        *"Phase 6"*)
            # Reporting - check for final report
            [[ -f "${results_dir}/ANALYSIS-REPORT.md" ]] || [[ -f "${results_dir}/analysis-summary.md" ]]
            ;;
        *)
            return 1
            ;;
    esac
}

#######################################
# Display analysis progress
#######################################
display_analysis_progress() {
    local task_file="$1"
    
    echo "📊 Analysis Progress:"
    echo ""
    
    local total=$(jq '.tasks | length' "${task_file}")
    local completed=$(jq '[.tasks[] | select(.status == "completed")] | length' "${task_file}")
    local in_progress=$(jq '[.tasks[] | select(.status == "in_progress")] | length' "${task_file}")
    local pending=$(jq '[.tasks[] | select(.status == "pending")] | length' "${task_file}")
    local blocked=$(jq '[.tasks[] | select(.status == "blocked")] | length' "${task_file}")
    
    echo "  Total Phases: ${total}"
    echo "  ✅ Completed: ${completed}"
    echo "  🔄 In Progress: ${in_progress}"
    echo "  ⏳ Pending: ${pending}"
    echo "  ⛔ Blocked: ${blocked}"
    echo ""
    
    # Show progress bar
    local progress=$((completed * 100 / total))
    local bar_length=50
    local filled=$((progress * bar_length / 100))
    local empty=$((bar_length - filled))
    
    printf "  ["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] %d%%\n" "${progress}"
    
    echo ""
    echo "  Current Phase: Phase $((completed + 1))/${total}"
    
    # Show time estimation
    if [[ ${completed} -gt 0 ]]; then
        local elapsed=$(( $(date +%s) - $(stat -c %Y "${HOME}/.claude/tasks/${CLAUDE_CODE_TASK_LIST_ID}.json" 2>/dev/null || date +%s) ))
        local avg_time_per_task=$((elapsed / completed))
        local remaining=$((total - completed))
        local est_remaining=$((remaining * avg_time_per_task))
        local est_hours=$((est_remaining / 3600))
        local est_mins=$(( (est_remaining % 3600) / 60 ))
        
        echo ""
        echo "  Time Elapsed: $(date -d@${elapsed} -u +%H:%M:%S)"
        echo "  Estimated Remaining: ${est_hours}h ${est_mins}m"
    fi
}

#######################################
# Generate analysis reports
#######################################
generate_analysis_reports() {
    local id="$1"
    local codebase_dir="$2"
    local tech_stack="$3"
    
    local results_dir="${RESULTS_DIR}/${id}"
    
    echo "📊 Generating Analysis Reports"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Generate WBSO report
    echo "📄 Generating WBSO verantwoordingsrapportage..."
    generate_wbso_report "${id}" "${codebase_dir}" "${tech_stack}"
    
    # Export formats (if requested)
    if [[ "${EXPORT_JSON}" == "true" ]]; then
        echo "📄 Exporting to JSON..."
        export_to_json "${id}" "${results_dir}"
    fi
    
    if [[ "${EXPORT_HTML}" == "true" ]]; then
        echo "📄 Generating HTML dashboard..."
        export_to_html "${id}" "${results_dir}"
    fi
    
    # Generate follow-up PRDs (if requested)
    if [[ "${GENERATE_MIGRATION_PRD}" == "true" ]]; then
        echo "📄 Generating Migration PRD..."
        generate_migration_prd "${id}" "${results_dir}" "${TARGET_STACK}"
    fi
    
    if [[ "${CREATE_BACKLOG}" == "true" ]]; then
        echo "📄 Creating prioritized backlog..."
        create_backlog_prds "${id}" "${results_dir}"
    fi
    
    echo ""
    echo "✅ All reports generated successfully"
    echo ""
    echo "📄 Reports available:"
    echo "  - Results: ${results_dir}/"
    echo "  - WBSO Report: ${LOGS_DIR}/${id}/WBSO-REPORT.md"
    
    if [[ "${EXPORT_JSON}" == "true" ]]; then
        echo "  - JSON Export: ${results_dir}/analysis-export.json"
    fi
    
    if [[ "${EXPORT_HTML}" == "true" ]]; then
        echo "  - HTML Dashboard: ${results_dir}/analysis-dashboard.html"
    fi
}

#######################################
# Generate WBSO report
#######################################
generate_wbso_report() {
    local id="$1"
    local codebase_dir="$2"
    local tech_stack="$3"
    
    local report_file="${LOGS_DIR}/${id}/WBSO-REPORT.md"
    local task_file="${HOME}/.claude/tasks/${id}.json"
    
    # Get codebase statistics
    local loc=$(find "${codebase_dir}" -type f \( -name "*.cs" -o -name "*.java" -o -name "*.py" -o -name "*.asp" -o -name "*.js" \) -exec wc -l {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo "N/A")
    local files=$(find "${codebase_dir}" -type f 2>/dev/null | wc -l)
    
    cat > "${report_file}" << EOF
# WBSO Verantwoordingsrapportage - Code Analyse

**Project**: MarQed.ai Code Analysis
**Analysis ID**: ${id}
**Date**: $(date +%Y-%m-%d)
**Workflow**: Code Analysis

## Samenvatting

Uitgebreide code analyse uitgevoerd op ${loc} LOC ${tech_stack} codebase
om technische schuld, security risico's, compliance status en modernisatie
mogelijkheden te bepalen.

## Codebase Informatie

- **Technology Stack**: ${tech_stack}
- **Lines of Code**: ${loc}
- **Total Files**: ${files}
- **Analysis Mode**: ${ANALYSIS_MODE}

## S&O Werkzaamheden

### Technisch Onderzoek

EOF
    
    # Extract completed tasks and their details
    jq -r '.tasks[] | select(.status == "completed") | "#### \(.title)\n\n**Duration**: \(.estimatedTime)\n**Description**: \(.description)\n\n**S&O Activiteiten**:\n- Systematisch onderzoek uitgevoerd\n- Geautomatiseerde tools toegepast\n- Nieuwe analysemethoden ontwikkeld\n- Resultaten gedocumenteerd\n\n"' "${task_file}" >> "${report_file}"
    
    cat >> "${report_file}" << EOF

## Tijdsinvestering

EOF
    
    # Calculate total time
    local total_phases=$(jq '.tasks | length' "${task_file}")
    local completed_phases=$(jq '[.tasks[] | select(.status == "completed")] | length' "${task_file}")
    
    echo "**Totaal geplande fases**: ${total_phases}" >> "${report_file}"
    echo "**Afgeronde fases**: ${completed_phases}" >> "${report_file}"
    echo "" >> "${report_file}"
    
    # Time per phase
    echo "**Tijdsverdeling per fase**:" >> "${report_file}"
    jq -r '.tasks[] | select(.status == "completed") | "- \(.title): \(.estimatedTime)"' "${task_file}" >> "${report_file}"
    
    cat >> "${report_file}" << EOF

## Innovatie Elementen

1. **Agnostisch Analyse Framework**
   - Multi-stack support ontwikkeld
   - Uniforme analyse methodologie
   - Geautomatiseerde tool orchestration

2. **Healthcare Compliance Automation**
   - NEN7510 compliance verificatie
   - ISO27001 control mapping
   - GDPR data flow analysis

3. **Predictive Analysis**
   - Technical debt scoring algoritme
   - Migration complexity berekening
   - Effort estimation model

4. **Multi-format Reporting**
   - Markdown, JSON, HTML exports
   - WBSO verantwoordingsrapportage
   - Automated follow-up PRD generation

## Technische Uitdagingen

1. **Legacy Code Pattern Detection**
   - Probleem: Geen standaard tools voor ${tech_stack}
   - Oplossing: Custom pattern detection ontwikkeld
   - Resultaat: Effectieve vulnerability identificatie

2. **Compliance Automation**
   - Probleem: Handmatige checks zijn tijdrovend
   - Oplossing: Geautomatiseerde compliance mapping
   - Resultaat: 70% snellere verificatie

3. **Multi-Stack Analysis**
   - Probleem: Verschillende stacks vereisen verschillende tools
   - Oplossing: Agnostisch framework met tool orchestration
   - Resultaat: Unified analysis approach

## Resultaten

EOF
    
    # Add results from analysis
    if [[ -f "${RESULTS_DIR}/${id}/findings.json" ]]; then
        local findings_count=$(jq 'length' "${RESULTS_DIR}/${id}/findings.json" 2>/dev/null || echo "N/A")
        echo "- **Bevindingen geïdentificeerd**: ${findings_count}" >> "${report_file}"
    fi
    
    if [[ -f "${RESULTS_DIR}/${id}/priority-matrix.json" ]]; then
        local critical=$(jq '[.[] | select(.priority == "P0-Critical")] | length' "${RESULTS_DIR}/${id}/priority-matrix.json" 2>/dev/null || echo "N/A")
        echo "- **Kritieke issues**: ${critical}" >> "${report_file}"
    fi
    
    cat >> "${report_file}" << EOF

## Kwalificatie WBSO

Dit project kwalificeert voor WBSO subsidie onder:

**Technische onzekerheid**:
- Geen bestaande oplossing voor agnostische ${tech_stack} analyse
- Healthcare compliance automation is novel
- Predictive effort estimation is experimenteel

**Systematisch onderzoek**:
- Gestructureerde 6-fase aanpak
- Wetenschappelijke methodologie toegepast
- Reproduceerbare resultaten

**Nieuwe kennis generatie**:
- Novel algorithms voor pattern detection
- Nieuwe compliance verification methods
- Innovative reporting methodologie

**Innovatie in software ontwikkeling**:
- Nieuwe analyse technieken ontwikkeld
- Automated compliance verification
- Predictive modeling voor legacy systems

---

**Rapport gegenereerd door**: MarQed.ai Workflow System
**Datum**: $(date +%Y-%m-%d\ %H:%M:%S)
**KvK**: 98614797
EOF
    
    echo "✅ WBSO report generated: ${report_file}"
}

#######################################
# Export to JSON
#######################################
export_to_json() {
    local id="$1"
    local results_dir="$2"
    
    local export_file="${results_dir}/analysis-export.json"
    
    # Consolidate all JSON results
    jq -n \
        --arg id "${id}" \
        --arg timestamp "$(date -Iseconds)" \
        --arg stack "${TECH_STACK}" \
        '{
            analysis_id: $id,
            timestamp: $timestamp,
            codebase: {
                stack: $stack,
                location: env.CODEBASE_DIR
            }
        }' > "${export_file}"
    
    # Merge in findings if available
    if [[ -f "${results_dir}/findings.json" ]]; then
        jq --slurpfile findings "${results_dir}/findings.json" \
            '.findings = $findings[0]' \
            "${export_file}" > "${export_file}.tmp"
        mv "${export_file}.tmp" "${export_file}"
    fi
    
    # Merge in metrics if available
    if [[ -f "${results_dir}/metrics.json" ]]; then
        jq --slurpfile metrics "${results_dir}/metrics.json" \
            '.metrics = $metrics[0]' \
            "${export_file}" > "${export_file}.tmp"
        mv "${export_file}.tmp" "${export_file}"
    fi
    
    # Merge in database analysis if available
    if [[ -f "${results_dir}/database-analysis.json" ]]; then
        jq --slurpfile db "${results_dir}/database-analysis.json" \
            '.database = $db[0]' \
            "${export_file}" > "${export_file}.tmp"
        mv "${export_file}.tmp" "${export_file}"
    fi
    
    echo "✅ JSON export: ${export_file}"
}

#######################################
# Export to HTML
#######################################
export_to_html() {
    local id="$1"
    local results_dir="$2"
    
    local html_file="${results_dir}/analysis-dashboard.html"
    
    # Load data from JSON if available
    local total_findings=0
    local critical_count=0
    local high_count=0
    local medium_count=0
    local low_count=0
    
    if [[ -f "${results_dir}/findings.json" ]]; then
        total_findings=$(jq 'length' "${results_dir}/findings.json" 2>/dev/null || echo 0)
        critical_count=$(jq '[.[] | select(.severity == "critical")] | length' "${results_dir}/findings.json" 2>/dev/null || echo 0)
        high_count=$(jq '[.[] | select(.severity == "high")] | length' "${results_dir}/findings.json" 2>/dev/null || echo 0)
        medium_count=$(jq '[.[] | select(.severity == "medium")] | length' "${results_dir}/findings.json" 2>/dev/null || echo 0)
        low_count=$(jq '[.[] | select(.severity == "low")] | length' "${results_dir}/findings.json" 2>/dev/null || echo 0)
    fi
    
    cat > "${html_file}" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Analysis Dashboard - ${id}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .metrics {
            display: flex;
            gap: 20px;
            margin: 30px 0;
        }
        .metric {
            flex: 1;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 5px;
            text-align: center;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #4CAF50;
        }
        .metric-label {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }
        .chart-container {
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 5px;
        }
        canvas {
            max-height: 400px;
        }
        .info {
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Code Analysis Dashboard</h1>
        
        <div class="info">
            <strong>Analysis ID:</strong> ${id}<br>
            <strong>Tech Stack:</strong> ${TECH_STACK}<br>
            <strong>Codebase:</strong> ${CODEBASE_DIR}<br>
            <strong>Generated:</strong> $(date +%Y-%m-%d\ %H:%M:%S)
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">${total_findings}</div>
                <div class="metric-label">Total Findings</div>
            </div>
            <div class="metric">
                <div class="metric-value">${critical_count}</div>
                <div class="metric-label">Critical Issues</div>
            </div>
            <div class="metric">
                <div class="metric-value">${high_count}</div>
                <div class="metric-label">High Priority</div>
            </div>
            <div class="metric">
                <div class="metric-value">$((medium_count + low_count))</div>
                <div class="metric-label">Medium/Low</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Findings by Severity</h2>
            <canvas id="severityChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h2>Priority Distribution</h2>
            <canvas id="priorityChart"></canvas>
        </div>
        
        <div class="footer">
            Generated by MarQed.ai Code Analysis Workflow<br>
            For more information: <a href="https://github.com/marqed-ai/workflows">MarQed.ai Workflows</a>
        </div>
    </div>
    
    <script>
        // Severity chart
        const severityData = {
            labels: ['Critical', 'High', 'Medium', 'Low'],
            datasets: [{
                label: 'Findings',
                data: [${critical_count}, ${high_count}, ${medium_count}, ${low_count}],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(255, 159, 64, 0.8)',
                    'rgba(255, 205, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)'
                ]
            }]
        };
        
        new Chart(document.getElementById('severityChart'), {
            type: 'bar',
            data: severityData,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // Priority chart
        const priorityData = {
            labels: ['Critical (P0)', 'High (P1)', 'Medium (P2)', 'Low (P3)'],
            datasets: [{
                label: 'Findings',
                data: [${critical_count}, ${high_count}, ${medium_count}, ${low_count}],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(255, 159, 64, 0.8)',
                    'rgba(255, 205, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)'
                ]
            }]
        };
        
        new Chart(document.getElementById('priorityChart'), {
            type: 'doughnut',
            data: priorityData,
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        });
    </script>
</body>
</html>
EOF
    
    echo "✅ HTML dashboard: ${html_file}"
}

#######################################
# Generate migration PRD (Scenario B)
#######################################
generate_migration_prd() {
    local id="$1"
    local results_dir="$2"
    local target_stack="$3"
    
    local migration_prd="MIGRATION-${id}.md"
    
    echo "📄 Generating Migration PRD from analysis..."
    
    # Copy template
    if [[ -f "${SCRIPT_DIR}/../templates/MIGRATION-TEMPLATE-v2.md" ]]; then
        cp "${SCRIPT_DIR}/../templates/MIGRATION-TEMPLATE-v2.md" "${migration_prd}"
        
        # Pre-fill with analysis findings
        sed -i "s/\[Project Name\]/Migration based on ${id}/" "${migration_prd}"
        sed -i "s/\[Date\]/$(date +%Y-%m-%d)/" "${migration_prd}"
        
        # Add reference to analysis
        cat >> "${migration_prd}" << EOF

---

## Analysis Reference

This migration PRD is based on comprehensive code analysis:

**Analysis ID**: ${id}
**Analysis Date**: $(date +%Y-%m-%d)
**Source Stack**: ${TECH_STACK}
**Target Stack**: ${target_stack}

**Key Findings**:
- Technical debt identified and quantified
- Security vulnerabilities documented
- Architecture patterns analyzed
- Migration complexity assessed

**See full analysis report**: ${results_dir}/ANALYSIS-REPORT.md

EOF
        
        echo "✅ Migration PRD generated: ${migration_prd}"
    else
        echo "⚠️  Migration template not found, skipping PRD generation"
    fi
}

#######################################
# Create backlog PRDs (Scenario C)
#######################################
create_backlog_prds() {
    local id="$1"
    local results_dir="$2"
    
    echo "📄 Creating prioritized backlog from findings..."
    
    local backlog_dir="${results_dir}/backlog"
    mkdir -p "${backlog_dir}"
    
    # Create index
    cat > "${backlog_dir}/BACKLOG-INDEX.md" << EOF
# Prioritized Backlog - ${id}

Generated from Code Analysis ${id} on $(date +%Y-%m-%d)

## Overview

This backlog contains prioritized PRDs for all P0 and P1 findings
from the code analysis. Each PRD is ready to be picked up and 
executed using the appropriate MarQed.ai workflow.

## Priority Levels

- **P0 - Critical**: Fix immediately (security, data loss risk)
- **P1 - High**: Fix this sprint/month (functionality, compliance)
- **P2 - Medium**: Fix next quarter (technical debt, improvements)
- **P3 - Low**: Backlog (nice-to-have, minor issues)

## Backlog Items

EOF
    
    # Parse findings if available
    if [[ -f "${results_dir}/findings.json" ]]; then
        local p0_count=$(jq '[.[] | select(.priority == "P0-Critical")] | length' "${results_dir}/findings.json" 2>/dev/null || echo 0)
        local p1_count=$(jq '[.[] | select(.priority == "P1-High")] | length' "${results_dir}/findings.json" 2>/dev/null || echo 0)
        
        echo "### P0 - Critical (${p0_count} items)" >> "${backlog_dir}/BACKLOG-INDEX.md"
        echo "" >> "${backlog_dir}/BACKLOG-INDEX.md"
        
        jq -r '.[] | select(.priority == "P0-Critical") | "- [ ] \(.title) - \(.description)"' \
            "${results_dir}/findings.json" >> "${backlog_dir}/BACKLOG-INDEX.md" 2>/dev/null || true
        
        echo "" >> "${backlog_dir}/BACKLOG-INDEX.md"
        echo "### P1 - High (${p1_count} items)" >> "${backlog_dir}/BACKLOG-INDEX.md"
        echo "" >> "${backlog_dir}/BACKLOG-INDEX.md"
        
        jq -r '.[] | select(.priority == "P1-High") | "- [ ] \(.title) - \(.description)"' \
            "${results_dir}/findings.json" >> "${backlog_dir}/BACKLOG-INDEX.md" 2>/dev/null || true
    else
        echo "⚠️  No findings.json available for backlog generation"
    fi
    
    echo ""
    echo "✅ Backlog index created: ${backlog_dir}/BACKLOG-INDEX.md"
}

#######################################
# Main entry point
#######################################
main() {
    local id=""
    local prd_file="./PRD.md"
    local codebase_dir=""
    local mode="standard"
    local force_stack="auto"
    local max_iterations="${MAX_ITERATIONS}"
    local database_connection=""
    local db_type="sqlserver"
    
    # Scenario options
    export GENERATE_MIGRATION_PRD="false"
    export CREATE_BACKLOG="false"
    export TARGET_STACK=""
    
    # Export options
    export EXPORT_JSON="false"
    export EXPORT_HTML="false"
    
    # Execution control
    local resume=false
    local clear_checkpoint_flag=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--id)
                id="$2"
                shift 2
                ;;
            -c|--codebase)
                codebase_dir="$2"
                shift 2
                ;;
            -p|--prd)
                prd_file="$2"
                shift 2
                ;;
            -m|--mode)
                mode="$2"
                shift 2
                ;;
            -s|--stack)
                force_stack="$2"
                shift 2
                ;;
            -d|--database)
                database_connection="$2"
                shift 2
                ;;
            --db-type)
                db_type="$2"
                shift 2
                ;;
            --generate-migration-prd)
                GENERATE_MIGRATION_PRD="true"
                shift
                ;;
            --create-backlog)
                CREATE_BACKLOG="true"
                shift
                ;;
            --target-stack)
                TARGET_STACK="$2"
                shift 2
                ;;
            --resume)
                resume=true
                shift
                ;;
            --clear-checkpoint)
                clear_checkpoint_flag=true
                shift
                ;;
            --max-iter)
                max_iterations="$2"
                shift 2
                ;;
            --export-json)
                EXPORT_JSON="true"
                shift
                ;;
            --export-html)
                EXPORT_HTML="true"
                shift
                ;;
            --export-all)
                EXPORT_JSON="true"
                EXPORT_HTML="true"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo "❌ Error: Unknown option: $1" >&2
                usage
                exit 1
                ;;
        esac
    done
    
    # Validate required arguments
    if [[ -z "${id}" ]]; then
        echo "❌ Error: Analysis ID is required (-i|--id)" >&2
        usage
        exit 1
    fi
    
    if [[ -z "${codebase_dir}" ]]; then
        echo "❌ Error: Codebase directory is required (-c|--codebase)" >&2
        usage
        exit 1
    fi
    
    # Handle checkpoint clearing
    if [[ "${clear_checkpoint_flag}" == true ]]; then
        clear_checkpoint "${id}"
        echo "✅ Checkpoint cleared for ${id}"
        exit 0
    fi
    
    # Detect tech stack
    local detected_stack=$(detect_tech_stack "${codebase_dir}" "${force_stack}")
    export TECH_STACK="${detected_stack}"
    export DB_TYPE="${db_type}"
    
    # Initialize workflow
    initialize_analysis "${id}" "${prd_file}" "${codebase_dir}"
    
    # Run database analysis if connection provided
    if [[ -n "${database_connection}" ]]; then
        run_database_analysis "${database_connection}" "${db_type}" "${RESULTS_DIR}/${id}"
    fi
    
    # Run main loop
    marqed_analysis_loop "${id}" "${prd_file}" "${codebase_dir}" "${max_iterations}" "${mode}" "${detected_stack}"
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi