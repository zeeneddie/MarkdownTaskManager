#!/bin/bash
#
# Test Work Type Classifier
# Tests LLM-based and keyword-based classification
#

echo "🚀 Starting Work Type Classifier Tests..."
echo ""

# Compile TypeScript
echo "📦 Compiling TypeScript..."
npx tsc test_work_type_classifier.ts --module nodenext --moduleResolution nodenext --target es2022 --lib es2022 --esModuleInterop --resolveJsonModule --skipLibCheck 2>&1 | head -20

if [ $? -ne 0 ]; then
    echo "❌ TypeScript compilation failed"
    exit 1
fi

echo "✅ Compilation successful"
echo ""

# Run tests
echo "🧪 Running classification tests..."
echo ""
node test_work_type_classifier.js

exit_code=$?

# Cleanup
rm -f test_work_type_classifier.js

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ All tests completed successfully"
else
    echo ""
    echo "❌ Tests failed with exit code $exit_code"
fi

exit $exit_code
