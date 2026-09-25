# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


MODEL = "gemini-3.6-flash"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    q = query.lower()
    if "sf" in q or "san francisco" in q:
        tz_identifier = "America/Los_Angeles"
    elif "austin" in q or "texas" in q:
        tz_identifier = "America/Chicago"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from google.cloud import firestore

FIRESTORE_PROJECT = "qwiklabs-gcp-03-4304884868da"
COLLECTION_NAME = "math_formulas"

# Initialize Firestore client with the pinned project ID string
db = firestore.Client(project=FIRESTORE_PROJECT)


def search_math_formulas(query: str = "", category: str = "", grade_level: str = "") -> list[dict]:
    """Search or list mathematical formulas, theorems, and definitions in the formula catalog.

    Args:
        query: Optional search keyword to look for in formula title or description (e.g. 'quadratic', 'triangle', 'slope').
        category: Optional category filter (e.g. 'Algebra', 'Geometry', 'Statistics').
        grade_level: Optional grade filter (e.g. 'Elementary School', 'Middle School', 'High School').

    Returns:
        A list of matching formula dictionaries containing formula, steps, and examples.
    """
    col = db.collection(COLLECTION_NAME)
    docs = col.stream()
    results = []

    q_lower = query.lower().strip()
    cat_lower = category.lower().strip()
    grade_lower = grade_level.lower().strip()

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        # Apply category filter if specified
        if cat_lower and cat_lower not in data.get("category", "").lower():
            continue

        # Apply grade filter if specified
        if grade_lower and grade_lower not in data.get("grade_level", "").lower():
            continue

        # Apply keyword search filter if specified
        if q_lower:
            searchable_text = f"{data.get('title', '')} {data.get('formula', '')} {data.get('description', '')}".lower()
            if q_lower not in searchable_text:
                continue

        results.append(data)

    return results


def get_formula_details(formula_id: str) -> dict:
    """Retrieve detailed information, derivation steps, and examples for a specific formula by ID.

    Args:
        formula_id: The unique identifier of the formula (e.g. 'quadratic_formula', 'pythagorean_theorem').

    Returns:
        The formula details dictionary, or an error message if not found.
    """
    doc_ref = db.collection(COLLECTION_NAME).document(formula_id.strip())
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": f"Formula with ID '{formula_id}' not found."}
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def save_math_formula(
    formula_id: str,
    title: str,
    category: str,
    grade_level: str,
    formula: str,
    description: str,
    steps: list[str],
    example: str,
) -> dict:
    """Save or update a math formula, theorem, or definition in the formula catalog.

    Args:
        formula_id: Unique slug identifier for the formula (e.g. 'distance_formula').
        title: Human-readable title of the formula (e.g. 'Distance Formula').
        category: Subject area (e.g. 'Algebra', 'Geometry', 'Trigonometry', 'Calculus').
        grade_level: Target grade level (e.g. 'Elementary School', 'Middle School', 'High School').
        formula: Mathematical expression (e.g. 'd = √((x₂ - x₁)² + (y₂ - y₁))').
        description: Clear explanation of what the formula represents and when to use it.
        steps: Step-by-step instructions on how to apply and derive solutions with this formula.
        example: A worked-out sample problem showing the calculation.

    Returns:
        A confirmation dictionary indicating successful storage.
    """
    clean_id = formula_id.strip().lower().replace(" ", "_")
    doc_ref = db.collection(COLLECTION_NAME).document(clean_id)
    payload = {
        "id": clean_id,
        "title": title.strip(),
        "category": category.strip(),
        "grade_level": grade_level.strip(),
        "formula": formula.strip(),
        "description": description.strip(),
        "steps": steps,
        "example": example.strip(),
    }
    doc_ref.set(payload)
    return {"status": "success", "message": f"Saved formula '{title}' with ID '{clean_id}'.", "data": payload}


import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)


