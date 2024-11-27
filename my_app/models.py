from . import db
from datetime import datetime
from sqlalchemy import Sequence
import pytz

class Customer(db.Model):
    __tablename__ = 'Customers'
    customer_id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    phone_number = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'customer_id': self.customer_id,
            'name': self.name,
            'email': self.email,
            'phone_number': self.phone_number
        }
    
class User(db.Model):
    __tablename__ = 'User'
    user_id = db.Column(db.BigInteger, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    Password_reset_token = db.Column(db.Text)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'username': self.username,
            'email': self.email,
            'Password_reset_token': self.Password_reset_token
        }

class Booking(db.Model):
    __tablename__ = 'Bookings'
    booking_id = db.Column(db.Integer, primary_key=True)
    requested_date = db.Column(db.Date, nullable=False)
    event_location = db.Column(db.String)
    event_type = db.Column(db.String)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.customer_id'))
    number_of_guests = db.Column(db.Integer)
    bid_status = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'))
    
    # Define the foreign key for the Calendar relationship
    event_id = db.Column(db.Integer, db.ForeignKey('Calendar.event_id'), nullable=True)

    # Change to DateTime with timezone
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time = db.Column(db.DateTime(timezone=True), nullable=False)
    
    service_type = db.Column(db.String, nullable=True)

    # Relationship to Calendar with cascade rule applied here
    calendar = db.relationship('Calendar', backref='booking', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'booking_id': self.booking_id,
            'requested_date': self.requested_date.strftime('%Y-%m-%d'),
            'event_location': self.event_location,
            'event_type': self.event_type,
            'customer_id': self.customer_id,
            'number_of_guests': self.number_of_guests,
            'bid_status': self.bid_status,
            'user_id': self.user_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'service_type': self.service_type
        }


class Service(db.Model):
    __tablename__ = 'Service'
    service_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    service_name = db.Column(db.String)
    service_date = db.Column(db.Date)
    service_time = db.Column(db.Time)
    service_type = db.Column(db.String)
    booking_id = db.Column(db.Integer, db.ForeignKey('Bookings.booking_id'))

    def to_dict(self):
        return {
            'service_id': self.service_id,
            'created_at': self.created_at.isoformat(),
            'service_name': self.service_name,
            'service_date': self.service_date.isoformat(),
            'service_time': self.service_time.isoformat(),
            'service_type': self.service_type,
            'booking_id': self.booking_id
        }

class MealPrepBid(db.Model):
    __tablename__ = 'Meal_Prep_Bids'
    
    meal_bid_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True) 
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(), nullable=False)
    bid_status = db.Column(db.Text, nullable=False)
    miles = db.Column(db.BigInteger, nullable=False)
    service_fee = db.Column(db.BigInteger, nullable=False)
    estimated_groceries = db.Column(db.BigInteger, nullable=False)
    estimated_bid_price = db.Column(db.BigInteger, nullable=True)
    supplies = db.Column(db.BigInteger, nullable=False)
    booking_id = db.Column(db.BigInteger, db.ForeignKey('Bookings.booking_id'), nullable=False)
    customer_id = db.Column(db.BigInteger, primary_key=True)

    def to_dict(self):
        return {
            'meal_bid_id': self.meal_bid_id,
            'created_at': self.created_at.isoformat(),
            'bid_status': self.bid_status,
            'miles': self.miles,
            'service_fee': self.service_fee,
            'estimated_groceries': self.estimated_groceries,
            'supplies': self.supplies,
            'booking_id': self.booking_id
        }

class CateringBid(db.Model):
    __tablename__ = 'Catering_Bids'
    
    catering_bid_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)  # auto-increment
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    bid_status = db.Column(db.String, nullable=False)
    miles = db.Column(db.BigInteger, nullable=True)
    service_fee = db.Column(db.BigInteger, nullable=False)
    clean_up = db.Column(db.BigInteger, nullable=True)
    decorations = db.Column(db.BigInteger, nullable=True)
    estimated_groceries = db.Column(db.BigInteger, nullable=True)
    foods = db.Column(db.String)
    estimated_bid_price = db.Column(db.BigInteger, nullable=True)
    booking_id = db.Column(db.BigInteger, db.ForeignKey('Bookings.booking_id'), nullable=False)
    customer_id = db.Column(db.BigInteger, primary_key=True)
   

    def to_dict(self):
        return {
            'catering_bid_id': self.catering_bid_id,
            'created_at': self.created_at.isoformat(),
            'bid_status': self.bid_status,
            'miles': self.miles,
            'service_fee': self.service_fee,
            'clean_up': self.clean_up,
            'decorations': self.decorations,
            'estimated_groceries': self.estimated_groceries,
            'booking_id': self.booking_id,
        }

class Calendar(db.Model):
    __tablename__ = 'Calendar'
    
    event_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    event_date = db.Column(db.Date, nullable=False)
    event_status = db.Column(db.String, nullable=False)
    event_type = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'))
    
    # Foreign key to Booking model
    booking_id = db.Column(db.Integer, db.ForeignKey('Bookings.booking_id'))
    
    # Relationship to the Booking model without cascade here
    booking = db.relationship('Booking', backref='calendar', uselist=False, foreign_keys=[booking_id])

    # Change to DateTime with timezone
    start_time = db.Column(db.DateTime(timezone=True))
    end_time = db.Column(db.DateTime(timezone=True))

    def to_dict(self):
        return {
            'event_id': self.event_id,
            'created_at': self.created_at.isoformat(),
            'event_date': self.event_date.isoformat(),
            'event_status': self.event_status,
            'event_type': self.event_type,
            'user_id': self.user_id,
            'booking_id': self.booking_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }
