"""
Simplified Database Schema for BrokerBuddy

This module defines the database schema for the simplified BrokerBuddy application.
It includes four main tables: clients, lenders, lender_guidelines, and matches.
"""

import sqlite3
import os
import datetime

class BrokerBuddyDB:
    def __init__(self, db_path):
        """Initialize the database connection."""
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def initialize_database(self):
        """Create the database tables if they don't exist."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Create clients table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            credit_score TEXT,
            time_in_business TEXT,
            monthly_revenue REAL,
            equipment_type TEXT,
            equipment_cost REAL,
            industry TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create lenders table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            min_amount REAL,
            max_amount REAL,
            industries_served TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            website TEXT,
            logo_url TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create lender_guidelines table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lender_guidelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lender_id INTEGER NOT NULL,
            min_credit_score INTEGER,
            min_time_in_business INTEGER,
            min_monthly_revenue REAL,
            equipment_types TEXT,
            max_term_length INTEGER,
            interest_rate_range TEXT,
            approval_speed TEXT,
            documentation_required TEXT,
            special_programs TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lender_id) REFERENCES lenders (id)
        )
        ''')
        
        # Create matches table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            lender_id INTEGER NOT NULL,
            match_score REAL,
            match_reasons TEXT,
            caution_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (lender_id) REFERENCES lenders (id)
        )
        ''')
        
        # Create indexes for frequently queried fields
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_credit_score ON clients (credit_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_time_in_business ON clients (time_in_business)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_equipment_type ON clients (equipment_type)')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lender_guidelines_min_credit_score ON lender_guidelines (min_credit_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lender_guidelines_min_time_in_business ON lender_guidelines (min_time_in_business)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lender_guidelines_lender_id ON lender_guidelines (lender_id)')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_matches_client_id ON matches (client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_matches_lender_id ON matches (lender_id)')
        
        conn.commit()
        self.close()
        
    def import_existing_lenders(self, old_db_path):
        """Import lenders from the existing database."""
        if not os.path.exists(old_db_path):
            return False
            
        old_conn = sqlite3.connect(old_db_path)
        old_conn.row_factory = sqlite3.Row
        old_cursor = old_conn.cursor()
        
        new_conn = self.connect()
        new_cursor = new_conn.cursor()
        
        # Get lenders from old database
        old_cursor.execute('SELECT * FROM lenders')
        old_lenders = old_cursor.fetchall()
        
        # Get criteria categories from old database
        old_cursor.execute('SELECT * FROM criteria_categories')
        old_categories = old_cursor.fetchall()
        
        # Get lender criteria from old database
        old_cursor.execute('SELECT * FROM lender_criteria')
        old_criteria = old_cursor.fetchall()
        
        # Map old lenders to new schema
        for old_lender in old_lenders:
            # Insert into new lenders table
            new_cursor.execute('''
            INSERT INTO lenders (
                name, description, min_amount, max_amount, 
                industries_served, active
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                old_lender['name'],
                old_lender['program_type'],  # Use program_type as description
                0,  # Default min_amount
                0,  # Default max_amount
                '',  # Default industries_served
                1   # Active by default
            ))
            
            new_lender_id = new_cursor.lastrowid
            
            # Get criteria for this lender
            lender_criteria = [c for c in old_criteria if c['lender_id'] == old_lender['id']]
            
            # Map criteria to new schema
            min_credit_score = None
            min_time_in_business = None
            equipment_types = None
            
            for criterion in lender_criteria:
                category_id = criterion['category_id']
                category = next((c for c in old_categories if c['id'] == category_id), None)
                
                if category:
                    category_name = category['name']
                    value = criterion['value']
                    
                    if category_name == 'personal_credit':
                        # Extract numeric value from credit score range
                        if '+' in value:
                            min_credit_score = int(value.replace('+', ''))
                        elif '-' in value:
                            min_credit_score = int(value.split('-')[0])
                    
                    elif category_name == 'time_in_business':
                        # Extract numeric value from time in business
                        if 'years' in value.lower() or 'year' in value.lower():
                            years = value.lower().replace('years', '').replace('year', '').strip()
                            if '+' in years:
                                min_time_in_business = int(years.replace('+', '')) * 12
                            else:
                                min_time_in_business = int(float(years)) * 12
                        elif 'months' in value.lower() or 'month' in value.lower():
                            months = value.lower().replace('months', '').replace('month', '').strip()
                            min_time_in_business = int(months)
                    
                    elif category_name == 'amount_considered':
                        # Extract numeric values from amount range
                        if '-' in value:
                            parts = value.replace('$', '').replace('k', '000').replace('K', '000').split('-')
                            min_amount = float(parts[0].strip())
                            max_amount = float(parts[1].strip())
                            
                            # Update lender with amount range
                            new_cursor.execute('''
                            UPDATE lenders SET min_amount = ?, max_amount = ? WHERE id = ?
                            ''', (min_amount, max_amount, new_lender_id))
                    
                    elif category_name == 'equipment_type' or category_name == 'collateral_type':
                        equipment_types = value
            
            # Insert into lender_guidelines
            new_cursor.execute('''
            INSERT INTO lender_guidelines (
                lender_id, min_credit_score, min_time_in_business, 
                equipment_types
            ) VALUES (?, ?, ?, ?)
            ''', (
                new_lender_id,
                min_credit_score or 0,
                min_time_in_business or 0,
                equipment_types or ''
            ))
        
        new_conn.commit()
        old_conn.close()
        self.close()
        
        return True