def solve_and_verify_math(expression: str, variable: str = "x") -> dict:
    """Solves algebraic equations, simplifies expressions, factors polynomials, and computes exact values.

    Use this tool whenever solving an equation or calculating an expression to ensure 100% mathematical accuracy.

    Args:
        expression: The mathematical expression or equation to solve (e.g. '2*x^2 - 4*x - 6 = 0', '3*x + 5 = 20', 'x^2 + 5*x + 6', '(1/2) + (3/4)').
        variable: The variable to solve for (defaults to 'x').

    Returns:
        A dictionary containing the parsed expression, solutions, factored form, expanded form, and numerical evaluation.
    """
    try:
        # Preprocessing common user formats (e.g. ^ for power, = for equations)
        cleaned_expr = expression.strip()
        transformations = standard_transformations + (implicit_multiplication_application, convert_xor)
        sym_var = sp.Symbol(variable.strip())

        if "=" in cleaned_expr:
            lhs_str, rhs_str = cleaned_expr.split("=", 1)
            lhs = parse_expr(lhs_str.strip(), transformations=transformations)
            rhs = parse_expr(rhs_str.strip(), transformations=transformations)
            eq = sp.Eq(lhs, rhs)
            diff_expr = lhs - rhs
            solutions = sp.solve(diff_expr, sym_var)
            
            # Format solutions
            exact_roots = [str(sol) for sol in solutions]
            decimal_roots = []
            for sol in solutions:
                try:
                    decimal_roots.append(float(sol.evalf()))
                except Exception:
                    decimal_roots.append(None)

            return {
                "type": "equation",
                "equation": str(eq),
                "variable": str(sym_var),
                "exact_solutions": exact_roots,
                "decimal_solutions": decimal_roots,
                "simplified_form": str(sp.simplify(diff_expr)) + " = 0",
                "factored_form": str(sp.factor(diff_expr)) + " = 0",
                "status": "success",
            }
        else:
            expr = parse_expr(cleaned_expr, transformations=transformations)
            simplified = sp.simplify(expr)
            factored = sp.factor(expr)
            expanded = sp.expand(expr)
            
            num_val = None
            try:
                num_val = float(expr.evalf())
            except Exception:
                pass

            return {
                "type": "expression",
                "expression": str(expr),
                "simplified": str(simplified),
                "factored": str(factored),
                "expanded": str(expanded),
                "numerical_value": num_val,
                "status": "success",
            }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Could not solve expression '{expression}': {str(e)}",
            "suggestion": "Please check syntax. Use '*' for multiplication and standard variable names.",
        }


import io
import uuid
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless server
import matplotlib.pyplot as plt
import numpy as np
from google.cloud import storage

GCS_BUCKET_NAME = f"mathmaster-k12-assets-{FIRESTORE_PROJECT}"
storage_client = storage.Client(project=FIRESTORE_PROJECT)


