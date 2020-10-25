import json

from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, RadioField
from wtforms.validators import InputRequired

from dataset.data import days
from defaults import TEACHERS_COUNT_ON_MAIN
from utils import get_random_set

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['WTF_CSRF_ENABLED'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class BookingForm(FlaskForm):
    clientWeekday = HiddenField()
    clientTime = HiddenField()
    clientTeacher = HiddenField()
    clientName = StringField(validators=[InputRequired(), ])
    clientPhone = StringField(validators=[InputRequired(), ])


class RequestForm(FlaskForm):
    goal = RadioField(choices=["travel", "study", "work", "relocate"])
    time = RadioField(choices=["1-2", "3-5", "5-7", "7-10"])
    clientName = StringField(validators=[InputRequired(), ])
    clientPhone = StringField(validators=[InputRequired(), ])


teachers_goals_association = db.Table(
    "teachers_goals",
    db.Column("teacher_id", db.Integer, db.ForeignKey("teachers.id")),
    db.Column("goal_id", db.Integer, db.ForeignKey("goals.id"))
)


class Teacher(db.Model):
    __tablename__ = "teachers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    about = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    picture = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    free = db.Column(db.String, nullable=False)
    goals = db.relationship(
        "Goal",
        secondary=teachers_goals_association,
        back_populates="teachers",
    )


class Goal(db.Model):
    __tablename__ = "goals"
    id = db.Column(db.Integer, primary_key=True)
    inner_name = db.Column(db.String, nullable=False, unique=True)
    name = db.Column(db.String, nullable=False)
    teachers = db.relationship(
        "Teacher",
        secondary=teachers_goals_association,
        back_populates="goals"
    )


class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    client_name = db.Column(db.String, nullable=False)
    client_phone = db.Column(db.String, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    teacher = db.relationship("Teacher")


class Request(db.Model):
    __tablename__ = "requests"
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String, nullable=False)
    client_name = db.Column(db.String, nullable=False)
    client_phone = db.Column(db.String, nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey("goals.id"))
    goal = db.relationship("Goal")


@app.route("/profiles/<profile_id>/")
def profile(profile_id):
    teacher = Teacher.query.get_or_404(profile_id)
    return render_template(
        "profile.html",
        teacher=teacher,
        schedule=json.loads(teacher.free),
        days=days
    )


@app.route("/goals/<goal_id>/")
def goals(goal_id):
    goal = Goal.query.filter_by(inner_name=goal_id).first()
    teachers = Teacher.query \
        .join(Goal, Teacher.goals) \
        .filter_by(inner_name=goal_id) \
        .order_by(Teacher.rating.desc()) \
        .all()
    return render_template(
        "goal.html", teachers=teachers, goal=goal
    )


@app.route("/")
def main():
    t_db_count = Teacher.query.count()
    goals = Goal.query.all()
    random_set = get_random_set(
        length=TEACHERS_COUNT_ON_MAIN, max_value=t_db_count - 1
    )
    # random teachers
    rand_ts = [Teacher.query.filter_by(id=id_).first() for id_ in random_set]
    return render_template("index.html", teachers=rand_ts, goals=goals)


@app.route("/booking/<profile_id>/<day>/<time>/", methods=["GET", "POST"])
def booking(profile_id, day, time):
    teacher = Teacher.query.get_or_404(profile_id)
    rus_weekday = days[day]
    booking_form = BookingForm()

    if booking_form.validate_on_submit():
        # update teacher schedule
        teacher = Teacher.query.get_or_404(booking_form.clientTeacher.data)
        free = json.loads(teacher.free)
        free[booking_form.clientWeekday.data][
            booking_form.clientTime.data] = False
        teacher.free = json.dumps(free)
        # write entry to Booking table
        booking = Booking(
            day=booking_form.clientWeekday.data,
            time=booking_form.clientTime.data,
            teacher_id=booking_form.clientTeacher.data,
            client_name=booking_form.clientName.data,
            client_phone=booking_form.clientPhone.data
        )
        db.session.add(booking)
        db.session.commit()

        return render_template(
            "booking_done.html",
            rus_weekday=days[booking_form.clientWeekday.data],
            booking_form=booking_form,
        )
    return render_template(
        "booking.html",
        teacher=teacher,
        weekday=day,
        time=str(time),
        rus_weekday=rus_weekday,
    )


@app.route("/request/", methods=["GET", "POST"])
def request():
    request_form = RequestForm()
    if request_form.validate_on_submit():
        goal = Goal.query.filter_by(inner_name=request_form.goal.data).first()
        db.session.add(
            Request(time=request_form.time.data,
                    client_name=request_form.clientName.data,
                    client_phone=request_form.clientPhone.data,
                    goal_id=goal.id)
        )
        db.session.commit()
        return render_template("request_done.html", request_form=request_form)
    return render_template("request.html")


if __name__ == '__main__':
    app.run()
