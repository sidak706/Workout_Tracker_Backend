from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from collections import defaultdict


app = Flask(__name__)
CORS(app)  # allows frontend (GitHub Pages) to talk to backend

DB_NAME = "workout-tracker.db"

def create_exercise_table():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS Exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                muscle_group TEXT
            )
        """)
        conn.commit()

def create_workout_table():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS Workout (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                muscle_group TEXT,
                sets INTEGER NOT NULL,
                reps INTEGER NOT NULL,
                weight REAL NOT NULL,
                date TEXT NOT NULL,
                loggedAt TEXT NOT NULL
            )
        """)
        conn.commit()

def init_db():
    create_workout_table()
    create_exercise_table()


@app.route("/new_exer", methods=["POST"])
def add_exer():
    data = request.get_json()
    name= data.get("name")
    muscle_group = data.get("muscle_group")

    

    if not name:
        return jsonify({"status": "error", "message": "Exercise name is required"}), 400

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM Exercises WHERE LOWER(name) = LOWER(?)", (name,))
            if c.fetchone():
                return jsonify({"status": "error", "message": f"Exercise {name} already exists"}), 409
            
            c.execute("""
                INSERT INTO Exercises (name, muscle_group)
                VALUES (?, ?)
            """, (name, muscle_group))
            conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": f"Exercise '{name}' already exists"}), 409

    return jsonify({"status": "success", "message": f"Added exercise '{name}'"})


@app.route("/get_last_5", methods=["GET"])
def get_last_5(): 
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT name, muscle_group
            FROM Exercises
            ORDER BY id DESC
            LIMIT 5
        """)
        rows = c.fetchall()

    exercises = [
        {"name": r[0], "muscle_group": r[1]}
        for r in rows
    ]
    print(exercises)
    return jsonify(exercises)

@app.route("/get_groups", methods=["GET"])
def get_groups():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT(muscle_group)
            FROM Exercises
        """)
        rows = c.fetchall()

    groups = [r[0] for r in rows if r[0] is not None]

    print(groups)

    return groups


@app.route('/')
def home():
    return "Flask backend is running!"

@app.route('/test', methods=['POST'])
def test():
    data = request.get_json()
    print("Received from frontend:", data)
    return jsonify({"message": "Data received successfully!", "data": data})

@app.route("/add_workout", methods=["POST"])
def add_workout():
    data = request.get_json()
    print(data)
    name = data.get("name")
    muscle_group = data.get("muscle_group")  # optional
    date = data["date"]
    sets = data["sets"]
    reps = data["reps"]
    weight = data["weight"]
    loggedAt = data["loggedAt"]

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO Workout (name, muscle_group, sets, reps, weight, date, loggedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, muscle_group, sets, reps, weight, date, loggedAt))
        conn.commit()

    return jsonify({"success": True})



@app.route("/get_all_exer", methods=["GET"])
def get_all_exer():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT name FROM Exercises
                """)
        rows = c.fetchall()

    all_exers = [
        {
            "name": r[0]
        }
        for r in rows
    ]

    return all_exers


@app.route("/get_last5_workouts", methods=["GET"])
def get_last5_workouts():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT name, date, sets, reps, weight, loggedAt
            FROM Workout
            ORDER BY id DESC
            LIMIT 5
                  """)
        rows = c.fetchall()

    last5 = [
        {
            "name": r[0],
            "date": r[1],
            "sets": r[2],
            "reps": r[3],
            "weight": r[4],
            "loggedAt": r[5]
        }
        for r in rows
    ]

    print(f"Last 5: {last5}")
    return jsonify(last5)

# DELETE FROM WORKOUT where Workout.id = id
@app.route("/delete_workout", methods=["DELETE"])
def delete_workout():
    data = request.get_json()
    id = data["id"]
    return 0


# DELETE FROM Exercise where Exercise.id = id
@app.route("/delete_exercises", methods=["DELETE"])
def delete_exercises():
    data = request.get_json()
    names = data.get("names", [])
    print("Deleting exercises:", names)

    if not names:
        return jsonify({"status": "error", "message": "No exercises provided"}), 400

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # Delete workouts linked to those exercises
            c.executemany("""
                DELETE FROM Workout
                WHERE name = ?
            """, [(name,) for name in names])

            # Delete the exercises themselves
            c.executemany("""
                DELETE FROM Exercises
                WHERE name = ?
            """, [(name,) for name in names])

            conn.commit()

        return jsonify({"status": "success", "message": f"Deleted {len(names)} exercise(s)"})

    except Exception as e:
        print("Error while deleting:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# @app.route("/get_progress_w_name", methods=["GET"])
# def get_progress_w_name():
#     name = request.args.get("name")
    
#     with sqlite3.connect(DB_NAME) as conn:
#         c = conn.cursor()
#         c.execute("""
#             SELECT date, sets, reps, weight, loggedAt
#             FROM Workout
#             WHERE name = (?)
#             ORDER BY date DESC
#                   """, (name, ))
#         rows = c.fetchall()

#     # Group by date
#     grouped = defaultdict(list)
#     for date, reps, weight in rows:
#         grouped[date].append({"reps": reps, "weight": weight})

#     progress = [{"date": date, "sets": sets} for date, sets in grouped.items()]

#     print(progress)

#     return jsonify(progress)

@app.route("/get_progress_w_name", methods=["GET"])
def get_progress_w_name():
    name = request.args.get("name")
    rows = []
    
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT date, sets, reps, weight
            FROM Workout
            WHERE name = ?
            ORDER BY date ASC
        """, (name,))
        rows = c.fetchall()

    progress = defaultdict(list)

    for date, sets, reps, weight in rows:
        progress[date].append((sets, reps, weight))

    # Convert defaultdict back to normal dict if you want JSON safe
    progress = dict(progress)

    return jsonify(progress)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
