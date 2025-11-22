# Agent Prompts for Algo Sovereignty Analyzer

Here are three detailed prompts to parallelize development.

## Prompt 1: Expand API Layer (Priority: High)
**Role:** Backend API Engineer
**Context:** We have a basic FastAPI structure in `api/` and core logic in `core/`.
**Task:** Build out the full REST API to support the frontend.
**Requirements:**
1.  **Implement Endpoints:**
    *   `POST /api/v1/analyze`: Accepts JSON body `{"address": "...", "monthly_expenses": 3000}`. Calls `core.analyzer`, calculates sovereignty ratio if expenses provided, and returns full analysis.
    *   `GET /api/v1/classifications`: Returns the current list of manual asset classifications from `data/asset_classification.csv`.
    *   `POST /api/v1/classifications`: (Optional) Endpoint to suggest or add new classifications (validate input).
2.  **Refine Schemas:** Update `api/schemas.py` to ensure all Pydantic models perfectly match the JSON output from `core`.
3.  **CORS:** Configure CORS in `api/main.py` to allow requests from `http://localhost:3000` (our future frontend).
4.  **Error Handling:** Ensure graceful 404s for invalid addresses and 500s for node errors.

## Prompt 2: Enhance Core Engine (Priority: High)
**Role:** Python Data Engineer
**Context:** The core logic in `core/` works but is basic. We need it to be more robust and testable.
**Task:** Refine the classification engine and add testing.
**Requirements:**
1.  **Improve Classification (`core/classifier.py`):**
    *   Refactor the regex patterns into a more maintainable structure (e.g., a configuration dict or separate file).
    *   Add a method to easily reload classifications without restarting.
2.  **Robustness (`core/analyzer.py`):**
    *   Add retry logic for CoinGecko API calls.
    *   Handle cases where `asset_classification.csv` might be missing or malformed without crashing.
3.  **Testing:**
    *   Flesh out `tests/test_classifier.py` with real test cases (mocking the CSV).
    *   Add unit tests for `core/models.py` to ensure validation works.

## Prompt 3: Scaffold Frontend (Priority: Medium - Do after API is ready)
**Role:** Senior Frontend Engineer
**Context:** We need a modern web interface for the analyzer.
**Task:** Initialize the `web/` directory and build the main dashboard.
**Requirements:**
1.  **Setup:** Initialize a Next.js 14 (App Router) project in `web/`. Use TypeScript and Tailwind CSS.
2.  **UI Components:** Install `shadcn/ui` (or similar) for polished components (Cards, Inputs, Buttons).
3.  **Features:**
    *   **Landing Page:** A clean, "Sovereignty" themed search bar for the Algorand address.
    *   **Dashboard:** A results page showing:
        *   Sovereignty Score (Big, color-coded).
        *   Asset Breakdown (Hard Money vs Productive vs Shitcoins).
        *   "Runway" calculator (Input field to tweak monthly expenses and see how the score changes live).
4.  **Integration:** Fetch data from `http://localhost:8000/api/v1/analyze`.