def generate_and_save_plot(
    function_expr: str,
    x_min: float = -10.0,
    x_max: float = 10.0,
    title: str = "",
) -> dict:
    """Generates a 2D mathematical plot for a function expression and saves it to Cloud Storage as a public image.

    Call this tool whenever a student asks for a graph, plot, visual representation, or when solving linear, quadratic, or polynomial functions.

    Args:
        function_expr: Mathematical function in terms of x (e.g. '2*x + 3', 'x^2 - 4*x - 6', 'sin(x)', '2*x^2 - 5').
        x_min: Minimum value of x on the horizontal axis (default -10.0).
        x_max: Maximum value of x on the horizontal axis (default 10.0).
        title: Optional custom title for the plot.

    Returns:
        A dictionary containing the public image URL, markdown image snippet, and function details.
    """
    try:
        # Parse expression using sympy
        cleaned_expr = function_expr.strip()
        transformations = standard_transformations + (implicit_multiplication_application, convert_xor)
        sym_x = sp.Symbol("x")
        
        # If user passed "y = ...", strip "y ="
        if "=" in cleaned_expr:
            parts = cleaned_expr.split("=", 1)
            cleaned_expr = parts[1].strip()

        parsed = parse_expr(cleaned_expr, transformations=transformations)
        f_lambdified = sp.lambdify(sym_x, parsed, modules=["numpy"])

        # Generate points
        x_vals = np.linspace(float(x_min), float(x_max), 500)
        y_vals = f_lambdified(x_vals)

        # Handle scalar constant output from lambdify
        if np.isscalar(y_vals) or y_vals.shape == ():
            y_vals = np.full_like(x_vals, float(y_vals))

        # Create plot
        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
        ax.plot(x_vals, y_vals, label=f"y = {cleaned_expr}", color="#1a73e8", linewidth=2.5)
        ax.axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
        ax.axvline(0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
        ax.grid(True, linestyle=":", alpha=0.6)
        
        plot_title = title if title else f"Plot of y = {cleaned_expr}"
        ax.set_title(plot_title, fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("x", fontsize=12)
        ax.set_ylabel("y", fontsize=12)
        ax.legend(loc="best", frameon=True)

        # Buffer to PNG
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)

        # Upload to Google Cloud Storage
        filename = f"plots/plot_{uuid.uuid4().hex[:10]}.png"
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_file(buf, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "function": cleaned_expr,
            "x_range": [x_min, x_max],
            "image_url": public_url,
            "markdown": f"![{plot_title}]({public_url})",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Could not generate plot for '{function_expr}': {str(e)}",
            "suggestion": "Check syntax. For example, use 'x^2' or '2*x + 1'.",
        }


PRACTICE_COLLECTION = "practice_problems"
PROGRESS_COLLECTION = "student_progress"


def generate_practice_problem(
    topic: str,
    grade_level: str = "Middle School",
    difficulty: str = "medium",
) -> dict:
    """Generates a practice problem tailored to a specific topic and grade level, saving it in the Problem Bank.

    Call this tool when a student wants to practice, test their understanding, or solve an exercise.

    Args:
        topic: The math topic (e.g. 'linear equations', 'pythagorean theorem', 'quadratic equations', 'fractions').
        grade_level: Target grade level ('Elementary School', 'Middle School', 'High School').
        difficulty: Difficulty level ('easy', 'medium', 'hard').

    Returns:
        A dictionary containing the problem_id, question, hints, and instructions for the student (solution is kept server-side).
    """
    import random
    problem_id = f"prob_{uuid.uuid4().hex[:8]}"
    topic_clean = topic.strip().lower()

    # Built-in generator templates with deterministic math verification
    if "pythagor" in topic_clean or "triangle" in topic_clean:
        triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (9, 12, 15), (8, 15, 17)]
        a, b, c = random.choice(triples)
        question = f"A right triangle has legs of length a = {a} and b = {b}. What is the length of the hypotenuse c?"
        solution_value = str(c)
        derivation = [
            f"1. Use the Pythagorean Theorem: a² + b² = c²",
            f"2. Substitute legs: {a}² + {b}² = {a*a} + {b*b} = {c*c}",
            f"3. Take the square root: c = √{c*c} = {c}",
        ]
        hints = ["Remember the formula a² + b² = c².", f"Calculate {a}² + {b}² first."]
    elif "linear" in topic_clean or "slope" in topic_clean:
        m = random.randint(2, 6)
        x_val = random.randint(1, 9)
        b = random.randint(1, 10)
        c = m * x_val + b
        question = f"Solve for x: {m}x + {b} = {c}"
        solution_value = str(x_val)
        derivation = [
            f"1. Subtract {b} from both sides: {m}x = {c} - {b} = {c - b}",
            f"2. Divide both sides by {m}: x = {c - b} / {m} = {x_val}",
        ]
        hints = [f"First isolate the term with x by subtracting {b} from {c}.", f"Then divide by {m}."]
    elif "quadratic" in topic_clean:
        r1 = random.randint(1, 5)
        r2 = random.randint(-4, -1)
        # (x - r1)(x - r2) = x^2 - (r1+r2)x + r1*r2
        b_coeff = -(r1 + r2)
        c_coeff = r1 * r2
        b_sign = "+" if b_coeff >= 0 else "-"
        c_sign = "+" if c_coeff >= 0 else "-"
        question = f"Find the roots of the quadratic equation: x² {b_sign} {abs(b_coeff)}x {c_sign} {abs(c_coeff)} = 0"
        solution_value = f"{min(r1, r2)}, {max(r1, r2)}"
        derivation = [
            f"1. Factor the quadratic: (x - {r1})(x - ({r2})) = (x - {r1})(x + {abs(r2)}) = 0",
            f"2. Set each factor to 0 to find roots: x = {r1} or x = {r2}",
        ]
        hints = ["Try factoring into two binomials (x - p)(x - q) = 0.", "Or use the quadratic formula with a=1."]
    else:
        # General arithmetic / fractions / pre-algebra
        num1 = random.randint(10, 50)
        num2 = random.randint(2, 9)
        prod = num1 * num2
        question = f"Find x in the equation: {num2}x = {prod}"
        solution_value = str(num1)
        derivation = [f"1. Divide both sides by {num2}: x = {prod} / {num2} = {num1}"]
        hints = [f"Divide {prod} by {num2} to solve for x."]

    problem_doc = {
        "problem_id": problem_id,
        "topic": topic,
        "grade_level": grade_level,
        "difficulty": difficulty,
        "question": question,
        "solution_value": solution_value,
        "derivation": derivation,
        "hints": hints,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    # Save to Firestore Problem Bank
    db.collection(PRACTICE_COLLECTION).document(problem_id).set(problem_doc)

    return {
        "status": "success",
        "problem_id": problem_id,
        "topic": topic,
        "grade_level": grade_level,
        "difficulty": difficulty,
        "question": question,
        "hints": hints,
        "note": "Present this question and hints to the student. When they answer, verify their answer or use submit_problem_attempt.",
    }


def record_student_attempt(
    problem_id: str,
    student_answer: str,
    is_correct: bool,
    student_id: str = "default_student",
) -> dict:
    """Records a student's answer attempt and updates their mastery progress in Firestore.

    Args:
        problem_id: The ID of the practice problem attempted.
        student_answer: What the student submitted.
        is_correct: Whether the student got it right.
        student_id: Student identifier (defaults to 'default_student').

    Returns:
        Summary of student attempt and cumulative topic score.
    """
    attempt_id = f"attempt_{uuid.uuid4().hex[:8]}"
    attempt_doc = {
        "attempt_id": attempt_id,
        "problem_id": problem_id,
        "student_id": student_id,
        "student_answer": student_answer,
        "is_correct": is_correct,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    db.collection(PROGRESS_COLLECTION).document(attempt_id).set(attempt_doc)

    # Calculate cumulative stats for this student
    attempts_ref = db.collection(PROGRESS_COLLECTION).where("student_id", "==", student_id).stream()
    total = 0
    correct = 0
    for doc in attempts_ref:
        d = doc.to_dict()
        total += 1
        if d.get("is_correct"):
            correct += 1

    accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0

    return {
        "status": "success",
        "attempt_id": attempt_id,
        "is_correct": is_correct,
        "total_attempted": total,
        "total_correct": correct,
        "accuracy_pct": accuracy,
    }


from google.adk.tools import ToolContext
from google import genai

HARDCODED_BUCKET_NAME = "mathmaster-k12-assets-qwiklabs-gcp-03-4304884868da"
IMAGE_MODEL = "gemini-3.1-flash-lite-image"
genai_image_client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT, location="global")


async def generate_math_illustration(
    prompt: str,
    tool_context: ToolContext,
    title: str = "Math Illustration",
) -> dict:
    """Generates an educational math illustration or diagram using gemini-3.1-flash-lite-image.

    The generated image is saved to the session artifacts panel and uploaded directly to public Cloud Storage.

    Args:
        prompt: Descriptive prompt for the math diagram or illustration (e.g., 'A clean 2D geometric diagram of a right-angled triangle showing sides a, b and hypotenuse c with right angle indicator').
        tool_context: ADK ToolContext used for saving the artifact into the Playground session.
        title: Descriptive title for the image.

    Returns:
        A dictionary containing the public Cloud Storage HTTPS URL, artifact filename, and markdown embed string.
    """
    try:
        # Generate image using gemini-3.1-flash-lite-image via generate_content
        full_prompt = (
            f"Generate an educational, clear math textbook illustration: {prompt}. "
            "Clean vector-like lines, clear mathematical labels, white background, high contrast, visually accurate."
        )
        response = genai_image_client.models.generate_content(
            model=IMAGE_MODEL,
            contents=full_prompt,
        )

        image_bytes = None
        mime_type = "image/jpeg"

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

        if not image_bytes:
            return {
                "status": "error",
                "error_message": "Model did not return image bytes in response.",
            }

        # (1) Save artifact in ToolContext for Playground Artifacts panel
        ext = "png" if "png" in mime_type else "jpg"
        artifact_filename = f"math_diagram_{uuid.uuid4().hex[:8]}.{ext}"
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        try:
            await tool_context.save_artifact(
                filename=artifact_filename,
                artifact=artifact_part,
                custom_metadata={"title": title, "prompt": prompt},
            )
        except Exception as art_err:
            print(f"Warning: could not save artifact to tool_context: {art_err}")

        # (2) Upload image bytes directly to the public Cloud Storage bucket
        gcs_object_name = f"illustrations/{artifact_filename}"
        bucket = storage_client.bucket(HARDCODED_BUCKET_NAME)
        blob = bucket.blob(gcs_object_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{HARDCODED_BUCKET_NAME}/{gcs_object_name}"

        return {
            "status": "success",
            "title": title,
            "artifact_filename": artifact_filename,
            "image_url": public_url,
            "markdown": f"![{title}]({public_url})",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to generate illustration: {str(e)}",
        }


from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are MathMaster K-12, an encouraging and expert math tutor helping students solve "
        "comprehensive math problems with clear, step-by-step derivations."
    ),
    workflow_description=(
        "When solving equations, factoring polynomials, or computing expressions, ALWAYS call "
        "`solve_and_verify_math` to verify the exact mathematical answer.\n"
        "When explaining a solution, consult the formula catalog using `search_math_formulas` "
        "or `get_formula_details` for reference definitions and standard steps.\n"
        "When a student asks for a graph or visual function plot, call `generate_and_save_plot`.\n"
        "When a student asks for a geometric diagram or illustration, call `generate_math_illustration`.\n"
        "When a student wants to practice or test their knowledge, call `generate_practice_problem`.\n"
        "When the student submits an answer to a practice problem, verify it, explain the result, "
        "and record their progress using `record_student_attempt`.\n"
        "Break down math solutions into numbered, step-by-step derivations showing how each step leads to the next.\n"
        "Analyze the request and return structured UI when appropriate."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image or plot tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    tools=[
        solve_and_verify_math,
        generate_and_save_plot,
        generate_math_illustration,
        generate_practice_problem,
        record_student_attempt,
        search_math_formulas,
        get_formula_details,
        save_math_formula,
    ],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
