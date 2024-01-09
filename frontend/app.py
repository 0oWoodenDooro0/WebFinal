import os

from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from gevent.pywsgi import WSGIServer
from wtforms import StringField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired, ValidationError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'YourSecretKey'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/postgres'
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
    submit = SubmitField('Next')


class RoomForm(FlaskForm):
    type = SelectField('Room Number', validators=[DataRequired()])
    submit = SubmitField('Next')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/room', methods=['GET', 'POST'])
def room():
    form = RoomForm()
    rooms = Room.query.order_by("id").all()
    form.type.choices = [(room.id, room.detail) for room in rooms]
    if form.validate_on_submit():
        return redirect(url_for('guest', room_id=form.type.data))

    return render_template('room.html', form=form)


@app.route('/guest', methods=['GET', 'POST'])
def guest():
    form = GuestForm()
    if form.validate_on_submit():
        return redirect(url_for('booking', room_id=request.args.get('room_id'), guest_name=form.guest_name.data,
                                contact_info=form.contact_info.data))

    return render_template('guest.html', form=form)


@app.route('/booking', methods=['GET', 'POST'])
def booking():
    form = BookingForm()
    if form.validate_on_submit():
        days = (form.check_out_date.data - form.check_in_date.data).days
        price = Room.query.filter_by(id=request.args.get('room_id')).first().price_per_day
        new_guest = Guest(name=request.args.get('guest_name'), contact=request.args.get('contact_info'))
        db.session.add(new_guest)
        db.session.flush()

        new_booking = Booking(
            guest_id=new_guest.id,
            room_id=request.args.get('room_id'),
            check_in_date=form.check_in_date.data,
            check_out_date=form.check_out_date.data,
            amount=price * days
        )
        db.session.add(new_booking)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('booking.html', form=form)


if __name__ == '__main__':
    server = WSGIServer(('0.0.0.0', 5000), app)
    server.serve_forever()
