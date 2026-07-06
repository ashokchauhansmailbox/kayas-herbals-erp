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
  Continue Sprint 1.1 — Kaya BOS (Business Operating System).
  Repository: https://github.com/ashokchauhansmailbox/kayas-herbals-erp
  Sprint 1.1 scope = Database Foundation:
    - SQLAlchemy Base + async session + mixins + type helpers
    - Identity models (9 tables) and Master-data models (10 tables)
    - Alembic setup + migrations 001 (extensions/enums), 002 (identity), 003 (master data)
    - Per-migration docs under /docs/database
    - Smoke tests: model-contract + migration cycle (upgrade → downgrade → upgrade)

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
        -comment: "Verified live returns ok; ready returns db up; db endpoint reports alembic_revision=003 and 20 tables. Fixed pre-existing broken import in app/api/v1/__init__.py that referenced non-existent route modules."

  - task: "Pytest suite (39 cases)"
    implemented: true
    working: true
    file: "backend/tests/test_models_schema.py, backend/tests/test_migrations_cycle.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "main"
        -comment: "39 passed. Model-contract tests need no DB (import metadata); migration-cycle tests exercise upgrade/downgrade/upgrade + enum + extension + drift on kaya_bos_test. pytest.ini configured -n 2 --dist loadscope."

frontend:
  - task: "Sprint 1.1 has no frontend work"
    implemented: false
    working: "NA"
    file: "n/a"
    stuck_count: 0
    priority: "low"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Sprint 1.1 is database-only. Frontend rework is scheduled for Sprint 2."

metadata:
  created_by: "main_agent"
  version: "1.1"
  test_sequence: 1
  run_ui: false

test_plan:
  current_focus:
    - "Alembic migrations 001-003"
    - "Pytest suite (39 cases)"
    - "Health endpoints (/api/v1/health/live, /ready, /db)"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    -agent: "main"
    -message: "Sprint 1.1 (Database Foundation) complete. 39/39 pytest green. Alembic round-trip + drift-check clean. Ready to move to Sprint 1.2 (Catalog + Inventory) on next request."