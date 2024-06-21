from flask import Flask, request, render_template, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "secrete_key"

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    # note = db.relationship("Note", uselist=False, back_populates="user")

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


with app.app_context():
    db.create_all()


@app.route("/dashboard")
def home():
    if session["username"]:
        user_ = User.query.filter_by(username=session["username"]).first()
        notes = Note.query.filter_by(user_id=session["id"])

        return render_template("dashboard.html", user=user_, notes=notes)

    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        name = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        user_= User.query.filter_by(username=name).first()
        user_e = User.query.filter_by(email=email).first()
        if user_ != None:
            flash('Username already exist.', 'alert')
            return redirect("/register")

        elif user_e != None:
            flash('Email already exist.', 'alert')
            return redirect("/register")
        else:
            new_user = User(username=name, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully.', 'information')

            return redirect("/")
    return render_template("register_page.html")


@app.route("/", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["username"] = user.username
            session["id"] = user.id
            return redirect("/dashboard")
        else:
            flash('Invalid user credentials.', 'error')
            return render_template("login_page.html", error="Invalid user.")

    return render_template("login_page.html")


@app.route("/logout")
def user_logout():
    session.pop("username", None)
    return redirect("/")


@app.route("/add-note", methods=["GET", "POST"])
def add_note():
    if request.method == "POST":
        # breakpoint()
        title = request.form["title"]
        content = request.form["content"]
        timestamp_str = request.form["time"]
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M')
        user_id = session["id"]

        new_note = Note(title=title, content=content, timestamp=timestamp, user_id=user_id)
        db.session.add(new_note)
        db.session.commit()
        flash('Note added successfully.', 'information')
        return redirect("/dashboard")
    return render_template("addNote.html")


@app.route("/update-note/<int:id>", methods=["GET", "POST"])
def update_note(id):
    note = Note.query.filter_by(id=id).first()
    if request.method == "POST":
        note = Note.query.filter_by(id=id).first()
        note.title = request.form["title"]
        note.content = request.form["content"]
        timestamp_str = request.form["time"]
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M')
        note.timestamp = timestamp
        db.session.commit()
        flash('User updated successfully.', 'information')
        return redirect("/dashboard")

    return render_template("updateNote.html", data=note)


@app.route("/delete-note/<int:id>", methods=["GET", "POST"])
def delete_note(id):
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully.', 'danger')
    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(debug=True)
