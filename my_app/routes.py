from flask import Blueprint, request, jsonify 
from .models import Customer, Booking, Service, MealPrepBid, CateringBid, Calendar, User 
from . import db 
from datetime import datetime 
from sqlalchemy.exc import IntegrityError 
import pytz 
from pytz import timezone 
from dateutil import parser  
import requests 
from werkzeug.security import check_password_hash 
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash
from flask import current_app
from flask_mail import Message
from sqlalchemy import UniqueConstraint
import logging 
from datetime import datetime, timezone, timedelta  # Add timedelta here
logging.basicConfig(level=logging.DEBUG) 

main = Blueprint('main', __name__) 

logger = logging.getLogger(__name__) 
logger.setLevel(logging.INFO) 

handler = logging.StreamHandler() 

handler.setLevel(logging.INFO) 

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') 

handler.setFormatter(formatter) 

logger.addHandler(handler) 

 
 

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

 
 

@main.route('/customers/<int:customer_id>', methods=['PATCH'])
def soft_delete_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    print(f"Deactivating customer: {customer_id}, is_active: {customer.is_active}")

    # Check if the customer has associated bookings
    bookings = db.session.query(Booking).filter(Booking.customer_id == customer_id).all()
    if bookings:
        return jsonify({"error": "Cannot deactivate customer. Associated bookings exist."}), 400

    try:
        customer.is_active = False
        db.session.commit()
        print(f"Customer deactivated: {customer_id}, is_active: {customer.is_active}")
        return jsonify({"message": "Customer deactivated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main.route('/customers/<int:customer_id>/reactivate', methods=['PATCH'])
def reactivate_customer(customer_id):
    print(f"Reactivate request received for customer ID: {customer_id}")  # Ensure route is hit
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    print(f"Reactivating customer: {customer_id}, is_active: {customer.is_active}")
    try:
        customer.is_active = True
        db.session.commit()
        print(f"Customer reactivated: {customer_id}, is_active: {customer.is_active}")
        return jsonify({"message": "Customer reactivated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main.route('/customers/<int:customer_id>', methods=['PUT']) 
def edit_customer(customer_id): 
    # Get the customer from the database using the customer_id 
    customer = Customer.query.get(customer_id) 
    if not customer: 
        return jsonify({'error': 'Customer not found'}), 404 
    # Get the data from the request body 

    data = request.json 
    # Update the customer's details 
    if 'name' in data: 
        customer.name = data['name'] 
    if 'email' in data: 
        customer.email = data['email'] 
    if 'phone_number' in data: 
        customer.phone_number = data['phone_number'] 
    # Commit the changes to the database 

    db.session.commit() 

     

    # Return the updated customer 

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
            
            'foods': bid.foods,

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
@main.route('/meal_prep_bids/<int:meal_bid_id>/<int:customer_id>/<int:booking_id>', methods=['PUT'])
def update_meal_prep_bid(meal_bid_id, customer_id, booking_id):
    # Log the request
    print(f"Received PUT request for Meal Prep Bid ID: {meal_bid_id}, Customer ID: {customer_id}")
    
    data = request.json
    print(f"Received payload: {data}")

    # Query using both meal_bid_id and customer_id for composite primary key
    bid = MealPrepBid.query.filter_by(meal_bid_id=meal_bid_id, customer_id=customer_id, booking_id=booking_id,).first()

    if not bid:
        print(f"Meal Prep Bid with ID {meal_bid_id} and Customer ID {customer_id} not found.")
        return jsonify({'error': 'Meal Prep Bid not found'}), 404

    # Log the existing state of the bid
    print(f"Existing Meal Prep Bid: {bid.to_dict()}")

    # Update fields with provided data, if any
    bid.bid_status = data.get('bid_status', bid.bid_status)
    bid.miles = data.get('miles', bid.miles)
    bid.service_fee = data.get('service_fee', bid.service_fee)
    bid.estimated_groceries = data.get('estimated_groceries', bid.estimated_groceries)
    bid.estimated_bid_price = data.get('estimated_bid_price', bid.estimated_bid_price)
    bid.supplies = data.get('supplies', bid.supplies)
    bid.foods = data.get('foods', bid.foods)
    bid.booking_id = data.get('booking_id', bid.booking_id)

    # Optionally update customer info if provided
    customer_name = data.get('customer_name')
    if customer_name:
        customer = Customer.query.filter_by(name=customer_name).first()
        if customer:
            bid.customer_id = customer.id
        else:
            print(f"Customer {customer_name} not found.")
            return jsonify({'error': 'Customer not found'}), 404

    try:
        db.session.commit()
        print("Meal Prep Bid successfully updated.")
        return jsonify(bid.to_dict()), 200
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError during update: {str(e)}")
        return jsonify({'error': f'Failed to update meal prep bid: {str(e)}'}), 400
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

     

@main.route('/catering_bids/<int:catering_bid_id>/<int:customer_id>/<int:booking_id>', methods=['PUT'])
def update_catering_bid(catering_bid_id, customer_id, booking_id):
    # Log the request
    print(f"Received PUT request for Catering Bid ID: {catering_bid_id}, Customer ID: {customer_id}")
    
    data = request.json
    print(f"Received payload: {data}")

    # Query using the composite primary key
   # Query using both booking_id and customer_id
    bid = CateringBid.query.filter_by(booking_id=booking_id, customer_id=customer_id).first()


    if not bid:
        print(f"Catering Bid with ID {catering_bid_id} and Customer ID {customer_id} not found.")
        return jsonify({'error': 'Catering Bid not found'}), 404

    # Log the existing state of the bid
    print(f"Existing Catering Bid: {bid.to_dict()}")

    # Update fields with provided data, if any
    bid.bid_status = data.get('bid_status', bid.bid_status)
    bid.miles = data.get('miles', bid.miles)
    bid.service_fee = data.get('service_fee', bid.service_fee)
    bid.clean_up = data.get('clean_up', bid.clean_up)
    bid.decorations = data.get('decorations', bid.decorations)
    bid.estimated_groceries = data.get('estimated_groceries', bid.estimated_groceries)
    bid.estimated_bid_price = data.get('estimated_bid_price', bid.estimated_bid_price)
    bid.foods = data.get('foods', bid.foods)
    bid.booking_id = data.get('booking_id', bid.booking_id)

    try:
        db.session.commit()
        print("Catering Bid successfully updated.")
        return jsonify(bid.to_dict()), 200
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError during update: {str(e)}")
        return jsonify({'error': 'Failed to update catering bid'}), 400
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

 
 
# POST route to create a Meal Prep bid
@main.route('/meal_prep_bids', methods=['POST'])
def create_meal_prep_bid():
    data = request.json
    
    # Validate input
    if not data.get('booking_id') or not data.get('customer_id'):
        return jsonify({'error': 'Booking ID and Customer ID are required.'}), 400
    
    # Check if the customer is deactivated
    customer = Customer.query.get(data['customer_id'])
    if not customer or not customer.is_active:
        return jsonify({'error': 'This customer is deactivated and cannot create a bid.'}), 400
    
    # Check if a MealPrepBid or CateringBid already exists for the given booking_id
    existing_meal_prep_bid = MealPrepBid.query.filter_by(booking_id=data['booking_id']).first()
    existing_catering_bid = CateringBid.query.filter_by(booking_id=data['booking_id']).first()

    if existing_meal_prep_bid or existing_catering_bid:
        return jsonify({'error': 'This booking has already been used for a Meal Prep or Catering bid.'}), 400

    # Create a new MealPrepBid instance
    new_bid = MealPrepBid(
        bid_status=data['bid_status'],
        miles=data['miles'],
        service_fee=data['service_fee'],
        estimated_groceries=data['estimated_groceries'],
        supplies=data.get('supplies', 0),  # Default to 0 if not provided
        estimated_bid_price=data.get('estimated_bid_price'),
        foods=data.get('foods'),
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



@main.route('/catering_bids', methods=['POST'])
def create_catering_bid():
    data = request.json
    
    # Validate input
    if not data.get('booking_id') or not data.get('customer_id'):
        return jsonify({'error': 'Booking ID and Customer ID are required.'}), 400
    
    # Check if the customer is deactivated
    customer = Customer.query.get(data['customer_id'])
    if not customer or not customer.is_active:
        return jsonify({'error': 'This customer is deactivated and cannot create a bid.'}), 400
    
    # Check if a MealPrepBid or CateringBid already exists for the given booking_id
    existing_meal_prep_bid = MealPrepBid.query.filter_by(booking_id=data['booking_id']).first()
    existing_catering_bid = CateringBid.query.filter_by(booking_id=data['booking_id']).first()

    if existing_meal_prep_bid or existing_catering_bid:
        return jsonify({'error': 'This booking has already been used for a Meal Prep or Catering bid.'}), 400

    # Create a new CateringBid instance
    new_bid = CateringBid(
        bid_status=data['bid_status'],
        miles=data['miles'],
        service_fee=data['service_fee'],
        clean_up=data.get('clean_up', False),
        decorations=data.get('decorations', False),
        estimated_bid_price=data.get('estimated_bid_price'),
        estimated_groceries=data['estimated_groceries'],
        foods=data['foods'],
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

 
@main.route('/catering_bids/<int:catering_bid_id>/<int:customer_id>', methods=['DELETE'])
def delete_catering_bid(catering_bid_id, customer_id):
    try:
        # Fetch the record using both primary key values
        bid = CateringBid.query.filter_by(catering_bid_id=catering_bid_id, customer_id=customer_id).first()
        if not bid:
            return jsonify({'error': 'Meal Prep Bid not found'}), 404

        # Delete the record
        db.session.delete(bid)
        db.session.commit()
        return jsonify({'message': 'Catering Bid deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
 
 
@main.route('/meal_prep_bids/<int:meal_bid_id>/<int:customer_id>', methods=['DELETE'])
def delete_meal_prep_bid(meal_bid_id, customer_id):
    try:
        # Fetch the record using both primary key values
        bid = MealPrepBid.query.filter_by(meal_bid_id=meal_bid_id, customer_id=customer_id).first()
        if not bid:
            return jsonify({'error': 'Meal Prep Bid not found'}), 404

        # Delete the record
        db.session.delete(bid)
        db.session.commit()
        return jsonify({'message': 'Meal Prep Bid deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
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
    print(f"Received data in POST request: {data}")

    # Validate required fields
    required_fields = [
        'requested_date', 'event_location', 'event_type', 'customer_id',  # Ensure customer_id is included
        'number_of_guests', 'bid_status', 'user_id', 'service_type',
        'start_time', 'end_time'
    ]
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        # Parse the requested_date
        requested_date = datetime.strptime(data['requested_date'], '%Y-%m-%d').date()

        # Parse start_time and end_time, and extract only the time part (without date and timezone)
        start_time = parser.isoparse(data['start_time']) if data['start_time'] else None
        end_time = parser.isoparse(data['end_time']) if data['end_time'] else None

        # Log the parsed times
        print(f"Parsed start_time: {start_time}, Parsed end_time: {end_time}")

        # Validate that start_time and end_time are not None
        if not start_time or not end_time:
            return jsonify({'error': 'Both start_time and end_time must be provided and valid.'}), 400

    except ValueError as e:
        print("Parsing error:", str(e))
        return jsonify({'error': 'Invalid date or time format.'}), 400

    # Check if the customer is active
    customer_id = data['customer_id']
    if not customer_id:  # Check if customer_id is null
        return jsonify({'error': 'Customer ID is required.'}), 400

    
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found.'}), 404

    if not customer.is_active:
        return jsonify({'error': 'This customer is deactivated and cannot make a booking.'}), 403

    # Extract the customer's name
    customer_name = customer.name
    print(f"Customer found: {customer_name}")  # Log the customer name

    # Create the new booking object
    new_booking = Booking(
    requested_date=requested_date,
    event_location=data['event_location'],
    event_type=data['event_type'],
    customer_id=customer_id,  # Make sure `customer_id` is correct
    customer=customer,  # Make sure the relationship is set properly
    number_of_guests=data['number_of_guests'],
    bid_status=data['bid_status'],
    user_id=data['user_id'],
    service_type=data['service_type'],
    start_time=start_time,
    end_time=end_time
)

    try:
        # Add to the session and commit to the database
        db.session.add(new_booking)
        db.session.commit()
        print("Booking added to the session")

        # Create the associated calendar event with customer name
        calendar_data = {
        'event_date': requested_date.strftime('%Y-%m-%d'),
        'event_status': 'Pending',
        'event_type': data['event_type'],
        'start_time': start_time.strftime('%H:%M:%S'),
        'end_time': end_time.strftime('%H:%M:%S'),
        'booking_id': new_booking.booking_id,
        'customer_id': customer_id,  # Use `customer_id` here
        'customer_name': customer.name  # Ensure `customer_name` is correctly populated
    }
        # Log the calendar data before sending it
        print(f"Sending data to calendar: {calendar_data}")

        # Make the POST request to the calendar service
        calendar_response = requests.post("http://127.0.0.1:5000/calendar", json=calendar_data)
        
        # Check the calendar response status
        if calendar_response.status_code != 200:
            print(f"Failed to create calendar event: {calendar_response.status_code} - {calendar_response.text}")
        else:
            print(f"Calendar event created successfully: {calendar_response.text}")

        return jsonify(new_booking.to_dict()), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Failed to add booking. Integrity error occurred.'}), 400

 
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
    # Fetch all events
    events = Calendar.query.all()
    
    # Prepare a list to hold the response data
    response_data = []

    for event in events:
        # Fetch the customer based on customer_id
        customer = Customer.query.get(event.customer_id)  # Assuming customer_id is a field in Calendar
        
        # Append the event data along with the customer name (if exists)
        response_data.append({
            'event_id': event.event_id,
            'created_at': event.created_at.isoformat() if event.created_at else None,
            'event_date': event.event_date.isoformat() if event.event_date else None,
            'event_status': event.event_status,
            'customer_id': event.customer_id,  # Keep the customer_id
            'customer_name': customer.name if customer else None,  # Get customer name safely
            'event_type': event.event_type,
            'booking_id': event.booking_id,
            'start_time': event.start_time.isoformat() if event.start_time else None,
            'end_time': event.end_time.isoformat() if event.end_time else None
        })

    return jsonify(response_data)
 
 

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
    print(f"Updated event data: {data}")

    try:
        # Parse incoming data
        event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M:%S').time()  # Cast to time
        end_time = datetime.strptime(data['end_time'], '%H:%M:%S').time()  # Cast to time

        # Fetch the calendar event
        calendar_event = Calendar.query.get(event_id)
        if not calendar_event:
            return jsonify({'error': 'Event not found.'}), 404

        # Update calendar event fields
        calendar_event.event_type = data['event_type']
        calendar_event.event_status = data['event_status']
        calendar_event.event_date = event_date
        calendar_event.start_time = start_time
        calendar_event.end_time = end_time

        # Fetch and update the related booking
        booking = Booking.query.get(calendar_event.booking_id)
        if booking:
            booking.event_type = data['event_type']
            booking.requested_date = event_date
            booking.start_time = start_time  # Ensure this is a `time` object
            booking.end_time = end_time  # Ensure this is a `time` object

        db.session.commit()
        return jsonify({'message': 'Event and booking updated successfully.'}), 200

    except ValueError as e:
        print(f"Date or time parsing error: {e}")
        return jsonify({'error': 'Invalid date or time format.'}), 400
    except Exception as e:
        print(f"Update error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update event or booking.'}), 500

     
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

 

@main.route('/bookings_and_calendar/<int:booking_id>', methods=['DELETE']) 

def delete_booking_and_calendar(booking_id): 

    try: 

        logger.info(f"Attempting to delete booking with ID {booking_id}") 

         

        # Start a transaction 

        with db.session.begin(): 

            # Try to get the booking first 

            booking = Booking.query.get(booking_id) 

            if not booking: 

                logger.info(f"Booking {booking_id} not found. Proceeding to delete associated calendar events.") 

                 

                # Fetch and delete the associated calendar events (if booking doesn't exist) 

                calendar_events = Calendar.query.filter_by(booking_id=booking_id).all() 

                if not calendar_events: 

                    logger.error(f"No calendar events found for booking {booking_id}") 

                    return jsonify({"error": "No associated calendar events found"}), 404 

                else: 

                    logger.info(f"Found {len(calendar_events)} calendar events for booking {booking_id}, deleting them.") 

                     

                for calendar_event in calendar_events: 

                    try: 

                        db.session.delete(calendar_event) 

                        logger.info(f"Deleted calendar event with ID {calendar_event.event_id} for booking {booking_id}") 

                    except Exception as e: 

                        logger.error(f"Error deleting calendar event {calendar_event.event_id}: {str(e)}") 

                        db.session.rollback() 

                        return jsonify({"error": f"Error deleting calendar event {calendar_event.event_id}: {str(e)}"}), 500 

                 

                # Commit the transaction (only the calendar events are deleted in this case) 

                db.session.commit() 

                logger.info(f"Successfully committed changes: deleted calendar events for booking {booking_id}") 

                return jsonify({"message": "Calendar events deleted successfully, but the booking doesn't exist."}), 200 

 
 

            else: 

                # If the booking exists, delete the associated calendar events 

                calendar_events = Calendar.query.filter_by(booking_id=booking_id).all() 

                for calendar_event in calendar_events: 

                    db.session.delete(calendar_event) 

                    logger.info(f"Deleted calendar event with ID {calendar_event.event_id} for booking {booking_id}") 

                 

                # Now delete the booking itself 

                db.session.delete(booking) 

                logger.info(f"Deleted booking with ID {booking_id}") 

                 

                # Commit the transaction 

                db.session.commit() 

                logger.info(f"Successfully committed changes for booking {booking_id} and its associated calendar events") 

             

            return jsonify({"message": "Booking and associated calendar events deleted successfully"}), 200 

 
 

    except SQLAlchemyError as e: 

        db.session.rollback() 

        logger.error(f"SQLAlchemyError during the deletion of booking {booking_id} and calendar events: {str(e)}") 

        return jsonify({"error": f"SQLAlchemyError during the deletion: {str(e)}"}), 500 

    except Exception as e: 

        logger.error(f"Unexpected error occurred while deleting booking {booking_id}: {str(e)}") 

        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500 

 

# Create a token serializer
serializer = URLSafeTimedSerializer(current_app.secret_key)


@main.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200
