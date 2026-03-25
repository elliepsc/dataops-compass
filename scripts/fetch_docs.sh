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

echo "=== Fetching additional dbt docs ==="

DBT_BASE="https://raw.githubusercontent.com/dbt-labs/docs.getdbt.com/current/website/docs/docs"

declare -A DBT_EXTRA=(
  ["ref.md"]="$DBT_BASE/build/ref.md"
  ["incremental-models.md"]="$DBT_BASE/build/incremental-models.md"
  ["packages.md"]="$DBT_BASE/build/packages.md"
  ["schema-yml.md"]="$DBT_BASE/build/schema-yml.md"
  ["node-selection.md"]="$DBT_BASE/reference/node-selection/syntax.md"
  ["dbt-project-yml.md"]="$DBT_BASE/reference/dbt_project.yml.md"
)

for filename in "${!DBT_EXTRA[@]}"; do
  url="${DBT_EXTRA[$filename]}"
  echo "  → $filename"
  curl -sf "$url" -o "data/documents/dbt/$filename" || echo "    ⚠ Failed: $url"
done

echo "=== Fetching missing Airflow docs ==="

AIRFLOW_BASE="https://raw.githubusercontent.com/apache/airflow/v2-10-stable/docs/apache-airflow/core-concepts"

declare -A AIRFLOW_EXTRA=(
  ["connections.rst"]="$AIRFLOW_BASE/connections.rst"
  ["hooks.rst"]="$AIRFLOW_BASE/hooks.rst"
  ["scheduler.rst"]="$AIRFLOW_BASE/scheduler.rst"
  ["variables.rst"]="https://raw.githubusercontent.com/apache/airflow/v2-10-stable/docs/apache-airflow/core-concepts/variables.rst"
  ["params.rst"]="https://raw.githubusercontent.com/apache/airflow/v2-10-stable/docs/apache-airflow/core-concepts/params.rst"
)

for filename in "${!AIRFLOW_EXTRA[@]}"; do
  url="${AIRFLOW_EXTRA[$filename]}"
  echo "  → $filename"
  curl -sf "$url" -o "data/documents/airflow/$filename" || echo "    ⚠ Failed: $url"
done

echo "=== Fetching missing GE docs ==="

GE_BASE="https://raw.githubusercontent.com/great-expectations/great_expectations/develop/docs/docusaurus/docs"

declare -A GE_EXTRA=(
  ["checkpoints.md"]="$GE_BASE/core/trigger_actions_based_on_results/create_a_checkpoint.md"
  ["data_docs.md"]="$GE_BASE/core/trigger_actions_based_on_results/choose_how_to_view_validation_results.md"
  ["suites_overview.md"]="$GE_BASE/core/define_expectations/organize_expectation_suites.md"
  ["gx_overview.md"]="$GE_BASE/gx_welcome.md"
  ["set_up_environment.md"]="$GE_BASE/core/set_up_a_gx_environment/set_up_a_gx_environment.md"
)

for filename in "${!GE_EXTRA[@]}"; do
  url="${GE_EXTRA[$filename]}"
  echo "  → $filename"
  curl -sf "$url" -o "data/documents/great_expectations/$filename" || echo "    ⚠ Failed: $url"
done

echo ""
echo "=== Final Summary ==="
echo "dbt docs:                $(ls data/documents/dbt/*.md 2>/dev/null | wc -l) files"
echo "Airflow docs:            $(ls data/documents/airflow/*.rst 2>/dev/null | wc -l) files"
echo "Great Expectations docs: $(ls data/documents/great_expectations/*.md 2>/dev/null | wc -l) files"
