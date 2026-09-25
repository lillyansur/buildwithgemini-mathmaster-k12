# MathMaster K-12

An intelligent, interactive math tutoring agent designed to help K-12 students master mathematical concepts through verified step-by-step solutions, symbolic computation, educational illustrations, formula catalog lookups, and practice problems.

![MathMaster K-12 Demo](assets/demo.gif)

---

## What the Agent Actually Does

Built with Google's **Agent Development Kit (ADK)** and running on **Gemini 2.5 Flash** (`gemini-2.5-flash`), MathMaster K-12 combines deterministic computation engines with generative AI to provide 100% verified math guidance.

### Implemented Capabilities & Tools

1. **Symbolic Mathematics & Equation Solving (`solve_and_verify_math`)**
   - Uses **SymPy** for exact mathematical accuracy.
   - Solves linear, polynomial, and systems of equations.
   - Factors polynomials, simplifies algebraic expressions, expands terms, and produces exact roots and decimal approximations.

2. **2D Function Plotting (`generate_and_save_plot`)**
   - Uses **Matplotlib** and **NumPy** in a headless environment to generate clean 2D plots for functions (polynomials, quadratics, trigonometric functions).
   - Automatically saves and streams generated plots to a public Google Cloud Storage bucket and returns public HTTPS image URLs.

3. **Multimodal Diagram & Illustration Generation (`generate_math_illustration`)**
   - Powered by `gemini-3.1-flash-lite-image` in Vertex AI (`global` location).
   - Generates educational textbook-style visual diagrams (geometric figures, right-angled triangles, coordinate systems).
   - Saves artifacts to the agent tool context and uploads high-resolution images to Google Cloud Storage.

4. **K-12 Formula & Theorem Catalog (`search_math_formulas`, `get_formula_details`, `save_math_formula`)**
   - Grounded in a dedicated **Google Cloud Firestore** collection (`math_formulas`).
   - Supports search across titles, descriptions, and formulas with category and grade-level filters (Elementary, Middle, High School).
   - Retrieves derivation steps, canonical formula definitions, and worked examples.

5. **Practice Problem Generator & Progress Tracker (`generate_practice_problem`, `record_student_attempt`)**
   - Creates randomized, mathematically verified practice exercises across algebra and geometry with hints and step derivations.
   - Saves generated exercises to Firestore (`practice_problems`).
   - Records student submissions in Firestore (`student_progress`) and computes cumulative accuracy percentages.

6. **Rich Card UI (`A2UI v0.8`)**
   - Implements Google's **Agent-to-User Interface (A2UI)** v0.8 with the Basic Catalog.
   - Emits structured JSON payloads containing `Card`, `Column`, `Row`, `Text`, and `Image` components.
   - The included custom chat frontend renders A2UI natively in the browser alongside standard conversation text.

---

## Google Cloud Services Wired Up

- **Vertex AI Agent Runtime (Agent Engine)**: Hosts the agent backend over the Agent-to-Agent (A2A 1.0) protocol.
- **Vertex AI Gemini Models**:
  - `gemini-2.5-flash`: Core reasoning, step derivation, and A2UI orchestration.
  - `gemini-3.1-flash-lite-image`: Geometric diagram and textbook illustration synthesis.
- **Google Cloud Firestore**: Persists formula knowledge bases (`math_formulas`), practice banks (`practice_problems`), and attempt telemetry (`student_progress`).
- **Google Cloud Storage (GCS)**: Stores rendered Matplotlib plots and Gemini-generated illustrations with public HTTPS access.
- **Google Cloud Run**: Hosts the production FastAPI proxy and responsive A2UI chat interface.

---

## Planned / Not Yet Implemented Features

The following items from the initial design brief are planned for future iterations:
- **Cross-session Long-Term Memory Bank**: Persistent student mastery profiles across independent user sessions (planned, not yet implemented).
- **Interactive Socratic Dialogue Branching**: Multi-step student assessment workflows (currently student progress is recorded per problem attempt).

---

## Project Structure

```
mathmaster-k12/
├── app/
│   ├── agent.py               # Core agent definition, prompts, and tool implementations
│   ├── a2ui_utils.py          # A2UI after-model callback and payload processor
│   ├── fast_api_app.py        # Local ADK FastAPI runtime server
│   └── app_utils/             # A2A adapters and runtime helpers
├── assets/
│   └── demo.gif               # Recorded walkthrough of agent problem solving and diagram generation
├── frontend/
│   ├── main.py                # FastAPI proxy connecting browser to deployed A2A agent
│   ├── static/
│   │   └── index.html         # Responsive chat UI with native A2UI card renderer
│   └── requirements.txt       # Frontend proxy dependencies
├── agents-cli-manifest.yaml   # Deployment metadata and runtime configuration
└── pyproject.toml             # Python dependencies and build specifications
```

---

## Running Locally

### 1. Run the Agent Locally via ADK Playground

```bash
# Navigate to the project root
cd mathmaster-k12

# Install dependencies with uv
uv sync

# Launch the ADK development environment
uv run agents-cli playground
```

### 2. Run the Web Frontend & A2A Proxy Locally

```bash
cd frontend

# Set up virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Configure target reasoning engine and directory
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/<REGION>/reasoningEngines/<ENGINE_ID>"
export AGENT_DIRECTORY="app"

# Start the frontend server on port 8080
python main.py
```

Open a web browser and navigate to `http://localhost:8080` (or the configured `$PORT`).

---

## Testing & Evaluation

Run unit and integration test suites:

```bash
uv run pytest tests/unit tests/integration
```

Run agent evaluation with the agents-cli Quality Flywheel:

```bash
agents-cli eval run
```

