#!/bin/bash
# Full audit script - finds all issues to fix

echo "🔍 Starting Full System Audit..."
echo ""

AUDIT_DIR="audit-results-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$AUDIT_DIR"

echo "📋 Phase 1: Marketing Claims Audit"
echo "=================================="

# Find all "patent" references
echo "Finding 'patent' references..."
grep -r -i "patent" --include="*.py" --include="*.html" --include="*.md" --include="*.txt" . > "$AUDIT_DIR/patent-claims.txt" 2>/dev/null
echo "  ✅ Found $(wc -l < "$AUDIT_DIR/patent-claims.txt") references"
echo "  📄 Saved to: $AUDIT_DIR/patent-claims.txt"

# Find all "proprietary" references
echo "Finding 'proprietary' references..."
grep -r -i "proprietary" --include="*.py" --include="*.html" --include="*.md" . > "$AUDIT_DIR/proprietary-claims.txt" 2>/dev/null
echo "  ✅ Found $(wc -l < "$AUDIT_DIR/proprietary-claims.txt") references"

# Find all "military-grade" references
echo "Finding 'military-grade' references..."
grep -r -i "military.*grade\|government.*grade" --include="*.py" --include="*.html" --include="*.md" . > "$AUDIT_DIR/military-claims.txt" 2>/dev/null
echo "  ✅ Found $(wc -l < "$AUDIT_DIR/military-claims.txt") references"

# Find all "unique" or "exclusive" technology claims
echo "Finding 'unique/exclusive' claims..."
grep -r -i "unique.*technology\|exclusive.*technology\|our own.*protocol" --include="*.py" --include="*.html" --include="*.md" . > "$AUDIT_DIR/unique-claims.txt" 2>/dev/null
echo "  ✅ Found $(wc -l < "$AUDIT_DIR/unique-claims.txt") references"

echo ""
echo "🔒 Phase 2: Security Audit"
echo "=========================="

# Find hardcoded credentials
echo "Finding potential hardcoded credentials..."
grep -r -i "password.*=.*['\"].*['\"]\|api.*key.*=.*['\"].*['\"]\|secret.*=.*['\"].*['\"]" --include="*.py" . > "$AUDIT_DIR/hardcoded-secrets.txt" 2>/dev/null
echo "  ✅ Found $(wc -l < "$AUDIT_DIR/hardcoded-secrets.txt") potential issues"

# Find SQL queries (potential injection)
echo "Finding SQL queries..."
grep -r -i "SELECT\|INSERT\|UPDATE\|DELETE.*\+.*\$\|f\".*SELECT" --include="*.py" . > "$AUDIT_DIR/sql-queries.txt" 2>/dev/null
echo "  ✅ Found $(wc -l < "$AUDIT_DIR/sql-queries.txt") SQL queries to review"

# Find eval/exec usage (dangerous)
echo "Finding eval/exec usage..."
grep -r "eval(\|exec(\|__import__" --include="*.py" . > "$AUDIT_DIR/dangerous-functions.txt" 2>/dev/null
echo "  ✅ Found $(wc -l < "$AUDIT_DIR/dangerous-functions.txt") uses"

# Find file operations (potential path traversal)
echo "Finding file operations..."
grep -r "open(\|file(\|Path(" --include="*.py" . | grep -v "#" | head -50 > "$AUDIT_DIR/file-operations.txt" 2>/dev/null
echo "  ✅ Found file operations to review"

echo ""
echo "📦 Phase 3: Code Quality Audit"
echo "==============================="

# Find TODO/FIXME comments
echo "Finding TODO/FIXME comments..."
grep -r -i "TODO\|FIXME\|HACK\|XXX" --include="*.py" --include="*.sh" . > "$AUDIT_DIR/todos.txt" 2>/dev/null
echo "  ✅ Found $(wc -l < "$AUDIT_DIR/todos.txt") items"

# Find print statements (should use logging)
echo "Finding print statements (should use logging)..."
grep -r "^[^#]*print(" --include="*.py" . | wc -l > "$AUDIT_DIR/print-statements-count.txt" 2>/dev/null
echo "  ✅ Found $(cat "$AUDIT_DIR/print-statements-count.txt") print statements"

echo ""
echo "📊 Audit Summary"
echo "==============="
echo "All results saved to: $AUDIT_DIR/"
echo ""
echo "Files to review:"
ls -lh "$AUDIT_DIR"/*.txt 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'
echo ""
echo "✅ Audit complete! Review the files above."

