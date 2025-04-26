"""
Database verification script for BrokerBuddy application.
This script checks and updates the database schema to ensure all required tables and columns exist.
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

def verify_database():
    """Verify and update database schema if needed"""
    log(f"Verifying database at: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        log(f"Database file does not exist at {DB_PATH}. Creating new database.")
        create_database()
        return
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        log(f"Found tables: {', '.join(tables)}")
        
        # Create missing tables
        required_tables = ['clients', 'lenders', 'lender_guidelines', 'matches']
        for table in required_tables:
            if table not in tables:
                log(f"Table '{table}' is missing. Creating it.")
                create_table(conn, table)
        
        # Verify columns in clients table
        verify_clients_table(conn)
        
        # Verify columns in lenders table
        verify_lenders_table(conn)
        
        # Verify columns in lender_guidelines table
        verify_lender_guidelines_table(conn)
        
        # Verify columns in matches table
        verify_matches_table(conn)
        
        log("Database verification completed successfully.")
        
    except sqlite3.Error as e:
        log(f"SQLite error: {e}")
    except Exception as e:
        log(f"Unexpected error: {e}")
    finally:
        if conn:
            conn.close()

def create_database():
    """Create a new database with all required tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Create all tables
        create_table(conn, 'clients')
        create_table(conn, 'lenders')
        create_table(conn, 'lender_guidelines')
        create_table(conn, 'matches')
        
        conn.close()
        log("New database created successfully with all required tables.")
    except Exception as e:
        log(f"Error creating database: {e}")

def create_table(conn, table_name):
    """Create a specific table based on its name"""
    cursor = conn.cursor()
    
    if table_name == 'clients':
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
        log("Created clients table")
        
    elif table_name == 'lenders':
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
        log("Created lenders table")
        
    elif table_name == 'lender_guidelines':
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
        log("Created lender_guidelines table")
        
    elif table_name == 'matches':
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
        log("Created matches table")
    
    conn.commit()

def verify_clients_table(conn):
    """Verify and update the clients table schema"""
    cursor = conn.cursor()
    
    # Get current columns
    cursor.execute("PRAGMA table_info(clients)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    log(f"Clients table columns: {', '.join(columns.keys())}")
    
    # Required columns with their types
    required_columns = {
        'client_id': 'INTEGER',
        'business_name': 'TEXT',
        'credit_score': 'TEXT',
        'time_in_business': 'TEXT',
        'monthly_revenue': 'TEXT',
        'equipment_type': 'TEXT',
        'equipment_cost': 'TEXT',
        'industry': 'TEXT',
        'notes': 'TEXT',
        'created_at': 'TEXT',
        'updated_at': 'TEXT'
    }
    
    # Add missing columns
    for col_name, col_type in required_columns.items():
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE clients ADD COLUMN {col_name} {col_type}")
                log(f"Added missing column '{col_name}' to clients table")
            except sqlite3.Error as e:
                log(f"Error adding column '{col_name}': {e}")
    
    # If 'name' column exists but 'business_name' doesn't, copy data
    if 'name' in columns and 'business_name' in columns:
        try:
            cursor.execute("UPDATE clients SET business_name = name WHERE business_name IS NULL OR business_name = ''")
            log("Copied data from 'name' to 'business_name' where needed")
        except sqlite3.Error as e:
            log(f"Error copying data from 'name' to 'business_name': {e}")
    
    conn.commit()

def verify_lenders_table(conn):
    """Verify and update the lenders table schema"""
    cursor = conn.cursor()
    
    # Get current columns
    cursor.execute("PRAGMA table_info(lenders)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    log(f"Lenders table columns: {', '.join(columns.keys())}")
    
    # Required columns with their types
    required_columns = {
        'lender_id': 'INTEGER',
        'name': 'TEXT',
        'program_type': 'TEXT',
        'description': 'TEXT',
        'website': 'TEXT',
        'contact_email': 'TEXT',
        'contact_phone': 'TEXT',
        'created_at': 'TEXT',
        'updated_at': 'TEXT'
    }
    
    # Add missing columns
    for col_name, col_type in required_columns.items():
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE lenders ADD COLUMN {col_name} {col_type}")
                log(f"Added missing column '{col_name}' to lenders table")
            except sqlite3.Error as e:
                log(f"Error adding column '{col_name}': {e}")
    
    conn.commit()

def verify_lender_guidelines_table(conn):
    """Verify and update the lender_guidelines table schema"""
    cursor = conn.cursor()
    
    # Get current columns
    cursor.execute("PRAGMA table_info(lender_guidelines)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    log(f"Lender_guidelines table columns: {', '.join(columns.keys())}")
    
    # Required columns with their types
    required_columns = {
        'guideline_id': 'INTEGER',
        'lender_id': 'INTEGER',
        'min_credit_score': 'TEXT',
        'min_time_in_business': 'TEXT',
        'min_monthly_revenue': 'TEXT',
        'min_equipment_cost': 'TEXT',
        'max_equipment_cost': 'TEXT',
        'equipment_types': 'TEXT',
        'industries_accepted': 'TEXT',
        'industries_restricted': 'TEXT',
        'funding_speed': 'TEXT',
        'rate_range': 'TEXT',
        'term_range': 'TEXT',
        'advance_rate': 'TEXT',
        'created_at': 'TEXT',
        'updated_at': 'TEXT'
    }
    
    # Add missing columns
    for col_name, col_type in required_columns.items():
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE lender_guidelines ADD COLUMN {col_name} {col_type}")
                log(f"Added missing column '{col_name}' to lender_guidelines table")
            except sqlite3.Error as e:
                log(f"Error adding column '{col_name}': {e}")
    
    conn.commit()

def verify_matches_table(conn):
    """Verify and update the matches table schema"""
    cursor = conn.cursor()
    
    # Get current columns
    cursor.execute("PRAGMA table_info(matches)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    log(f"Matches table columns: {', '.join(columns.keys())}")
    
    # Required columns with their types
    required_columns = {
        'match_id': 'INTEGER',
        'client_id': 'INTEGER',
        'lender_id': 'INTEGER',
        'match_score': 'REAL',
        'match_details': 'TEXT',
        'created_at': 'TEXT'
    }
    
    # Add missing columns
    for col_name, col_type in required_columns.items():
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE matches ADD COLUMN {col_name} {col_type}")
                log(f"Added missing column '{col_name}' to matches table")
            except sqlite3.Error as e:
                log(f"Error adding column '{col_name}': {e}")
    
    conn.commit()

if __name__ == "__main__":
    log("Starting database verification")
    verify_database()
    log("Database verification completed")

