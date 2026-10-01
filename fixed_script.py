"""
Student Record Management System  —  FIXED VERSION
Manages student records: load from CSV, compute grades, generate reports.

Bugs fixed (see debugging_log.md for full details):
  Bug 1 – load_students:      no error handling (FileNotFoundError, KeyError, ValueError)
  Bug 2 – calculate_average:  =+ used instead of +=, so total was reset every iteration
  Bug 3 – assign_grade:       dict iteration not sorted descending; wrong grade returned
  Bug 4 – find_top_students:  sorted() missing reverse=True, returned bottom students
  Bug 5 – save_json:          json.dump missing indent=, output was one unreadable line
  Bug 6 – check_passing:      avg > 60 excluded score of exactly 60 (should be >= 60)
"""

import csv
import os
import json
import sys
from datetime import datetime


# Sorted descending so assign_grade() can return on the first match.
GRADE_THRESHOLDS = [
    ("A", 90),
    ("B", 80),
    ("C", 70),
    ("D", 60),
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_students(filepath: str) -> list:
    """Load student records from a CSV file.

    FIX (Bug 1): Wrapped in try/except blocks to handle:
      * FileNotFoundError  — path does not exist
      * KeyError           — a required column is absent from the CSV
      * ValueError         — a score field cannot be converted to int
    The function now prints a clear message and exits rather than letting
    an unhandled exception crash the programme with a raw traceback.
    """
    if not os.path.exists(filepath):                  # fast, friendly check
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    students = []
    try:
        with open(filepath, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for line_num, row in enumerate(reader, start=2):   # row 1 is the header
                try:
                    student = {
                        "id":     row["id"],
                        "name":   row["name"],
                        "scores": [int(x.strip()) for x in row["scores"].split(";")],
                        "email":  row["email"],
                    }
                    students.append(student)
                except KeyError as exc:
                    print(f"Warning: line {line_num} missing column {exc} — skipped.",
                          file=sys.stderr)
                except ValueError as exc:
                    print(f"Warning: line {line_num} has non-integer score ({exc}) — skipped.",
                          file=sys.stderr)
    except OSError as exc:
        print(f"Error reading '{filepath}': {exc}", file=sys.stderr)
        sys.exit(1)

    return students


# ---------------------------------------------------------------------------
# Calculation helpers
# ---------------------------------------------------------------------------

def calculate_average(scores: list) -> float:
    """Return the arithmetic mean of a list of scores.

    FIX (Bug 2): Changed `total =+ score` to `total += score`.
    The original operator =+ is legal Python but means `total = (+score)`,
    which silently *replaced* the running total with the current score on
    every iteration. The result was always the last score in the list, not
    the sum — and averaging it against len(scores) produced absurdly low
    values (e.g. 24.00 for Eva instead of 96.50).
    """
    if not scores:
        return 0.0
    total = 0
    for score in scores:
        total += score          # FIX: was `total =+ score`
    return total / len(scores)


def assign_grade(average: float) -> str:
    """Return a letter grade for a numeric average.

    FIX (Bug 3): The original code iterated over a plain dict whose key
    order in CPython 3.7+ is insertion order — A, B, C, D — so for an
    average of 95 the condition `average >= 80` (B) was checked *before*
    `average >= 90` (A) and returned "B" incorrectly.

    The fix replaces the dict with a list of (grade, threshold) tuples
    sorted highest-first. The function now returns on the first threshold
    the average meets, which is always the correct (highest) grade.
    """
    for grade, threshold in GRADE_THRESHOLDS:   # list is sorted A→B→C→D (90→80→70→60)
        if average >= threshold:
            return grade
    return "F"


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def find_top_students(students: list, n: int = 3) -> list:
    """Return the names of the top n students by average score.

    FIX (Bug 4): sorted() was missing reverse=True, so it returned the
    students with the *lowest* averages (ascending order). Adding
    reverse=True correctly returns the highest scorers first.
    """
    averages = {s["name"]: calculate_average(s["scores"]) for s in students}
    sorted_names = sorted(averages, key=lambda name: averages[name], reverse=True)  # FIX
    return sorted_names[:n]


def generate_report(students: list, output_path: str) -> None:
    """Write a human-readable summary report to a text file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=== Student Report ===\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for s in students:
            avg   = calculate_average(s["scores"])
            grade = assign_grade(avg)
            f.write(f"Name:    {s['name']}\n")
            f.write(f"  Average: {avg:.2f}\n")
            f.write(f"  Grade:   {grade}\n")
            f.write(f"  Email:   {s['email']}\n\n")


def save_json(students: list, output_path: str) -> None:
    """Persist enriched student data as pretty-printed JSON.

    FIX (Bug 5): json.dump was called without indent=, so the entire
    dataset was written as one long line, making the file unreadable in
    any text editor. Adding indent=2 produces properly formatted JSON.
    """
    enriched = []
    for s in students:
        avg = calculate_average(s["scores"])
        enriched.append({
            "id":      s["id"],
            "name":    s["name"],
            "average": round(avg, 2),
            "grade":   assign_grade(avg),
            "email":   s["email"],
        })
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)    # FIX: was json.dump(enriched, f)


def check_passing(students: list) -> dict:
    """Return a dict mapping each student's name to 'Pass' or 'Fail'.

    FIX (Bug 6): The original condition `avg > 60` used strict greater-than,
    so a student with an exact average of 60 (grade D, still a passing grade)
    was incorrectly marked as 'Fail'. Changed to `avg >= 60`.
    """
    results = {}
    for s in students:
        avg = calculate_average(s["scores"])
        results[s["name"]] = "Pass" if avg >= 60 else "Fail"   # FIX: was `avg > 60`
    return results


def summarise(students: list) -> None:
    """Print class-level statistics to the console."""
    if not students:
        print("No student data available.")
        return
    averages = [calculate_average(s["scores"]) for s in students]
    print(f"Class size : {len(students)}")
    print(f"Highest avg: {max(averages):.2f}")
    print(f"Lowest  avg: {min(averages):.2f}")
    print(f"Class  mean: {sum(averages) / len(averages):.2f}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    base        = os.path.dirname(os.path.abspath(__file__))
    csv_path    = os.path.join(base, "students.csv")
    report_path = os.path.join(base, "report.txt")
    json_path   = os.path.join(base, "students.json")

    students = load_students(csv_path)
    if not students:
        print("No valid student records found. Exiting.", file=sys.stderr)
        sys.exit(1)
    print(f"Loaded {len(students)} students.")

    summarise(students)

    top = find_top_students(students)
    print(f"Top students: {top}")

    generate_report(students, report_path)
    print(f"Report written to {report_path}")

    save_json(students, json_path)
    print(f"JSON saved to {json_path}")

    passing = check_passing(students)
    print("\nPass/Fail results:")
    for name, status in passing.items():
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
