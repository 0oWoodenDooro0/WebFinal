import os

from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from gevent.pywsgi import WSGIServer
from wtforms import StringField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired, ValidationError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'YourSecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    contact = db.Column(db.String(255))


class Room(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    max_guests = db.Column(db.Integer)
    price_per_day = db.Column(db.Integer)
    detail = db.Column(db.String(255))


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'))
    room_id = db.Column(db.String(10), db.ForeignKey('room.id'))
    check_in_date = db.Column(db.Date)
    check_out_date = db.Column(db.Date)
    detail = db.Column(db.String(255))
    amount = db.Column(db.Integer)


class BookingForm(FlaskForm):
    check_in_date = DateField('Check-In Date', format='%Y-%m-%d', validators=[DataRequired()])
    check_out_date = DateField('Check-Out Date', format='%Y-%m-%d', validators=[DataRequired()])
    detail = StringField('Detail', validators=[DataRequired()])
    submit = SubmitField('Book Now')

    def validate_check_out_date(form, field):
        if field.data < form.check_in_date.data:
            raise ValidationError("Check-out date must not be earlier than check-in date.")


class GuestForm(FlaskForm):
    guest_name = StringField('Guest Name', validators=[DataRequired()])
    contact_info = StringField('Contact Information', validators=[DataRequired()])
    submit = SubmitField('Book Now')


class RoomForm(FlaskForm):
    detail = SelectField('Room Number', validators=[DataRequired()])
    submit = SubmitField('Book Now')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/room', methods=['GET', 'POST'])
def room():
    form = RoomForm()
    rooms = Room.query.order_by("id").all()
    form.detail.choices = [(room.id, room.detail) for room in rooms]
    if form.validate_on_submit():
        global room_form
        room_form = form
        return redirect(url_for('guest'))

    return render_template('room.html', form=form)


@app.route('/guest', methods=['GET', 'POST'])
def guest():
    form = GuestForm()
    if form.validate_on_submit():
        global guest_form
        guest_form = form
        return redirect(url_for('booking'))

    return render_template('guest.html', form=form)


@app.route('/booking', methods=['GET', 'POST'])
def booking():
    form = BookingForm()

    if form.validate_on_submit():
        new_guest = Guest(name=guest_form.guest_name.data, contact=guest_form.contact_info.data)
        db.session.add(new_guest)
        db.session.flush()

        days = (form.check_out_date.data - form.check_in_date.data).days
        price = Room.query.filter_by(id=room_form.detail.data).first().price_per_day
        new_booking = Booking(
            guest_id=new_guest.id,
            room_id=room_form.detail.data,
            check_in_date=form.check_in_date.data,
            check_out_date=form.check_out_date.data,
            detail=form.detail.data,
            amount=price * days
        )
        db.session.add(new_booking)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('booking.html', form=form)


if __name__ == '__main__':
    server = WSGIServer(('0.0.0.0', 5000), app)
    server.serve_forever()
