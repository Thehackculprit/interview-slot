from flask import Flask, render_template, request, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = "supersecretkey"

# --------------------------
# Google Sheets Setup
# --------------------------
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("booking slots").sheet1
    return sheet

# --------------------------
# Helper Functions
# --------------------------
def get_all_slots():
    sheet = get_sheet()
    return sheet.get_all_records()

def add_slot_to_sheet(date, time):
    sheet = get_sheet()
    slots = sheet.get_all_records()
    new_id = len(slots) + 1
    sheet.append_row([new_id, date, time, 0, "", "", ""])

def delete_slot_in_sheet(slot_id):
    sheet = get_sheet()
    rows = sheet.get_all_records()
    for i, row in enumerate(rows, start=2):
        if int(row["id"]) == int(slot_id):
            sheet.delete_rows(i)
            break

def book_slot_in_sheet(slot_id, name, email, phone):
    sheet = get_sheet()
    rows = sheet.get_all_records()
    for i, row in enumerate(rows, start=2):
        if int(row["id"]) == int(slot_id):
            sheet.update_cell(i, 4, 1)  # mark as booked
            sheet.update_cell(i, 5, name)
            sheet.update_cell(i, 6, email)
            sheet.update_cell(i, 7, phone)
            break

# --------------------------
# Routes
# --------------------------
@app.route("/", methods=["GET"])
def index():
    slots = get_all_slots()
    return render_template("index.html", slots=slots)

@app.route("/book/<int:slot_id>", methods=["POST"])
def book_slot(slot_id):
    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    book_slot_in_sheet(slot_id, name, email, phone)
    return redirect("/")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin@123":
            session["admin"] = True
            return redirect("/admin")
        return "Invalid credentials"
    return render_template("admin_login.html")

@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    slots = get_all_slots()
    return render_template("admin_dashboard.html", slots=slots)

@app.route("/admin/add_slot", methods=["POST"])
def add_slot():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    date = request.form["date"]
    time = request.form["time"]
    add_slot_to_sheet(date, time)
    return redirect("/admin")

@app.route("/admin/delete_slot/<int:slot_id>", methods=["POST"])
def delete_slot(slot_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    delete_slot_in_sheet(slot_id)
    return redirect("/admin")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/")

# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
