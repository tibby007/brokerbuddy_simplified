"""
Database reset script for BrokerBuddy application.
This script forcibly resets the database by removing it and creating a new one with the correct schema.
"""

import os
import sqlite3
import sys
from datetime import datetime

# Get database path from environment variable or use default
DB_PATH = os.environ.get('DATABASE_PATH', 'brokerbuddy.db')

def log(message):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def reset_database():
    """Force reset the database by removing it and creating a new one"""
    # Check if database exists
    if os.path.exists(DB_PATH):
        log(f"Removing existing database at {DB_PATH}")
        try:
            os.remove(DB_PATH)
            log("Database file removed successfully")
        except Exception as e:
            log(f"Error removing database file: {e}")
            return False
    
    # Create new database
    log(f"Creating new database at {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        create_schema(conn)
        populate_sample_data(conn)
        conn.close()
        log("Database reset completed successfully")
        return True
    except Exception as e:
        log(f"Error creating new database: {e}")
        return False

def create_schema(conn):
    """Create the database schema with all required tables"""
    cursor = conn.cursor()
    
    # Create clients table
    log("Creating clients table")
    cursor.execute('''
    CREATE TABLE clients (
        client_id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_name TEXT NOT NULL,
        credit_score TEXT NOT NULL,
        time_in_business TEXT NOT NULL,
        monthly_revenue TEXT,
        equipment_type TEXT NOT NULL,
        equipment_cost TEXT NOT NULL,
        industry TEXT,
        notes TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    # Create lenders table
    log("Creating lenders table")
    cursor.execute('''
    CREATE TABLE lenders (
        lender_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        program_type TEXT NOT NULL,
        description TEXT,
        website TEXT,
        contact_email TEXT,
        contact_phone TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    # Create lender_guidelines table
    log("Creating lender_guidelines table")
    cursor.execute('''
    CREATE TABLE lender_guidelines (
        guideline_id INTEGER PRIMARY KEY AUTOINCREMENT,
        lender_id INTEGER NOT NULL,
        min_credit_score TEXT,
        min_time_in_business TEXT,
        min_monthly_revenue TEXT,
        min_equipment_cost TEXT,
        max_equipment_cost TEXT,
        equipment_types TEXT,
        industries_accepted TEXT,
        industries_restricted TEXT,
        funding_speed TEXT,
        rate_range TEXT,
        term_range TEXT,
        advance_rate TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY (lender_id) REFERENCES lenders (lender_id)
    )
    ''')
    
    # Create matches table
    log("Creating matches table")
    cursor.execute('''
    CREATE TABLE matches (
        match_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        lender_id INTEGER NOT NULL,
        match_score REAL NOT NULL,
        match_details TEXT,
        created_at TEXT,
        FOREIGN KEY (client_id) REFERENCES clients (client_id),
        FOREIGN KEY (lender_id) REFERENCES lenders (lender_id)
    )
    ''')
    
    conn.commit()
    log("Database schema created successfully")

def populate_sample_data(conn):
    """Populate the database with sample lender data"""
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    # Sample lenders for App Only programs
    app_only_lenders = [
        ("FastTrack Capital", "App Only", "Quick approvals for equipment financing", "https://example.com/fasttrack", "contact@fasttrack.com", "800-555-1234", now, now),
        ("EasyLease Financial", "App Only", "Simplified leasing for small businesses", "https://example.com/easylease", "info@easylease.com", "800-555-2345", now, now),
        ("QuickApprove Funding", "App Only", "Same-day decisions on equipment loans", "https://example.com/quickapprove", "apply@quickapprove.com", "800-555-3456", now, now)
    ]
    
    # Sample lenders for Full Financials programs
    full_financials_lenders = [
        ("Premier Equipment Finance", "Full Financials", "Premium rates for established businesses", "https://example.com/premier", "info@premierequip.com", "800-555-4567", now, now),
        ("Enterprise Capital Group", "Full Financials", "Comprehensive financing solutions", "https://example.com/enterprise", "finance@enterprisecap.com", "800-555-5678", now, now),
        ("Strategic Leasing Partners", "Full Financials", "Tailored equipment leasing programs", "https://example.com/strategic", "partners@strategicleasing.com", "800-555-6789", now, now)
    ]
    
    # Insert lenders
    log("Inserting sample lenders")
    for lender in app_only_lenders + full_financials_lenders:
        cursor.execute('''
        INSERT INTO lenders (name, program_type, description, website, contact_email, contact_phone, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', lender)
    
    # Get lender IDs
    cursor.execute("SELECT lender_id, name, program_type FROM lenders")
    lenders = cursor.fetchall()
    
    # Sample guidelines for App Only lenders
    log("Inserting sample lender guidelines")
    for lender in lenders:
        lender_id, name, program_type = lender
        
        if program_type == "App Only":
            cursor.execute('''
            INSERT INTO lender_guidelines (
                lender_id, min_credit_score, min_time_in_business, min_monthly_revenue,
                min_equipment_cost, max_equipment_cost, equipment_types, industries_accepted,
                industries_restricted, funding_speed, rate_range, term_range, advance_rate,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lender_id, "600", "1 year", "10000",
                "5000", "150000", "Construction, Transportation, Manufacturing", "Most industries",
                "Adult Entertainment, Gambling", "1-2 days", "8%-15%", "2-5 years", "Up to 100%",
                now, now
            ))
        else:  # Full Financials
            cursor.execute('''
            INSERT INTO lender_guidelines (
                lender_id, min_credit_score, min_time_in_business, min_monthly_revenue,
                min_equipment_cost, max_equipment_cost, equipment_types, industries_accepted,
                industries_restricted, funding_speed, rate_range, term_range, advance_rate,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lender_id, "650", "2 years", "25000",
                "25000", "500000", "All equipment types", "All established industries",
                "None", "3-5 days", "6%-12%", "2-7 years", "Up to 100%",
                now, now
            ))
    
    conn.commit()
    log(f"Sample data populated: {len(app_only_lenders) + len(full_financials_lenders)} lenders with guidelines")

if __name__ == "__main__":
    log("Starting database reset")
    success = reset_database()
    if success:
        log("Database reset completed successfully")
    else:
        log("Database reset failed")
        sys.exit(1)

