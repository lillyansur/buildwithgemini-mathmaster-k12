"""Seed Firestore with math formulas, theorems, and definitions for MathMaster K-12."""

from google.cloud import firestore

FIRESTORE_PROJECT = "qwiklabs-gcp-03-4304884868da"
COLLECTION_NAME = "math_formulas"

FORMULAS = [
    {
        "id": "quadratic_formula",
        "title": "Quadratic Formula",
        "category": "Algebra",
        "grade_level": "High School",
        "formula": "x = (-b ± √(b² - 4ac)) / (2a)",
        "description": "Used to find the roots of any quadratic equation of standard form ax² + bx + c = 0.",
        "steps": [
            "1. Identify the coefficients a, b, and c in ax² + bx + c = 0.",
            "2. Calculate the discriminant: Δ = b² - 4ac.",
            "3. If Δ < 0, there are 2 complex roots; if Δ = 0, 1 real root; if Δ > 0, 2 distinct real roots.",
            "4. Substitute a, b, and Δ into x = (-b ± √Δ) / (2a) and simplify."
        ],
        "example": "For 2x² - 4x - 6 = 0: a=2, b=-4, c=-6. Δ = (-4)² - 4(2)(-6) = 16 + 48 = 64. x = (4 ± 8) / 4 -> x = 3 or x = -1."
    },
    {
        "id": "pythagorean_theorem",
        "title": "Pythagorean Theorem",
        "category": "Geometry",
        "grade_level": "Middle School",
        "formula": "a² + b² = c²",
        "description": "In a right-angled triangle, the square of the hypotenuse (c) is equal to the sum of the squares of the other two sides (a and b).",
        "steps": [
            "1. Confirm the triangle has a 90° right angle.",
            "2. Identify the legs 'a' and 'b' adjacent to the right angle.",
            "3. Identify the hypotenuse 'c' opposite the right angle.",
            "4. Solve for the missing side: c = √(a² + b²) or a = √(c² - b²)."
        ],
        "example": "If legs are a = 3 and b = 4, c = √(3² + 4²) = √(9 + 16) = √25 = 5."
    },
    {
        "id": "slope_intercept_form",
        "title": "Slope-Intercept Form of a Linear Equation",
        "category": "Algebra",
        "grade_level": "Middle School",
        "formula": "y = mx + b",
        "description": "Represents the equation of a straight line where m is the slope and b is the y-intercept (where line crosses the y-axis).",
        "steps": [
            "1. Calculate slope: m = (y₂ - y₁) / (x₂ - x₁).",
            "2. Determine y-intercept: b = y - mx using any known point (x, y).",
            "3. Write the equation y = mx + b."
        ],
        "example": "A line passing through (0, 3) and (2, 7): m = (7-3)/(2-0) = 4/2 = 2. Intercept b = 3. Equation: y = 2x + 3."
    },
    {
        "id": "area_of_circle",
        "title": "Area of a Circle",
        "category": "Geometry",
        "grade_level": "Elementary / Middle School",
        "formula": "A = πr²",
        "description": "Calculates the total two-dimensional surface area inside a circle with radius r.",
        "steps": [
            "1. Measure or identify radius r (if diameter d is given, r = d / 2).",
            "2. Square the radius: r² = r × r.",
            "3. Multiply by π (approximately 3.14159)."
        ],
        "example": "For a circle of radius 7 cm: A = π × 7² = 49π ≈ 153.94 cm²."
    },
    {
        "id": "arithmetic_mean",
        "title": "Arithmetic Mean (Average)",
        "category": "Statistics",
        "grade_level": "Elementary School",
        "formula": "Mean = (∑ x) / n",
        "description": "The central tendency of a collection of numbers, calculated by dividing the sum of values by the total count.",
        "steps": [
            "1. Add all numbers together to find the sum.",
            "2. Count how many numbers are in the set (n).",
            "3. Divide the sum by n."
        ],
        "example": "For dataset {4, 8, 6, 10}: Sum = 4+8+6+10 = 28. Count n = 4. Mean = 28 / 4 = 7."
    }
]

def seed():
    print(f"Connecting to Firestore in project: {FIRESTORE_PROJECT}")
    db = firestore.Client(project=FIRESTORE_PROJECT)
    collection = db.collection(COLLECTION_NAME)

    for item in FORMULAS:
        doc_id = item["id"]
        collection.document(doc_id).set(item)
        print(f"  ✓ Seeded {item['title']} ({doc_id})")

    print(f"\nSuccessfully seeded {len(FORMULAS)} formulas into collection '{COLLECTION_NAME}'.")

if __name__ == "__main__":
    seed()
