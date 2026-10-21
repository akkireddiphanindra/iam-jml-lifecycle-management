
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
app.secret_key = "jml-learning-demo-key"

DB_PATH = Path(__file__).with_name("jml_demo.db")

DEPARTMENTS = ["IT", "HR", "Finance", "Security"]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active',
                access TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT NOT NULL
            )
        """)


def log_event(conn, employee_name, action, details):
    conn.execute(
        """INSERT INTO audit_logs
           (timestamp, employee_name, action, details)
           VALUES (?, ?, ?, ?)""",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
         employee_name, action, details)
    )


def department_access(department):
    return f"{department} Demo Access"


@app.route("/")
def index():
    with get_db() as conn:
        employees = conn.execute(
            "SELECT * FROM employees ORDER BY id DESC"
        ).fetchall()

    return render_template(
        "index.html",
        employees=employees,
        departments=DEPARTMENTS
    )


@app.route("/joiner", methods=["POST"])
def joiner():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    department = request.form.get("department", "").strip()

    if not name or not email or department not in DEPARTMENTS:
        flash("Enter valid employee details.", "error")
        return redirect(url_for("index"))

    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO employees
                   (name, email, department, status, access)
                   VALUES (?, ?, ?, 'Active', ?)""",
                (name, email, department, department_access(department))
            )
            log_event(
                conn, name, "JOINER",
                f"Employee created; simulated access assigned: "
                f"{department_access(department)}"
            )
        flash("Employee added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("That email already exists.", "error")

    return redirect(url_for("index"))


@app.route("/mover/<int:employee_id>", methods=["POST"])
def mover(employee_id):
    department = request.form.get("department", "").strip()

    if department not in DEPARTMENTS:
        flash("Select a valid department.", "error")
        return redirect(url_for("index"))

    with get_db() as conn:
        employee = conn.execute(
            "SELECT * FROM employees WHERE id = ? AND status = 'Active'",
            (employee_id,)
        ).fetchone()

        if employee:
            old_department = employee["department"]
            conn.execute(
                "UPDATE employees SET department = ?, access = ? WHERE id = ?",
                (department, department_access(department), employee_id)
            )
            log_event(
                conn, employee["name"], "MOVER",
                f"Department changed from {old_department} to {department}; "
                f"simulated access updated."
            )
            flash("Employee department updated.", "success")

    return redirect(url_for("index"))


@app.route("/leaver/<int:employee_id>", methods=["POST"])
def leaver(employee_id):
    with get_db() as conn:
        employee = conn.execute(
            "SELECT * FROM employees WHERE id = ? AND status = 'Active'",
            (employee_id,)
        ).fetchone()

        if employee:
            conn.execute(
                "UPDATE employees SET status = 'Inactive', access = ? WHERE id = ?",
                ("Revoked (simulated)", employee_id)
            )
            log_event(
                conn, employee["name"], "LEAVER",
                "Employee deactivated; access revocation recorded as simulated."
            )
            flash("Employee deactivated.", "success")

    return redirect(url_for("index"))


@app.route("/audit")
def audit():
    with get_db() as conn:
        audit_logs = conn.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC"
        ).fetchall()

    return render_template("audit.html", audit_logs=audit_logs)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
