#!/bin/bash
set -e

BASE_DIR="data/documents"
mkdir -p "$BASE_DIR/dbt"
mkdir -p "$BASE_DIR/airflow"
mkdir -p "$BASE_DIR/great_expectations"

echo "=== Fetching Great Expectations docs ==="

GE_BASE="https://raw.githubusercontent.com/great-expectations/great_expectations/develop/docs/docusaurus/docs/core"

declare -A GE_DOCS=(
  ["define_expectations.md"]="$GE_BASE/define_expectations/define_expectations.md"
  ["create_an_expectation.md"]="$GE_BASE/define_expectations/create_an_expectation.md"
  ["organize_expectation_suites.md"]="$GE_BASE/define_expectations/organize_expectation_suites.md"
  ["test_an_expectation.md"]="$GE_BASE/define_expectations/test_an_expectation.md"
  ["connect_to_data.md"]="$GE_BASE/connect_to_data/connect_to_data.md"
  ["run_validations.md"]="$GE_BASE/run_validations/run_validations.md"
  ["create_a_validation_definition.md"]="$GE_BASE/run_validations/create_a_validation_definition.md"
  ["run_a_validation_definition.md"]="$GE_BASE/run_validations/run_a_validation_definition.md"
)

for filename in "${!GE_DOCS[@]}"; do
  url="${GE_DOCS[$filename]}"
  echo "  → $filename"
  curl -sf "$url" -o "$BASE_DIR/great_expectations/$filename" || echo "    ⚠ Failed: $url"
done

echo ""
echo "=== Fetching Airflow docs (from PyPI mirrors) ==="

# Airflow moved docs to a separate repo: apache/airflow-site
AIRFLOW_BASE="https://raw.githubusercontent.com/apache/airflow/v2-10-stable/docs/apache-airflow/core-concepts"

declare -A AIRFLOW_DOCS=(
  ["dags.rst"]="$AIRFLOW_BASE/dags.rst"
  ["tasks.rst"]="$AIRFLOW_BASE/tasks.rst"
  ["operators.rst"]="$AIRFLOW_BASE/operators.rst"
  ["sensors.rst"]="$AIRFLOW_BASE/sensors.rst"
  ["hooks.rst"]="$AIRFLOW_BASE/hooks.rst"
  ["connections.rst"]="$AIRFLOW_BASE/connections.rst"
  ["xcoms.rst"]="$AIRFLOW_BASE/xcoms.rst"
  ["scheduler.rst"]="$AIRFLOW_BASE/scheduler.rst"
  ["taskflow.rst"]="$AIRFLOW_BASE/taskflow.rst"
)

for filename in "${!AIRFLOW_DOCS[@]}"; do
  url="${AIRFLOW_DOCS[$filename]}"
  echo "  → $filename"
  curl -sf "$url" -o "$BASE_DIR/airflow/$filename" || echo "    ⚠ Failed: $url"
done

echo ""
echo "=== Summary ==="
echo "dbt docs:                $(ls $BASE_DIR/dbt/*.md 2>/dev/null | wc -l) files"
echo "Airflow docs:            $(ls $BASE_DIR/airflow/*.rst 2>/dev/null | wc -l) files"
echo "Great Expectations docs: $(ls $BASE_DIR/great_expectations/*.md 2>/dev/null | wc -l) files"
echo ""
echo "Done."
