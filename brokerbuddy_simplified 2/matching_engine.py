"""
Simplified Matching Engine for BrokerBuddy

This module implements the matching algorithm for the simplified BrokerBuddy application.
It matches clients with lenders based on various criteria and calculates match scores.
"""

import sqlite3
import json
from datetime import datetime

class MatchingEngine:
    def __init__(self, db_connection):
        """Initialize the matching engine with a database connection."""
        self.conn = db_connection
        self.conn.row_factory = sqlite3.Row
    
    def find_matching_lenders(self, client_data):
        """
        Find lenders that match the client's criteria.
        
        Args:
            client_data: Dictionary containing client information
            
        Returns:
            List of matching lenders with match scores and details
        """
        cursor = self.conn.cursor()
        
        # Get all active lenders
        cursor.execute('SELECT * FROM lenders WHERE active = 1')
        lenders = cursor.fetchall()
        
        matches = []
        
        for lender in lenders:
            # Get lender guidelines
            cursor.execute('SELECT * FROM lender_guidelines WHERE lender_id = ?', (lender['id'],))
            guidelines = cursor.fetchone()
            
            if not guidelines:
                continue
            
            # Calculate match score
            match_score, match_details = self._calculate_match_score(client_data, lender, guidelines)
            
            # If match score is above threshold, add to matches
            if match_score > 0:
                matches.append({
                    'lender_id': lender['id'],
                    'lender_name': lender['name'],
                    'description': lender['description'],
                    'match_score': match_score,
                    'match_details': match_details
                })
        
        # Sort matches by score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches
    
    def _calculate_match_score(self, client_data, lender, guidelines):
        """
        Calculate a match score between a client and a lender.
        
        Args:
            client_data: Dictionary containing client information
            lender: Lender record
            guidelines: Lender guidelines record
            
        Returns:
            Tuple of (match_score, match_details)
        """
        match_details = []
        total_score = 0
        max_possible_score = 0
        
        # Credit Score (25% weight)
        if 'credit_score' in client_data and client_data['credit_score'] and guidelines['min_credit_score']:
            max_possible_score += 25
            client_credit = self._parse_credit_score(client_data['credit_score'])
            
            if client_credit >= guidelines['min_credit_score']:
                total_score += 25
                match_details.append({
                    'criterion': 'credit_score',
                    'result': 'Match',
                    'reason': f"Client's credit score ({client_credit}) meets or exceeds lender requirement ({guidelines['min_credit_score']})"
                })
            else:
                match_details.append({
                    'criterion': 'credit_score',
                    'result': 'No Match',
                    'reason': f"Client's credit score ({client_credit}) is below lender requirement ({guidelines['min_credit_score']})"
                })
        
        # Time in Business (25% weight)
        if 'time_in_business' in client_data and client_data['time_in_business'] and guidelines['min_time_in_business']:
            max_possible_score += 25
            client_time = self._parse_time_in_business(client_data['time_in_business'])
            
            if client_time >= guidelines['min_time_in_business']:
                total_score += 25
                match_details.append({
                    'criterion': 'time_in_business',
                    'result': 'Match',
                    'reason': f"Client's time in business ({client_time} months) meets or exceeds lender requirement ({guidelines['min_time_in_business']} months)"
                })
            else:
                match_details.append({
                    'criterion': 'time_in_business',
                    'result': 'No Match',
                    'reason': f"Client's time in business ({client_time} months) is below lender requirement ({guidelines['min_time_in_business']} months)"
                })
        
        # Equipment Cost/Loan Amount (25% weight)
        if 'equipment_cost' in client_data and client_data['equipment_cost'] and lender['min_amount'] and lender['max_amount']:
            max_possible_score += 25
            client_amount = float(client_data['equipment_cost'])
            
            if client_amount >= lender['min_amount'] and client_amount <= lender['max_amount']:
                total_score += 25
                match_details.append({
                    'criterion': 'loan_amount',
                    'result': 'Match',
                    'reason': f"Client's equipment cost (${client_amount:,.2f}) is within lender's range (${lender['min_amount']:,.2f} - ${lender['max_amount']:,.2f})"
                })
            else:
                match_details.append({
                    'criterion': 'loan_amount',
                    'result': 'No Match',
                    'reason': f"Client's equipment cost (${client_amount:,.2f}) is outside lender's range (${lender['min_amount']:,.2f} - ${lender['max_amount']:,.2f})"
                })
        
        # Equipment Type (15% weight)
        if 'equipment_type' in client_data and client_data['equipment_type'] and guidelines['equipment_types']:
            max_possible_score += 15
            equipment_types = guidelines['equipment_types'].lower().split(',')
            client_equipment = client_data['equipment_type'].lower()
            
            if any(eq_type.strip() in client_equipment for eq_type in equipment_types) or 'all' in equipment_types:
                total_score += 15
                match_details.append({
                    'criterion': 'equipment_type',
                    'result': 'Match',
                    'reason': f"Client's equipment type ({client_equipment}) is accepted by this lender"
                })
            else:
                match_details.append({
                    'criterion': 'equipment_type',
                    'result': 'No Match',
                    'reason': f"Client's equipment type ({client_equipment}) is not specifically listed in lender's accepted types"
                })
        
        # Industry (10% weight)
        if 'industry' in client_data and client_data['industry'] and lender['industries_served']:
            max_possible_score += 10
            industries = lender['industries_served'].lower().split(',')
            client_industry = client_data['industry'].lower()
            
            if any(ind.strip() in client_industry for ind in industries) or 'all' in industries:
                total_score += 10
                match_details.append({
                    'criterion': 'industry',
                    'result': 'Match',
                    'reason': f"Client's industry ({client_industry}) is served by this lender"
                })
            else:
                match_details.append({
                    'criterion': 'industry',
                    'result': 'No Match',
                    'reason': f"Client's industry ({client_industry}) is not specifically listed in lender's served industries"
                })
        
        # Calculate final percentage score
        final_score = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        
        return final_score, match_details
    
    def _parse_credit_score(self, credit_score):
        """Parse credit score from various formats."""
        try:
            # Handle range format (e.g., "650-700")
            if '-' in credit_score:
                parts = credit_score.split('-')
                return int(parts[0].strip())
            
            # Handle plus format (e.g., "700+")
            if '+' in credit_score:
                return int(credit_score.replace('+', '').strip())
            
            # Handle plain number
            return int(credit_score.strip())
        except (ValueError, AttributeError):
            return 0
    
    def _parse_time_in_business(self, time_in_business):
        """Parse time in business to months."""
        try:
            time_str = str(time_in_business).lower()
            
            # Handle "X years" format
            if 'year' in time_str:
                years = time_str.replace('years', '').replace('year', '').strip()
                if '+' in years:
                    years = years.replace('+', '')
                return int(float(years)) * 12
            
            # Handle "X months" format
            if 'month' in time_str:
                months = time_str.replace('months', '').replace('month', '').strip()
                if '+' in months:
                    months = months.replace('+', '')
                return int(months)
            
            # Handle numeric format (assume months)
            return int(float(time_str))
        except (ValueError, AttributeError):
            return 0
    
    def save_match_results(self, client_id, matches):
        """
        Save match results to the database.
        
        Args:
            client_id: ID of the client
            matches: List of matching lenders with scores and details
            
        Returns:
            Boolean indicating success
        """
        cursor = self.conn.cursor()
        
        try:
            # Delete any existing matches for this client
            cursor.execute('DELETE FROM matches WHERE client_id = ?', (client_id,))
            
            # Insert new matches
            for match in matches:
                cursor.execute('''
                INSERT INTO matches (
                    client_id, lender_id, match_score, 
                    match_reasons, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    client_id,
                    match['lender_id'],
                    match['match_score'],
                    json.dumps(match['match_details']),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving match results: {e}")
            self.conn.rollback()
            return False
