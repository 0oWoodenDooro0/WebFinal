from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'YourSecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    contact = db.Column(db.String(255))


class Room(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    max_guests = db.Column(db.Integer)
    price = db.Column(db.Integer)
    detail = db.Column(db.String(255))


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'))
    room_id = db.Column(db.String(10), db.ForeignKey('room.id'))
    check_in_date = db.Column(db.Date)
    check_out_date = db.Column(db.Date)
    detail = db.Column(db.String(255))


class BookingForm(FlaskForm):
    guest_name = StringField('Guest Name', validators=[DataRequired()])
    room_id = SelectField('Room Id', validators=[DataRequired()])
    check_in_date = DateField('Check-In Date', format='%Y-%m-%d', validators=[DataRequired()])
    check_out_date = DateField('Check-Out Date', format='%Y-%m-%d', validators=[DataRequired()])
    contact_info = StringField('Contact Information', validators=[DataRequired()])
    detial = StringField('Booking Detail', validators=[DataRequired()])

    submit = SubmitField('Book Now')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/booking', methods=['GET', 'POST'])
def booking():
    form = BookingForm()
    rooms = Room.query.order_by("id").all()
    form.room_id.choices = [(room.id, room.detail) for room in rooms]
    if form.validate_on_submit():
        new_guest = Guest(name=form.guest_name.data, contact=form.contact_info.data)
        db.session.add(new_guest)
        db.session.flush()  # Flush to get the ID of the new guest

        new_booking = Booking(
            guest_id=new_guest.id,
            room_id=form.room_id.data,
            check_in_date=form.check_in_date.data,
            check_out_date=form.check_out_date.data,
            detail=form.detial.data
        )
        db.session.add(new_booking)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('booking.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
