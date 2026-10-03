from flask import Flask, jsonify, render_template, request
import heapq

app = Flask(__name__)


def time_to_minutes(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


def minutes_to_time(minutes):
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def priority_queue(vehicles):
    heap = []
    for v in vehicles:
        heapq.heappush(
            heap,
            (-int(v["urgency"]), time_to_minutes(v["departure"]),
             int(v["duration"]), v["id"], v)
        )
    ordered = []
    while heap:
        ordered.append(heapq.heappop(heap)[-1])
    return ordered


def greedy_schedule(vehicles, slots):
    used = set()
    result = []
    for v in vehicles:
        chosen = None
        for slot in slots:
            if slot["id"] in used:
                continue
            start = time_to_minutes(slot["start"])
            end = start + int(v["duration"])
            slot_end = time_to_minutes(slot["end"])
            deadline = time_to_minutes(v["departure"])
            if end <= slot_end and end <= deadline:
                chosen = {
                    "vehicle": v["id"],
                    "urgency": int(v["urgency"]),
                    "departure": v["departure"],
                    "duration": int(v["duration"]),
                    "slot": slot["id"],
                    "start_time": slot["start"],
                    "end_time": minutes_to_time(end),
                    "status": "Scheduled",
                }
                break
        if chosen:
            used.add(chosen["slot"])
            result.append(chosen)
        else:
            result.append({
                "vehicle": v["id"], "urgency": int(v["urgency"]),
                "departure": v["departure"], "duration": int(v["duration"]),
                "slot": "No Slot", "start_time": "-", "end_time": "-",
                "status": "Waiting"
            })
    return result


def run_scheduler(vehicles):
    slots = [
        {"id": "S1", "start": "09:00", "end": "09:30"},
        {"id": "S2", "start": "09:30", "end": "10:00"},
        {"id": "S3", "start": "10:00", "end": "10:30"},
        {"id": "S4", "start": "10:30", "end": "11:00"},
        {"id": "S5", "start": "11:00", "end": "11:30"},
    ]
    ordered = priority_queue(vehicles)
    schedule = greedy_schedule(ordered, slots)
    return ordered, schedule


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/schedule", methods=["POST"])
def schedule():
    data = request.get_json(silent=True) or {}
    vehicles = data.get("vehicles", [])
    if not vehicles:
        return jsonify({"error": "No vehicles provided"}), 400
    ordered, result = run_scheduler(vehicles)
    return jsonify({
        "priority_queue": ordered,
        "schedule": result,
        "summary": {
            "vehicles": len(ordered),
            "scheduled": sum(x["status"] == "Scheduled" for x in result),
            "waiting": sum(x["status"] == "Waiting" for x in result),
            "slots": 5,
        }
    })


if __name__ == "__main__":
    app.run(debug=True)
