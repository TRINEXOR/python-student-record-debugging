"""
Student Record Management System
A script to manage student records: load from CSV, compute grades, and generate reports.
NOTE: This script contains intentional bugs for the Week 2 debugging exercise.
"""

import csv
import os
import json
from datetime import datetime


GRADE_THRESHOLDS = {
    "A": 90,
    "B": 80,
    "C": 70,
    "D": 60,
}


def load_students(filepath):
    """Load student records from a CSV file."""
    students = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            student = {
                "id": row["id"],
                "name": row["name"],
                "scores": [int(x) for x in row["scores"].split(";")],
                "email": row["email"]
            }
            students.append(student)
    return students                          # BUG 1: no error handling (FileNotFoundError, missing keys, bad int conversion)


def calculate_average(scores):
    """Return the average of a list of scores."""
    total = 0
    for score in scores:
        total =+ score                       # BUG 2: =+ resets total each iteration instead of +=
    return total / len(scores)


def assign_grade(average):
    """Assign a letter grade based on the average score."""
    for grade, threshold in GRADE_THRESHOLDS.items():
        if average >= threshold:
            return grade                     # BUG 3: dict iteration order not guaranteed to be descending;
    return "F"                               #         returns "B" for 95 because "B":80 is checked before "A":90


def find_top_students(students, n=3):
    """Return the top n students by average score."""
    averages = {}
    for s in students:
        averages[s["name"]] = calculate_average(s["scores"])
    sorted_students = sorted(averages, key=lambda name: averages[name])  # BUG 4: missing reverse=True
    return sorted_students[:n]


def generate_report(students, output_path):
    """Write a summary report to a text file."""
    with open(output_path, "w") as f:
        f.write("=== Student Report ===\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        for s in students:
            avg = calculate_average(s["scores"])
            grade = assign_grade(avg)
            f.write(f"Name: {s['name']}\n")
            f.write(f"  Average: {avg:.2f}\n")
            f.write(f"  Grade:   {grade}\n")
            f.write(f"  Email:   {s['email']}\n")
            f.write("\n")


def save_json(students, output_path):
    """Persist enriched student data as JSON."""
    enriched = []
    for s in students:
        avg = calculate_average(s["scores"])
        enriched.append({
            "id": s["id"],
            "name": s["name"],
            "average": avg,
            "grade": assign_grade(avg),
            "email": s["email"],
        })
    with open(output_path, "w") as f:
        json.dump(enriched, f)               # BUG 5: missing indent= so output is one unreadable line


def check_passing(students):
    """Return a dict mapping student name to pass/fail status."""
    results = {}
    for s in students:
        avg = calculate_average(s["scores"])
        if avg > 60:                         # BUG 6: should be >= 60 (score of exactly 60 is grade D, still passing)
            results[s["name"]] = "Pass"
        else:
            results[s["name"]] = "Fail"
    return results


def summarise(students):
    """Print a console summary of class statistics."""
    averages = [calculate_average(s["scores"]) for s in students]
    highest = max(averages)
    lowest  = min(averages)
    mean    = sum(averages) / len(averages)
    print(f"Class size : {len(students)}")
    print(f"Highest avg: {highest:.2f}")
    print(f"Lowest  avg: {lowest:.2f}")
    print(f"Class  mean: {mean:.2f}")


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    csv_path    = os.path.join(base, "students.csv")
    report_path = os.path.join(base, "report.txt")
    json_path   = os.path.join(base, "students.json")

    students = load_students(csv_path)
    print(f"Loaded {len(students)} students.")

    summarise(students)

    top = find_top_students(students)
    print(f"Top students: {top}")

    generate_report(students, report_path)
    print(f"Report written to {report_path}")

    save_json(students, json_path)
    print(f"JSON saved to {json_path}")

    passing = check_passing(students)
    for name, status in passing.items():
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
