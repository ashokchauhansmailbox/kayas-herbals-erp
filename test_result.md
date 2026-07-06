#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Continue Sprint 1.1 → 1.2 — Kaya BOS (Business Operating System).
  Repository: https://github.com/ashokchauhansmailbox/kayas-herbals-erp

  Sprint 1.1 (Database Foundation) — SQLAlchemy Base + async session + mixins
  + type helpers + identity/master-data models + Alembic 001–003 + tests.

  Pre-Sprint-1.2 tooling — OpenAPI baseline (JSON+YAML), CI (ruff/mypy/pytest/
  alembic cycle/openapi drift), .env.example, mypy.ini, docker-compose init
  script, reproducibility verification against a fresh Postgres.

  Sprint 1.2 (Catalog + Inventory) — catalog.py (products, variants, images,
  documents, certifications, price journals) + inventory.py (batches, ledger,
  snapshots, transfers, adjustments, alerts) + v_stock_valuation view +
  migrations 004, 005 + per-migration docs + unit/integration/smoke tests.

backend:
  - task: "SQLAlchemy foundation (base, session, mixins, types)"
    implemented: true
    working: true
    file: "backend/app/db/base.py, backend/app/db/session.py, backend/app/db/mixins.py, backend/app/db/types.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "Base with naming convention + async engine factory + Timestamp/Actor/SoftDelete/Version mixins + uuid_pk/jsonb_column helpers."

  - task: "Identity models (users, roles, permissions, sessions, invitations, audit/activity logs)"
    implemented: true
    working: true
    file: "backend/app/models/identity.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "9 tables per docs/architecture/02. users.id has no server_default (Supabase-owned); composite PKs on join tables; audit_logs indexed on (entity, entity_id, at) and (actor_id, at)."

  - task: "Master-data models (units, gst_rates, hsn_codes, categories, brands, warehouses, payment_terms, tax_rules, transporters, courier_partners)"
    implemented: true
    working: true
    file: "backend/app/models/master_data.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "10 tables per docs/architecture/08. Effective-dating on gst_rates + tax_rules. Warehouses carry version column."

  - task: "Alembic migrations 001-003"
    implemented: true
    working: true
    file: "backend/migrations/versions/001_extensions_and_enums.py, 002_identity_core.py, 003_master_data.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "Round-trip 'upgrade head → downgrade base → upgrade head' passes. 'alembic check' returns 'No new upgrade operations detected'. Actor FKs on master-data added post-create with use_alter to break the circular dep with users."

  - task: "Health endpoints (/api/v1/health/live, /ready, /db)"
    implemented: true
    working: true
    file: "backend/app/api/v1/routes/health.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "Verified live returns ok; ready returns db up; db endpoint reports alembic_revision=005 (post-Sprint-1.2) and 34 tables. Fixed pre-existing broken import in app/api/v1/__init__.py."

  - task: "OpenAPI baseline + drift-check CI"
    implemented: true
    working: true
    file: "scripts/generate_openapi.py, scripts/check_openapi_drift.py, docs/api/openapi.json, docs/api/openapi.yaml, .github/workflows/ci.yml"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "OpenAPI regenerated deterministically (sorted keys, 2-space indent, trailing newline). CI job openapi-contract re-runs generator and fails if drift detected. Verified locally: drift-check passes."

  - task: "Reproducibility (fresh clone + venv + postgres → migrations + tests + health)"
    implemented: true
    working: true
    file: "docker-compose.yml, infra/postgres-init/01-create-test-db.sql, backend/.env.example"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "Ran a full clean rebuild in /tmp: fresh venv + fresh Postgres DB + fresh pip install + alembic upgrade head → downgrade base → upgrade head + pytest (79 passed) + health endpoints (live/ready/db) all responding. PASS."

  - task: "Sprint 1.2 — Catalog models (product, variant, image, document, certification, price journals)"
    implemented: true
    working: true
    file: "backend/app/models/catalog.py, backend/migrations/versions/004_catalog.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "7 tables. products carries version + soft delete + FSSAI/AYUSH metadata. product_variants uniqueness on sku + barcode. Two append-only journals (product_price_history, purchase_price_history). purchase_price_history.vendor_id/po_id left FK-less (Sprint 1.3 will add)."

  - task: "Sprint 1.2 — Inventory models (batches, ledger, snapshots, transfers, adjustments, alerts) + v_stock_valuation view"
    implemented: true
    working: true
    file: "backend/app/models/inventory.py, backend/migrations/versions/005_inventory.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "7 tables + v_stock_valuation view. CHECK constraints enforce BR-INV-02 (ledger qty != 0), BR-INV-08 (available qty >= 0), from ≠ to on transfers, positive qty on transfer items. Functional unique index on stock_snapshots(variant, warehouse, COALESCE(batch, zero-uuid), state). Integration test verifies view returns qty*cost + days_to_expiry."

  - task: "Pytest suite (79 cases across Sprint 1.1 + 1.2)"
    implemented: true
    working: true
    file: "backend/tests/test_models_schema.py, backend/tests/test_migrations_cycle.py, backend/tests/test_catalog_inventory.py, backend/tests/conftest.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "79/79 passed under pytest-xdist -n2 loadscope. conftest.py gives each worker its own database (base_db + _gwN suffix) so migration-cycle + catalog-inventory tests no longer collide."

frontend:
  - task: "Sprint 1.1 + 1.2 have no frontend work"
    implemented: false
    working: "NA"
    file: "n/a"
    stuck_count: 0
    priority: "low"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Database-only sprints. Frontend rework is scheduled for Sprint 2."

metadata:
  created_by: "main_agent"
  version: "1.2"
  test_sequence: 2
  run_ui: false

test_plan:
  current_focus:
    - "Sprint 1.2 — Catalog models"
    - "Sprint 1.2 — Inventory models + v_stock_valuation view"
    - "Pytest suite (79 cases)"
    - "OpenAPI drift check"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    -agent: "main"
    -message: "Sprint 1.2 (Catalog + Inventory) complete. 79/79 pytest green. Alembic round-trip + drift-check clean. Reproducibility verified in a clean venv. Awaiting sprint review + approval before starting Sprint 1.3 (Purchase + Distributor + Customer)."