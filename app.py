"""
Main application file for the simplified BrokerBuddy application.
This module implements the Flask web application for BrokerBuddy,
focusing on the core matchmaking functionality between clients and lenders.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import sqlite3
from datetime import datetime
import sys

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_schema import BrokerBuddyDB
from matching_engine import MatchingEngine

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'brokerbuddy_simplified_secret_key')

# Configuration
app.config.update(
    DATABASE_PATH=os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brokerbuddy.db')),
    DEBUG=os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't'),
    TESTING=False
)

# Database connection helper
def get_db():
    db_path = app.config['DATABASE_PATH']
    db = BrokerBuddyDB(db_path)
    db.connect()
    return db

# Get matching engine
def get_matching_engine():
    db = get_db()
    return MatchingEngine(db.conn)

# Initialize database if it doesn't exist
def init_db():
    if not os.path.exists(app.config['DATABASE_PATH']):
        db = BrokerBuddyDB(app.config['DATABASE_PATH'])
        db.initialize_database()
        print(f"Database initialized at {app.config['DATABASE_PATH']}")

@app.route('/')
def index():
    return render_template('index.html', now=datetime.now())

@app.route('/client-form')
def client_form():
    return render_template('client_form.html', now=datetime.now())

@app.route('/submit-client', methods=['POST'])
def submit_client():
    if request.method == 'POST':
        client_data = {
            'business_name': request.form.get('business_name', ''),
            'industry': request.form.get('industry', ''),
            'time_in_business': request.form.get('time_in_business', ''),
            'monthly_revenue': request.form.get('monthly_revenue', ''),
            'credit_score': request.form.get('credit_score', ''),
            'equipment_type': request.form.get('equipment_type', ''),
            'equipment_cost': request.form.get('equipment_cost', ''),
            'notes': request.form.get('notes', '')
        }

        # Only these fields are required
        required_fields = ['business_name', 'industry', 'time_in_business', 'credit_score', 'equipment_type', 'equipment_cost']
        for field in required_fields:
            if not client_data[field]:
                flash(f"Please provide {field.replace('_', ' ').title()}")
                return redirect(url_for('client_form'))

        # Save client to database
        db = get_db()
        cursor = db.conn.cursor()

        cursor.execute('''
        INSERT INTO clients (
            name, credit_score, time_in_business, monthly_revenue,
            equipment_type, equipment_cost, industry, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client_data['business_name'],
            client_data['credit_score'],
            client_data['time_in_business'],
            client_data['monthly_revenue'],
            client_data['equipment_type'],
            client_data['equipment_cost'],
            client_data['industry'],
            client_data['notes'],
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        client_id = cursor.lastrowid
        db.conn.commit()

        # Find matching lenders
        matching_engine = get_matching_engine()
        matches = matching_engine.find_matching_lenders(client_data)

        # Save match results
        matching_engine.save_match_results(client_id, matches)

        # Store client_id and matches in session for results page
        session['client_id'] = client_id
        session['client_data'] = client_data
        session['matches'] = matches

        return redirect(url_for('find_lenders'))


        db = get_db()
        cursor = db.conn.cursor()

        cursor.execute('''
        INSERT INTO clients (
            name, credit_score, time_in_business, monthly_revenue,
            equipment_type, equipment_cost, industry, contact_email,
            contact_phone, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            client_data['business_name'],
            client_data['credit_score'],
            client_data['time_in_business'],
            client_data['monthly_revenue'],
            client_data['equipment_type'],
            client_data['equipment_cost'],
            client_data['industry'],
            '', '',
            client_data['notes'],
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        client_id = cursor.lastrowid
        db.conn.commit()

        matching_engine = get_matching_engine()
        matches = matching_engine.find_matching_lenders(client_data)
        matching_engine.save_match_results(client_id, matches)

        session['client_id'] = client_id
        session['client_data'] = client_data
        session['matches'] = matches

        return redirect(url_for('find_lenders'))

@app.route('/find-lenders')
def find_lenders():
    """Display matching lenders for the client."""
    client_id = session.get('client_id')
    client_data = session.get('client_data')
    matches = session.get('matches')

    if not client_id or not matches:
        flash("Please submit client information first")
        return redirect(url_for('client_form'))

    return render_template('results.html', client_data=client_data, matches=matches, now=datetime.now())

@app.route('/lender-details/<int:lender_id>')
def lender_details(lender_id):
    db = get_db()
    cursor = db.conn.cursor()

    cursor.execute('SELECT * FROM lenders WHERE lender_id = ?', (lender_id,))
    lender = cursor.fetchone()

    cursor.execute('SELECT * FROM lender_guidelines WHERE lender_id = ?', (lender_id,))
    guidelines = cursor.fetchone()

    return render_template('lender_details.html', lender=lender, guidelines=guidelines, now=datetime.now())

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', now=datetime.now()), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html', now=datetime.now()), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



     
     



