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
import logging

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_schema import BrokerBuddyDB
from matching_engine import MatchingEngine

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'brokerbuddy_simplified_secret_key')

# Configure logging
logging.basicConfig(level=logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

# Configuration
app.config.update(
    DATABASE_PATH=os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brokerbuddy.db')),
    DEBUG=os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't'),
    TESTING=False,
    SESSION_TYPE='filesystem',
    SESSION_PERMANENT=False,
    SESSION_USE_SIGNER=True
)

# Ensure session directory exists
session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
if not os.path.exists(session_dir):
    os.makedirs(session_dir)
app.config['SESSION_FILE_DIR'] = session_dir

# Database connection helper
def get_db():
    try:
        db_path = app.config['DATABASE_PATH']
        app.logger.debug(f"Connecting to database at {db_path}")
        db = BrokerBuddyDB(db_path)
        db.connect()
        return db
    except Exception as e:
        app.logger.error(f"Error connecting to database: {str(e)}")
        raise

# Get matching engine
def get_matching_engine():
    try:
        db = get_db()
        return MatchingEngine(db.conn)
    except Exception as e:
        app.logger.error(f"Error creating matching engine: {str(e)}")
        raise

# Initialize database if it doesn't exist
def init_db():
    try:
        if not os.path.exists(app.config['DATABASE_PATH']):
            app.logger.info(f"Initializing database at {app.config['DATABASE_PATH']}")
            db = BrokerBuddyDB(app.config['DATABASE_PATH'])
            db.initialize_database()
            app.logger.info(f"Database initialized at {app.config['DATABASE_PATH']}")
    except Exception as e:
        app.logger.error(f"Error initializing database: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html', now=datetime.now())

@app.route('/client-form')
def client_form():
    return render_template('client_form.html', now=datetime.now())

@app.route('/submit-client', methods=['POST'])
def submit_client():
    if request.method == 'POST':
        try:
            app.logger.debug("Processing client form submission")
            app.logger.debug(f"Form data: {request.form}")

            client_data = {
                'business_name': request.form.get('business_name', ''),
                'industry': request.form.get('industry', ''),
                'time_in_business': request.form.get('time_in_business', ''),
                'monthly_revenue': request.form.get('monthly_revenue', ''),
                'credit_score': request.form.get('credit_score', ''),
                'equipment_type': request.form.get('equipment_type', ''),
                'equipment_cost': request.form.get('equipment_cost', ''),
                'notes': request.form.get('notes', ''),
                'interested_in_wc': request.form.get('interested_in_wc', '')  # 🆕 Added
            }

            app.logger.debug(f"Processed client data: {client_data}")

            required_fields = ['business_name', 'credit_score', 'time_in_business', 'equipment_type', 'equipment_cost']
            for field in required_fields:
                if not client_data[field]:
                    app.logger.warning(f"Missing required field: {field}")
                    flash(f"Please provide {field.replace('_', ' ').title()}")
                    return redirect(url_for('client_form'))

            try:
                db = get_db()
                cursor = db.conn.cursor()

                app.logger.debug("Inserting client data into database")
                cursor.execute('''
                INSERT INTO clients (
                    business_name, credit_score, time_in_business, monthly_revenue,
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
                app.logger.debug(f"Client inserted with ID: {client_id}")
                db.conn.commit()
            except Exception as e:
                app.logger.error(f"Error saving client to database: {str(e)}")
                flash("An error occurred while saving your client information. Please try again.")
                return redirect(url_for('client_form'))

            try:
                app.logger.debug("Finding matching lenders")
                matching_engine = get_matching_engine()
                matches = matching_engine.find_matching_lenders(client_data)
                app.logger.debug(f"Found {len(matches)} matching lenders")

                matching_engine.save_match_results(client_id, matches)
                app.logger.debug("Saved match results to database")
            except Exception as e:
                app.logger.error(f"Error in matching engine: {str(e)}")
                flash("An error occurred while finding matching lenders. Please try again.")
                return redirect(url_for('client_form'))

            try:
                session['client_id'] = client_id
                session['client_data'] = client_data
                session['matches'] = matches
                app.logger.debug("Stored client data and matches in session")
            except Exception as e:
                app.logger.error(f"Error storing data in session: {str(e)}")
                flash("An error occurred while processing your request. Please try again.")
                return redirect(url_for('client_form'))

            return redirect(url_for('find_lenders'))
        except Exception as e:
            app.logger.error(f"Unexpected error in submit_client: {str(e)}")
            flash("An unexpected error occurred. Please try again later.")
            return redirect(url_for('client_form'))

@app.route('/find-lenders')
def find_lenders():
    """Display matching lenders for the client."""
    try:
        client_id = session.get('client_id')
        client_data = session.get('client_data')
        matches = session.get('matches')
        
        app.logger.debug(f"Retrieved from session - client_id: {client_id}, matches: {len(matches) if matches else 0}")

        if not client_id or not matches:
            app.logger.warning("No client data or matches found in session")
            flash("Please submit client information first")
            return redirect(url_for('client_form'))

        # Separate Equipment vs Working Capital Matches (NEW)
        equipment_matches = []
        working_capital_matches = []

        for match in matches:
            is_working_capital = False
            for detail in match.get('match_details', []):
                if detail.get('criterion') == 'working_capital' and detail.get('result') == 'Match':
                    is_working_capital = True
                    break

            if is_working_capital:
                working_capital_matches.append(match)
            else:
                equipment_matches.append(match)

        return render_template('results.html', 
            client_data=client_data, 
            equipment_matches=equipment_matches,
            working_capital_matches=working_capital_matches,
            now=datetime.now()
        )
    except Exception as e:
        app.logger.error(f"Error in find_lenders: {str(e)}")
        flash("An error occurred while retrieving lender matches. Please try again.")
        return redirect(url_for('client_form'))


@app.route('/lender-details/<int:lender_id>')
def lender_details(lender_id):
    try:
        db = get_db()
        cursor = db.conn.cursor()

        cursor.execute('SELECT * FROM lenders WHERE lender_id = ?', (lender_id,))
        lender = cursor.fetchone()

        cursor.execute('SELECT * FROM lender_guidelines WHERE lender_id = ?', (lender_id,))
        guidelines = cursor.fetchone()

        return render_template('lender_details.html', lender=lender, guidelines=guidelines, now=datetime.now())
    except Exception as e:
        app.logger.error(f"Error in lender_details: {str(e)}")
        flash("An error occurred while retrieving lender details. Please try again.")
        return redirect(url_for('find_lenders'))

@app.errorhandler(404)
def page_not_found(error):
    app.logger.warning(f"404 error: {request.path}")
    return render_template('404.html', now=datetime.now()), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"500 error: {str(e)}")
    return render_template('500.html', now=datetime.now()), 500

if __name__ == '__main__':
    try:
        init_db()
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        app.logger.error(f"Error starting application: {str(e)}")




            
           


 

