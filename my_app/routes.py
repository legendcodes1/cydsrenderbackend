from flask import Blueprint, request, jsonify
from .models import Customer, Booking, Service, MealPrepBid, CateringBid, Calendar, User
from . import db  # Updated import for db
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import pytz
from pytz import timezone
from dateutil import parser 
import requests
from werkzeug.security import check_password_hash
import logging
logging.basicConfig(level=logging.DEBUG)

main = Blueprint('main', __name__)

# Fetch all customers
@main.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return jsonify([customer.to_dict() for customer in customers])

# Add a new customer
@main.route('/customers', methods=['POST'])
def add_customer():
    data = request.json

    required_fields = ['name', 'email', 'phone_number']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    new_customer = Customer(
        name=data['name'],
        email=data['email'],
        phone_number=data['phone_number']
    )

    try:
        db.session.add(new_customer)
        db.session.commit()
        return jsonify(new_customer.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Could not add customer, possibly a duplicate entry.'}), 400

# Delete an existing customer
@main.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Customer deleted successfully'}), 200

# Edit an existing customer
@main.route('/customers/<int:customer_id>', methods=['PUT'])
def edit_customer(customer_id):
    data = request.json

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    if 'name' in data:
        customer.name = data['name']
    if 'email' in data:
        customer.email = data['email']
    if 'phone_number' in data:
        customer.phone_number = data['phone_number']

    db.session.commit()
    return jsonify(customer.to_dict()), 200

#fetch all bids
# Route to fetch all meal prep bids
@main.route('/meal_prep_bids', methods=['GET'])
def get_meal_prep_bids():
    meal_prep_bids = MealPrepBid.query.all()
    
    # Serialize the meal prep bids
    meal_prep_bids_list = [
        {
            'meal_bid_id': bid.meal_bid_id,
            'created_at': bid.created_at.isoformat(),
            'bid_status': bid.bid_status,
            'miles': bid.miles,
            'service_fee': str(bid.service_fee),
            'estimated_groceries': str(bid.estimated_groceries),
            'estimated_bid_price': str(bid.estimated_bid_price),
            'supplies': str(bid.supplies),
            'booking_id': bid.booking_id,
            'customer_id': bid.customer_id
        } for bid in meal_prep_bids
    ]

    return jsonify(meal_prep_bids_list), 200

# Route to fetch all catering bids
@main.route('/catering_bids', methods=['GET'])
def get_catering_bids():
    catering_bids = CateringBid.query.all()
    
    # Serialize the catering bids
    catering_bids_list = [
        {
            'catering_bid_id': bid.catering_bid_id,
            'created_at': bid.created_at.isoformat(),
            'bid_status': bid.bid_status,
            'miles': bid.miles,
            'service_fee': str(bid.service_fee),
            'clean_up': str(bid.clean_up),
            'decorations': str(bid.decorations),
            'estimated_groceries': str(bid.estimated_groceries),
            'foods': bid.foods,
            'estimated_bid_price': str(bid.estimated_bid_price),
            'booking_id': bid.booking_id,
            'customer_id': bid.customer_id
        } for bid in catering_bids
    ]

    return jsonify(catering_bids_list), 200

# Create a new bid based on service type

# PUT route to update a Meal Prep bid
@main.route('/meal_prep_bids/<int:meal_bid_id>', methods=['PUT'])
def update_meal_prep_bid(meal_bid_id):
    data = request.json

    # Retrieve the bid using both primary keys (assuming MealPrepBid has a composite primary key)
    bid = MealPrepBid.query.filter_by(meal_bid_id=meal_bid_id).first()

    if not bid:
        return jsonify({'error': 'Meal Prep Bid not found'}), 404

    # Update fields with provided data, if any
    bid.bid_status = data.get('bid_status', bid.bid_status)
    bid.miles = data.get('miles', bid.miles)
    bid.service_fee = data.get('service_fee', bid.service_fee)
    bid.estimated_groceries = data.get('estimated_groceries', bid.estimated_groceries)
    bid.estimated_bid_price = data.get('estimated_bid_price', bid.estimated_bid_price)
    bid.supplies = data.get('supplies', bid.supplies)
    bid.booking_id = data.get('booking_id', bid.booking_id)

    # Assign customer information if provided
    customer_name = data.get('customer_name')
    if customer_name:
        customer = Customer.query.filter_by(name=customer_name).first()
        if customer:
            bid.customer_id = customer.id
        else:
            return jsonify({'error': 'Customer not found'}), 404

    try:
        db.session.commit()
        return jsonify(bid.to_dict()), 200
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update meal prep bid: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    
# PUT route to update a Catering bid
@main.route('/catering_bids/<int:catering_bid_id>', methods=['PUT'])
def update_catering_bid(catering_bid_id):
    data = request.json
    bid = CateringBid.query.get(catering_bid_id)

    if not bid:
        return jsonify({'error': 'Catering Bid not found'}), 404

    # Update fields with provided data, if any
    bid.bid_status = data.get('bid_status', bid.bid_status)
    bid.miles = data.get('miles', bid.miles)
    bid.service_fee = data.get('service_fee', bid.service_fee)
    bid.clean_up = data.get('clean_up', bid.clean_up)
    bid.decorations = data.get('decorations', bid.decorations)
    bid.estimated_groceries = data.get('estimated_groceries', bid.estimated_groceries)
    bid.booking_id = data.get('booking_id', bid.booking_id)

    try:
        db.session.commit()
        return jsonify(bid.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Failed to update catering bid'}), 400

# POST route to create a Meal Prep bid
@main.route('/meal_prep_bids', methods=['POST'])
def create_meal_prep_bid():
    data = request.json

    # Create a new MealPrepBid instance
    new_bid = MealPrepBid(
        bid_status=data['bid_status'],
        miles=data['miles'],
        service_fee=data['service_fee'],
        estimated_groceries=data['estimated_groceries'],
        supplies=data.get('supplies', 0),  # Default to 0 if not provided
        booking_id=data['booking_id'],
        customer_id=data['customer_id']
    )

    try:
        db.session.add(new_bid)
        db.session.commit()
        return jsonify(new_bid.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Failed to create meal prep bid'}), 400

# POST route to create a Catering bid
@main.route('/catering_bids', methods=['POST'])
def create_catering_bid():
    data = request.json

    # Create a new CateringBid instance
    new_bid = CateringBid(
        bid_status=data['bid_status'],
        miles=data['miles'],
        service_fee=data['service_fee'],
        clean_up=data.get('clean_up', False),
        decorations=data.get('decorations', False),
        estimated_groceries=data['estimated_groceries'],
        booking_id=data['booking_id'],
        customer_id=data['customer_id']
    )

    try:
        db.session.add(new_bid)
        db.session.commit()
        return jsonify(new_bid.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Failed to create catering bid'}), 400




# Fetch all bookings
@main.route('/bookings', methods=['GET'])
def get_bookings():
    bookings = Booking.query.all()
    return jsonify([{
        'booking_id': b.booking_id,
        'requested_date': b.requested_date.isoformat(),
        'event_location': b.event_location,
        'event_type': b.event_type,
        'customer_id': b.customer_id,
        'number_of_guests': b.number_of_guests,
        'bid_status': b.bid_status,
        'start_time': b.start_time.isoformat() if b.start_time else None,  
        'end_time': b.end_time.isoformat() if b.end_time else None,
        'service_type': b.service_type,  # Add service_type here
    } for b in bookings])

# Fetch a booking by booking_id
@main.route('/bookings/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    # Find the booking with the specific booking_id
    booking = Booking.query.get(booking_id)

    # If booking is found, return it in JSON format
    if booking:
        # Strip timezone info if it's present
        start_time = booking.start_time.replace(tzinfo=None) if booking.start_time else None
        end_time = booking.end_time.replace(tzinfo=None) if booking.end_time else None
        
        return jsonify({
            'booking_id': booking.booking_id,
            'requested_date': booking.requested_date.isoformat(),
            'event_location': booking.event_location,
            'event_type': booking.event_type,
            'customer_id': booking.customer_id,
            'number_of_guests': booking.number_of_guests,
            'bid_status': booking.bid_status,
            'start_time': start_time.isoformat() if start_time else None,  
            'end_time': end_time.isoformat() if end_time else None,
            'service_type': booking.service_type,
        })
    else:
        return jsonify({"error": "Booking not found"}), 404

    
@main.route('/bookings', methods=['POST'])
def create_booking():
    data = request.json
    print(f"Received data in POST request: {data}")  # Log the incoming data

    # Validate required fields
    required_fields = [
        'requested_date', 'event_location', 'event_type', 'customer_id',
        'number_of_guests', 'bid_status', 'user_id', 'service_type',
        'start_time', 'end_time'
    ]
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        # Parse the requested_date (this is still a date field)
        requested_date = datetime.strptime(data['requested_date'], '%Y-%m-%d').date()

        # Parse start_time and end_time, and extract only the time part (without date and timezone)
        start_time = parser.isoparse(data['start_time']) if data['start_time'] else None
        end_time = parser.isoparse(data['end_time']) if data['end_time'] else None

        # Extract just the time from the datetime object (in %H:%M:%S format)
        start_time_str = start_time.strftime('%H:%M:%S') if start_time else None
        end_time_str = end_time.strftime('%H:%M:%S') if end_time else None

        # Log the parsed times to ensure correct parsing
        print(f"Parsed start_time: {start_time_str}, Parsed end_time: {end_time_str}")

        # Validate that start_time and end_time are not None
        if not start_time_str or not end_time_str:
            return jsonify({'error': 'Both start_time and end_time must be provided and valid.'}), 400

        print(f"Start time: {start_time_str}, End time: {end_time_str}, Requested date: {requested_date}")

    except ValueError as e:
        print("Parsing error:", str(e))
        return jsonify({'error': 'Invalid date or time format.'}), 400

    # Create the new booking object with the datetime and timezone-aware start_time and end_time
    new_booking = Booking(
        requested_date=requested_date,
        event_location=data['event_location'],
        event_type=data['event_type'],
        customer_id=data['customer_id'],
        number_of_guests=data['number_of_guests'],
        bid_status=data['bid_status'],
        user_id=data['user_id'],
        service_type=data['service_type'],
        start_time=start_time,  # Timezone-aware DateTime
        end_time=end_time       # Timezone-aware DateTime
    )

    try:
        db.session.add(new_booking)
        db.session.commit()
        print("Booking added to the session")

        # Create the associated calendar event with start_time and end_time included
        calendar_data = {
            'event_date': requested_date.strftime('%Y-%m-%d'),  # Convert date to string
            'event_status': 'Pending',  # Default event status
            'event_type': data['event_type'],
            'start_time': start_time_str,  # Send just the time part in %H:%M:%S format
            'end_time': end_time_str,      # Send just the time part in %H:%M:%S format
            'booking_id': new_booking.booking_id
        }

        # Make the POST request to the calendar service
        calendar_response = requests.post("https://cydsrenderbackend.onrender.com/calendar", json=calendar_data)
        if calendar_response.status_code != 200:
            print("Failed to create calendar event:", calendar_response.text)

        return jsonify(new_booking.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Failed to add booking.'}), 400

    
    
# Edit an existing booking
@main.route('/bookings/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    data = request.json
    print(f"Received data: {data}")  # Log the incoming data to check it

    # Validate required fields
    required_fields = ['requested_date', 'event_location', 'event_type', 'customer_id', 'number_of_guests', 'bid_status', 'user_id', 'service_type', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        # Parse the requested date (this is still a date field)
        requested_date = datetime.strptime(data['requested_date'], '%Y-%m-%d').date()

        # Parse start_time and end_time as time objects (just the time, no date or timezone)
        tz = pytz.timezone('America/Chicago')  # Set to your timezone, e.g., 'America/Chicago'

        # Parse the start and end times as time objects
        start_time = datetime.strptime(data['start_time'], '%H:%M:%S').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M:%S').time()

        # Combine date with time and localize to the desired timezone
        start_time = tz.localize(datetime.combine(requested_date, start_time)).time()
        end_time = tz.localize(datetime.combine(requested_date, end_time)).time()

    except ValueError:
        return jsonify({'error': 'Invalid date or time format.'}), 400

    try:
        # Fetch the booking record
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found.'}), 404

        # Update the booking record
        booking.requested_date = requested_date
        booking.event_location = data['event_location']
        booking.event_type = data['event_type']
        booking.customer_id = data['customer_id']
        booking.number_of_guests = data['number_of_guests']
        booking.bid_status = data['bid_status']
        booking.user_id = data['user_id']
        booking.service_type = data['service_type']
        booking.start_time = start_time  # Store as time with timezone
        booking.end_time = end_time  # Store as time with timezone

        db.session.commit()

        # Update the calendar event associated with this booking
        calendar_event = Calendar.query.filter_by(booking_id=booking_id).first()
        if calendar_event:
            calendar_event.event_date = requested_date
            calendar_event.start_time = start_time  # Store as time with timezone
            calendar_event.end_time = end_time  # Store as time with timezone
            db.session.commit()

        return jsonify({'message': 'Booking updated successfully.'}), 200

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Failed to update booking.'}), 400

# Delete an existing booking
@main.route('/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    db.session.delete(booking)
    db.session.commit()
    return jsonify({'message': 'Booking deleted successfully'}), 200

# Fetch all calendar events
@main.route('/calendar', methods=['GET'])
def get_calendar_events():
    events = Calendar.query.all()
    return jsonify([{
        'event_id': event.event_id,
        'created_at': event.created_at.isoformat() if event.created_at else None,
        'event_date': event.event_date.isoformat() if event.event_date else None,
        'event_status': event.event_status,
        'customer_id': event.booking.customer_id if event.booking else None ,
        'event_type': event.event_type,
        'booking_id': event.booking_id,
        'start_time': event.start_time.isoformat() if event.start_time else None,  # Include start_time
        'end_time': event.end_time.isoformat() if event.end_time else None  # Include end_time
    } for event in events])

# Fetch a specific event by booking_id
@main.route('/calendar/<int:booking_id>', methods=['GET'])
def get_calendar_event(booking_id):
    # Query the event using booking_id
    event = Calendar.query.filter_by(booking_id=booking_id).first()
    
    if event is None:
        return jsonify({'error': 'Event not found.'}), 404

    # Return the event data as JSON
    return jsonify({
        'event_id': event.event_id,
        'created_at': event.created_at.isoformat() if event.created_at else None,
        'event_date': event.event_date.isoformat() if event.event_date else None,
        'event_status': event.event_status,
        'customer_id': event.booking.customer_id if event.booking else None,
        'event_type': event.event_type,
        'booking_id': event.booking_id,
        'start_time': event.start_time.isoformat() if event.start_time else None,
        'end_time': event.end_time.isoformat() if event.end_time else None
    }), 200


# Add event to calendar
@main.route('/calendar', methods=['POST'])
def add_to_calendar():
    data = request.json

    # Required fields
    required_fields = ['event_date', 'event_status', 'event_type', 'booking_id', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        # Parse event_date as date (YYYY-MM-DD)
        event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date()

        # Parse start_time and end_time as time (HH:MM:SS)
        tz = pytz.timezone('America/Chicago')  # Set to your desired timezone, e.g., 'America/Chicago'
        start_time = datetime.strptime(data['start_time'], '%H:%M:%S').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M:%S').time()

        # Combine event_date with start_time and end_time and localize them to the timezone
        start_time = tz.localize(datetime.combine(event_date, start_time)).time()
        end_time = tz.localize(datetime.combine(event_date, end_time)).time()

    except ValueError as e:
        return jsonify({'error': f'Invalid date or time format: {str(e)}'}), 400

    # Create new calendar event
    new_event = Calendar(
        event_date=event_date,
        event_status=data['event_status'],
        event_type=data['event_type'],
        booking_id=data['booking_id'],
        start_time=start_time,  # Store as time with timezone
        end_time=end_time  # Store as time with timezone
    )

    try:
        db.session.add(new_event)
        db.session.commit()
        return jsonify({'message': 'Event added to calendar successfully'}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Failed to add event to calendar'}), 400

# Update an event in the calendar (using PATCH for partial updates)
@main.route('/calendar/<int:event_id>', methods=['PUT'])
def update_calendar_event(event_id):
    data = request.json
    print(f"Updated event data: {data}")  # Log the incoming data to check it

    try:
        # Parse the event_date (no change, it's still a date)
        event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date()

        # Parse start_time and end_time as time objects
        start_time_str = data['start_time']
        end_time_str = data['end_time']

        # Parse the time values (without timezone adjustment here)
        start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
        end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()

    except ValueError as e:
        print(f"Date or time parsing error: {e}")
        return jsonify({'error': 'Invalid date or time format.'}), 400

    try:
        # Fetch the event record
        calendar_event = Calendar.query.get(event_id)
        if not calendar_event:
            return jsonify({'error': 'Event not found.'}), 404

        # Update the event details
        calendar_event.event_type = data['event_type']
        calendar_event.event_status = data['event_status']
        calendar_event.event_date = event_date
        calendar_event.start_time = start_time  # Store as time
        calendar_event.end_time = end_time  # Store as time

        db.session.commit()
        return jsonify({'message': 'Event updated successfully.'}), 200

    except Exception as e:
        print(f"Update error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update event.'}), 500
    

# Delete event from the calendar
@main.route('/calendar/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        # Query the event by its ID
        event = Calendar.query.get(event_id)
        
        # If the event is not found, return a 404 error
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Delete the event
        db.session.delete(event)

        # Query and delete the associated booking
        booking = Booking.query.filter_by(event_id=event_id).first()  # Assuming event_id is a foreign key in Booking
        if booking:
            db.session.delete(booking)
        
        db.session.commit()
        
        return jsonify({'message': 'Event and associated booking deleted successfully'}), 200
    
    except Exception as e:
        print(f"Error deleting event and booking: {e}")
        db.session.rollback()  # Rollback in case of an error
        return jsonify({'error': 'Failed to delete event and booking'}), 500


@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    # Query the database for the user
    user = User.query.filter_by(username=username).first()

    if user:
        # Temporarily comparing plain-text passwords for existing users (for testing)
        if user.password == password:
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict()  # Convert user data to dictionary
            }), 200
        else:
            return jsonify({'message': 'Invalid username or password'}), 401
    else:
        return jsonify({'message': 'Invalid username or password'}), 401


@main.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data or 'email' not in data:
        return jsonify({'message': 'Username, password, and email are required'}), 400

    hashed_password = generate_password_hash(data['password'], method='bcrypt')

    new_user = User(
        username=data['username'],
        password=hashed_password,
        email=data['email']
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error creating user', 'error': str(e)}), 500
