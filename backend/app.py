from datetime import datetime

from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Create the SQLAlchemy db instance
db = SQLAlchemy(app)


# Define the data models
class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'))
    room_id = db.Column(db.String(10), db.ForeignKey('room.id'))
    check_in_date = db.Column(db.Date)
    check_out_date = db.Column(db.Date)
    detail = db.Column(db.String(255))
    amount = db.Column(db.Integer)
    guest = db.relationship('Guest', backref='booking')
    room = db.relationship('Room', backref='booking')


class Guest(db.Model):
    __tablename__ = 'guest'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    contact = db.Column(db.String(255))


class Room(db.Model):
    __tablename__ = 'room'
    id = db.Column(db.String(10), primary_key=True)
    max_guests = db.Column(db.Integer)
    price_per_day = db.Column(db.Integer)
    detail = db.Column(db.String(255))


# Route to show the booking list
@app.route('/')
def index():
    return render_template('index.html')


# Route to show the booking list
@app.route('/bookings')
def bookings():
    bookings_query = Booking.query.all()
    return render_template('bookings.html', bookings=bookings_query)


@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    data = request.get_json()
    booking_id = data.get('booking_id')
    print(f"booking_id: {booking_id}")

    try:
        booking = Booking.query.get(booking_id)
        if booking:
            db.session.delete(booking)
            db.session.commit()
            return jsonify({"status": "success", "message": "Booking deleted"})
        else:
            return jsonify({"status": "error", "message": "Booking not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/update_booking_date', methods=['POST'])
def update_booking_date():
    data = request.get_json()
    booking_id = data['booking_id']
    date_type = data['date_type']
    new_date = data['new_date']
    print(f"booking_id: {booking_id}, date_type: {date_type}, new_date:{new_date}")

    try:
        booking = Booking.query.get(booking_id)
        if booking:
            if date_type == 'check_in_date':
                booking.check_in_date = datetime.strptime(new_date, '%Y-%m-%d').date()
            elif date_type == 'check_out_date':
                booking.check_out_date = datetime.strptime(new_date, '%Y-%m-%d').date()
            if booking.check_in_date < booking.check_out_date:
                days = (booking.check_out_date - booking.check_in_date).days
                price = Room.query.filter_by(id=booking.room_id).first().price_per_day
                booking.amount = price * days
                db.session.commit()
                return jsonify({"status": "success", "message": "Booking date updated"})
            else:
                return jsonify({"status": "error", "message": "Booking date not correct"}), 404
        else:
            return jsonify({"status": "error", "message": "Booking not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# Route to show the guest list
@app.route('/guests')
def guests():
    guests_query = Guest.query.order_by('id').all()
    return render_template('guests.html', guests=guests_query)


# Route to show the room list
@app.route('/rooms')
def rooms():
    rooms_query = Room.query.order_by('id').all()
    return render_template('rooms.html', rooms=rooms_query)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
