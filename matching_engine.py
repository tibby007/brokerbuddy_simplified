import sqlite3
import json
from datetime import datetime

def safe_convert_to_number(value):
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        clean_value = ''.join(c for c in value if c.isdigit() or c == '.')
        if not clean_value:
            return 0
        try:
            return float(clean_value)
        except (ValueError, TypeError):
            return 0
    return 0

class MatchingEngine:
    def __init__(self, db_connection):
        self.conn = db_connection
        self.conn.row_factory = sqlite3.Row

    def find_matching_lenders(self, client_data):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM lenders')
        lenders = cursor.fetchall()

        matches = []

        for lender in lenders:
            cursor.execute('SELECT * FROM lender_guidelines WHERE lender_id = ?', (lender['lender_id'],))
            guidelines = cursor.fetchone()

            if not guidelines:
                continue

            result = self._calculate_match_score(client_data, lender, guidelines)
            if result:
                match_score, match_details = result
                if match_score > 0:
                    matches.append({
                        'lender_id': lender['lender_id'],
                        'lender_name': lender['name'],
                        'description': lender['description'],
                        'match_score': match_score,
                        'match_details': match_details
                    })

        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches

    def _calculate_match_score(self, client_data, lender, guidelines):
        match_details = []
        total_score = 0
        max_possible_score = 0

        # Credit Score
        if 'credit_score' in client_data and client_data['credit_score'] and guidelines['min_credit_score']:
            max_possible_score += 25
            client_credit = self._parse_credit_score(client_data['credit_score'])
            min_credit = safe_convert_to_number(guidelines['min_credit_score'])

            if client_credit >= min_credit:
                total_score += 25
                match_details.append({
                    'criterion': 'credit_score',
                    'result': 'Match',
                    'reason': f"Client's credit score ({client_credit}) meets requirement ({min_credit})"
                })
            else:
                match_details.append({
                    'criterion': 'credit_score',
                    'result': 'No Match',
                    'reason': f"Client's credit score ({client_credit}) is below requirement ({min_credit})"
                })

        # Time in Business
        if 'time_in_business' in client_data and client_data['time_in_business'] and guidelines['min_time_in_business']:
            max_possible_score += 25
            client_time = self._parse_time_in_business(client_data['time_in_business'])
            min_time = safe_convert_to_number(guidelines['min_time_in_business'])

            if client_time >= min_time:
                total_score += 25
                match_details.append({
                    'criterion': 'time_in_business',
                    'result': 'Match',
                    'reason': f"Client's time in business ({client_time} months) meets requirement ({min_time} months)"
                })
            else:
                match_details.append({
                    'criterion': 'time_in_business',
                    'result': 'No Match',
                    'reason': f"Client's time in business ({client_time} months) is below requirement ({min_time} months)"
                })

        # Loan Amount (Equipment Cost)
        if 'equipment_cost' in client_data and client_data['equipment_cost'] and guidelines['min_equipment_cost'] and guidelines['max_equipment_cost']:
            max_possible_score += 25
            client_amount = safe_convert_to_number(client_data['equipment_cost'])
            min_amount = safe_convert_to_number(guidelines['min_equipment_cost'])
            max_amount = safe_convert_to_number(guidelines['max_equipment_cost'])

            if min_amount <= client_amount <= max_amount:
                total_score += 25
                match_details.append({
                    'criterion': 'loan_amount',
                    'result': 'Match',
                    'reason': f"Client's equipment cost (${client_amount:,.2f}) is within range (${min_amount:,.2f} - ${max_amount:,.2f})"
                })
            else:
                match_details.append({
                    'criterion': 'loan_amount',
                    'result': 'No Match',
                    'reason': f"Client's equipment cost (${client_amount:,.2f}) is outside range (${min_amount:,.2f} - ${max_amount:,.2f})"
                })

        # Equipment Type
        if 'equipment_type' in client_data and client_data['equipment_type'] and guidelines['equipment_types']:
            max_possible_score += 15
            equipment_types = str(guidelines['equipment_types']).lower().split(',')
            client_equipment = str(client_data['equipment_type']).lower()

            if any(eq_type.strip() in client_equipment for eq_type in equipment_types) or 'all' in equipment_types:
                total_score += 15
                match_details.append({
                    'criterion': 'equipment_type',
                    'result': 'Match',
                    'reason': f"Client's equipment type ({client_equipment}) is accepted"
                })
            else:
                match_details.append({
                    'criterion': 'equipment_type',
                    'result': 'No Match',
                    'reason': f"Client's equipment type ({client_equipment}) is not accepted"
                })

        # Industry
        if 'industry' in client_data and client_data['industry'] and guidelines['industries_accepted']:
            max_possible_score += 10
            industries = str(guidelines['industries_accepted']).lower().split(',')
            client_industry = str(client_data['industry']).lower()

            if any(ind.strip() in client_industry for ind in industries) or 'all' in industries:
                total_score += 10
                match_details.append({
                    'criterion': 'industry',
                    'result': 'Match',
                    'reason': f"Client's industry ({client_industry}) is accepted"
                })
            else:
                match_details.append({
                    'criterion': 'industry',
                    'result': 'No Match',
                    'reason': f"Client's industry ({client_industry}) is not accepted"
                })

        if max_possible_score == 0:
            return None

        final_score = (total_score / max_possible_score * 100)
        return final_score, match_details

    def _parse_credit_score(self, credit_score):
        try:
            credit_str = str(credit_score).lower()
            if '-' in credit_str:
                parts = credit_str.split('-')
                return int(parts[0].strip())
            if '+' in credit_str:
                return int(credit_str.replace('+', '').strip())
            return int(credit_str.strip())
        except (ValueError, AttributeError):
            return 0

    def _parse_time_in_business(self, time_in_business):
        try:
            time_str = str(time_in_business).lower()
            if 'year' in time_str:
                years = time_str.replace('years', '').replace('year', '').strip()
                if '+' in years:
                    years = years.replace('+', '')
                return int(float(years)) * 12
            if 'month' in time_str:
                months = time_str.replace('months', '').replace('month', '').strip()
                if '+' in months:
                    months = months.replace('+', '')
                return int(months)
            return int(float(time_str))
        except (ValueError, AttributeError):
            return 0

    def save_match_results(self, client_id, matches):
        cursor = self.conn.cursor()

        try:
            cursor.execute("PRAGMA table_info(matches)")
            columns = [row[1] for row in cursor.fetchall()]
            match_details_column = 'match_details' if 'match_details' in columns else 'match_reasons'

            cursor.execute('DELETE FROM matches WHERE client_id = ?', (client_id,))

            for match in matches:
                if match_details_column == 'match_details':
                    cursor.execute(f'''
                    INSERT INTO matches (
                        client_id, lender_id, match_score, 
                        match_details, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        client_id,
                        match['lender_id'],
                        match['match_score'],
                        json.dumps(match['match_details']),
                        datetime.now().isoformat()
                    ))
                else:
                    cursor.execute(f'''
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

