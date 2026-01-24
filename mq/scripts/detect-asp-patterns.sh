#!/bin/bash
# Detect ASP Classic patterns that need migration

set -e

CODEBASE_DIR="$1"
OUTPUT_FILE="${2:-asp-patterns-detected.json}"

if [[ -z "${CODEBASE_DIR}" ]]; then
    echo "Usage: $0 <codebase_dir> [output_file]"
    exit 1
fi

echo "🔍 Detecting ASP Classic patterns in: ${CODEBASE_DIR}"

# Initialize JSON
cat > "${OUTPUT_FILE}" << 'EOF'
{
  "timestamp": "",
  "codebase": "",
  "patterns": {}
}
EOF

# Update timestamp and codebase
jq --arg ts "$(date -Iseconds)" \
   --arg cb "${CODEBASE_DIR}" \
   '.timestamp = $ts | .codebase = $cb' \
   "${OUTPUT_FILE}" > "${OUTPUT_FILE}.tmp"
mv "${OUTPUT_FILE}.tmp" "${OUTPUT_FILE}"

# Pattern: SQL Injection (string concatenation in queries)
echo "  🔍 Detecting SQL injection patterns..."
sql_injection=$(grep -rn "Execute.*&\|.*&.*Execute" "${CODEBASE_DIR}"/*.asp 2>/dev/null | wc -l || echo 0)

# Pattern: Session usage
echo "  🔍 Detecting session usage..."
session_usage=$(grep -rn "Session(" "${CODEBASE_DIR}"/*.asp 2>/dev/null | wc -l || echo 0)

# Pattern: Response.Write
echo "  🔍 Detecting Response.Write patterns..."
response_write=$(grep -rn "Response.Write" "${CODEBASE_DIR}"/*.asp 2>/dev/null | wc -l || echo 0)

# Pattern: ADODB.Connection
echo "  🔍 Detecting database connections..."
db_connections=$(grep -rn "ADODB.Connection\|ADODB.Command" "${CODEBASE_DIR}"/*.asp 2>/dev/null | wc -l || echo 0)

# Pattern: File upload (third-party components)
echo "  🔍 Detecting file upload components..."
file_uploads=$(grep -rni "Persits.Upload\|ASPUpload\|Upload" "${CODEBASE_DIR}"/*.asp 2>/dev/null | wc -l || echo 0)

# Pattern: CDO.Message (email)
echo "  🔍 Detecting email functionality..."
email_usage=$(grep -rn "CDO.Message" "${CODEBASE_DIR}"/*.asp 2>/dev/null | wc -l || echo 0)

# Pattern: On Error Resume Next
echo "  🔍 Detecting error handling..."
error_handling=$(grep -rn "On Error Resume Next" "${CODEBASE_DIR}"/*.asp 2>/dev/null | wc -l || echo 0)

# Add all patterns to JSON
jq --argjson sql "${sql_injection}" \
   --argjson sess "${session_usage}" \
   --argjson resp "${response_write}" \
   --argjson db "${db_connections}" \
   --argjson upload "${file_uploads}" \
   --argjson email "${email_usage}" \
   --argjson err "${error_handling}" \
   '.patterns = {
     "sql_injection_risk": {
       "count": $sql,
       "priority": "P0",
       "complexity": "high",
       "estimated_hours": ($sql * 0.5)
     },
     "session_management": {
       "count": $sess,
       "priority": "P1",
       "complexity": "low",
       "estimated_hours": ($sess * 0.1)
     },
     "response_output": {
       "count": $resp,
       "priority": "P2",
       "complexity": "medium",
       "estimated_hours": ($resp * 0.05)
     },
     "database_access": {
       "count": $db,
       "priority": "P0",
       "complexity": "high",
       "estimated_hours": ($db * 0.3)
     },
     "file_uploads": {
       "count": $upload,
       "priority": "P2",
       "complexity": "medium",
       "estimated_hours": ($upload * 2)
     },
     "email_sending": {
       "count": $email,
       "priority": "P2",
       "complexity": "low",
       "estimated_hours": ($email * 1)
     },
     "error_handling": {
       "count": $err,
       "priority": "P2",
       "complexity": "low",
       "estimated_hours": ($err * 0.2)
     }
   }' "${OUTPUT_FILE}" > "${OUTPUT_FILE}.tmp"
mv "${OUTPUT_FILE}.tmp" "${OUTPUT_FILE}"

# Calculate totals
jq '.summary = {
  "total_patterns": ([.patterns[].count] | add),
  "total_estimated_hours": ([.patterns[].estimated_hours] | add | floor),
  "high_priority_count": ([.patterns[] | select(.priority == "P0") | .count] | add)
}' "${OUTPUT_FILE}" > "${OUTPUT_FILE}.tmp"
mv "${OUTPUT_FILE}.tmp" "${OUTPUT_FILE}"

echo ""
echo "✅ Pattern detection complete"
echo ""
echo "📊 Summary:"
jq -r '.summary | "  Total patterns: \(.total_patterns)
  Total estimated hours: \(.total_estimated_hours)
  High priority (P0): \(.high_priority_count)"' "${OUTPUT_FILE}"

echo ""
echo "📄 Full report: ${OUTPUT_FILE}"