import re
import mysql.connector
from mysql.connector import pooling

class EfficientMediSearch:
    def __init__(self, db_config):
        self.db_config = db_config
        try:
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="medisearch_pool",
                pool_size=5,
                **db_config
            )
        except:
            self.connection_pool = None
        self._setup_patterns()
        self._setup_keywords()


    def _setup_patterns(self):

        self.patterns = {
            'healthid': re.compile(r'([A-Z]{2}\d{8})', re.IGNORECASE),
            'blood_group': re.compile(r'([ABO][+-]|[ABO]B?[+-])', re.IGNORECASE),
            'limit': re.compile(r'(last|latest|recent|top|first)\s+(\d+)', re.IGNORECASE)
        }
    
    def _setup_keywords(self):
        self.keyword_map = {
            'doctor': ['doctor', 'dr', 'specialist', 'physician'],
            'admission': ['admission', 'admitted', 'admit', 'discharge'],
            'billing': ['bill', 'billing', 'payment', 'paid', 'amount'],
            'patient': ['patient', 'patients', 'people']
        }
        
        # Add cities list for complex queries
        self.medical_terms = {
            'cities': [
                'pune', 'mumbai', 'delhi', 'bangalore', 'chennai', 
                'kolkata', 'hyderabad', 'ahmedabad', 'jaipur', 'lucknow',
                'nagpur', 'thane', 'nashik', 'surat', 'kanpur'
            ]
        }
        
        self.specializations = {
            'cardiology': 'Cardiology', 'heart': 'Cardiology',
            'dermatology': 'Dermatology', 'skin': 'Dermatology',
            'orthopedics': 'Orthopedics', 'bone': 'Orthopedics',
            'neurology': 'Neurology', 'brain': 'Neurology',
            'pediatrics': 'Pediatrics', 'child': 'Pediatrics'
        }
        
        self.payment_modes = {
            'cash': 'Cash', 'card': 'Card', 'upi': 'UPI', 'insurance': 'Insurance'
        }

           #A#
    def smart_search(self, user_input):
        input_lower = user_input.lower().strip()
        
        # HealthID has highest priority
        health_match = self.patterns['healthid'].search(user_input)
        if health_match:
            return self._healthid_query(health_match.group(1).upper(), input_lower)
        
        # Check for complex patient queries FIRST (NEW FEATURE)
        if any(word in input_lower for word in ['patient', 'patients']) and self._is_complex_query(input_lower):
            return self._handle_complex_patient_query(input_lower)
        
        # Route by keyword categories
        for category, keywords in self.keyword_map.items():
            if any(keyword in input_lower for keyword in keywords):
                return getattr(self, f'_{category}_query')(input_lower)
        
        return self._patient_query(input_lower)
    
       

    def _is_complex_query(self, input_lower):
        """Check if query has multiple filters"""
        filters_count = 0
        
        # Count different types of filters
        if any(gender in input_lower for gender in ['male', 'female']):
            filters_count += 1
        
        blood_match = self.patterns['blood_group'].search(input_lower)
        if blood_match:
            filters_count += 1
        
        if any(city in input_lower for city in self.medical_terms['cities']):
            filters_count += 1
        
        return filters_count >= 2

    def _handle_complex_patient_query(self, input_lower):
        """Handle multiple filters for patient queries"""
        limit = self._extract_limit(input_lower) or 10
        conditions = []
        params = []
        
        # Gender filter
        if 'male' in input_lower:
            conditions.append("Gender = 'M'")
        elif 'female' in input_lower:
            conditions.append("Gender = 'F'")
        
        # Blood group filter
        blood_match = self.patterns['blood_group'].search(input_lower)
        if blood_match:
            conditions.append("BloodGroup = %s")
            params.append(blood_match.group(1).upper())
        
        # City filter
        city_condition = self._get_city_condition(input_lower)
        if city_condition:
            conditions.append(city_condition['condition'])
            params.append(city_condition['param'])
        
        # Build the SQL query
        if conditions:
            where_clause = " AND ".join(conditions)
            sql = f"SELECT * FROM patient WHERE {where_clause} ORDER BY AdmissionDate DESC LIMIT %s"
            params.append(limit)
            return sql, params
        
        # Fallback to simple query
        return self._patient_query(input_lower)

    def _get_city_condition(self, input_lower):
        """Extract city condition from query"""
        for city in self.medical_terms['cities']:
            if city in input_lower:
                return {
                    'condition': "Address LIKE %s",
                    'param': f'%{city.title()}%'
                }
        return None
    
         #T#

    def _healthid_query(self, health_id, input_lower):
        base_queries = {
            'admission': """
                SELECT a.AdmissionID, p.Name, r.RoomType, a.AdmitDate, a.DischargeDate
                FROM admission a
                JOIN patient p ON a.HealthID = p.HealthID
                JOIN room r ON a.RoomID = r.RoomID
                WHERE p.HealthID = %s
                ORDER BY a.AdmitDate DESC
            """,
            'billing': """
                SELECT b.BillID, p.Name, b.TotalAmount, b.PaymentMode, b.PaymentDate
                FROM billing b
                JOIN patient p ON b.HealthID = p.HealthID
                WHERE p.HealthID = %s
                ORDER BY b.PaymentDate DESC
            """,
            'default': "SELECT * FROM patient WHERE HealthID = %s"
        }
        
        for key, query in base_queries.items():
            if key in input_lower:
                return query, [health_id]
        return base_queries['default'], [health_id]

    def _doctor_query(self, input_lower):
        limit = self._extract_limit(input_lower) or 10
        
        for key, spec in self.specializations.items():
            if key in input_lower:
                return "SELECT * FROM doctor WHERE Specialization = %s LIMIT %s", [spec, limit]
        
        return "SELECT * FROM doctor LIMIT %s", [limit]

    def _admission_query(self, input_lower):
        limit = self._extract_limit(input_lower) or 10
        
        if any(word in input_lower for word in ['current', 'active', 'ongoing']):
            query = """
                SELECT a.AdmissionID, p.Name, r.RoomType, a.AdmitDate
                FROM admission a
                JOIN patient p ON a.HealthID = p.HealthID
                JOIN room r ON a.RoomID = r.RoomID
                WHERE a.DischargeDate IS NULL
                ORDER BY a.AdmitDate DESC
                LIMIT %s
            """
        else:
            query = """
                SELECT a.AdmissionID, p.Name, r.RoomType, a.AdmitDate, a.DischargeDate
                FROM admission a
                JOIN patient p ON a.HealthID = p.HealthID
                JOIN room r ON a.RoomID = r.RoomID
                ORDER BY a.AdmitDate DESC
                LIMIT %s
            """
        
        return query, [limit]

    def _billing_query(self, input_lower):
        limit = self._extract_limit(input_lower) or 10
        
        # Payment mode filter
        for key, mode in self.payment_modes.items():
            if key in input_lower:
                query = """
                    SELECT b.BillID, p.Name, b.TotalAmount, b.PaymentMode, b.PaymentDate
                    FROM billing b
                    JOIN patient p ON b.HealthID = p.HealthID
                    WHERE b.PaymentMode = %s
                    ORDER BY b.PaymentDate DESC
                    LIMIT %s
                """
                return query, [mode, limit]
        
        # Summary query
        if any(word in input_lower for word in ['total', 'sum', 'revenue']):
            return """
                SELECT PaymentMode, COUNT(*) as TotalBills, SUM(TotalAmount) as TotalRevenue
                FROM billing
                GROUP BY PaymentMode
                ORDER BY TotalRevenue DESC
            """, []
        
        # Default billing query
        query = """
            SELECT b.BillID, p.Name, b.TotalAmount, b.PaymentMode, b.PaymentDate
            FROM billing b
            JOIN patient p ON b.HealthID = p.HealthID
            ORDER BY b.PaymentDate DESC
            LIMIT %s
        """
        return query, [limit]

    def _patient_query(self, input_lower):
        limit = self._extract_limit(input_lower) or 10
        
        # Blood group filter
        blood_match = self.patterns['blood_group'].search(input_lower)
        if blood_match:
            blood_group = blood_match.group(1).upper()
            return "SELECT * FROM patient WHERE BloodGroup = %s ORDER BY AdmissionDate DESC LIMIT %s", [blood_group, limit]
        
        # Gender filter
        if 'female' in input_lower:
            return "SELECT * FROM patient WHERE Gender = 'F' ORDER BY AdmissionDate DESC LIMIT %s", [limit]
        elif 'male' in input_lower:
            return "SELECT * FROM patient WHERE Gender = 'M' ORDER BY AdmissionDate DESC LIMIT %s", [limit]
        
        # City filter - ADDED THIS
        city_condition = self._get_city_condition(input_lower)
        if city_condition:
            return "SELECT * FROM patient WHERE Address LIKE %s ORDER BY AdmissionDate DESC LIMIT %s", [city_condition['param'], limit]
        
        # Count query
        if any(word in input_lower for word in ['count', 'how many', 'total']):
            return "SELECT COUNT(*) as TotalPatients FROM patient", []
        
        # Default: all patients
        return "SELECT * FROM patient ORDER BY AdmissionDate DESC LIMIT %s", [limit]

    def _extract_limit(self, input_lower):
        match = self.patterns['limit'].search(input_lower)
        return int(match.group(2)) if match else None

         #L#

    def execute_query(self, query_data):
        """Execute query with parameters"""
        if isinstance(query_data, tuple):
            sql, params = query_data
        else:
            sql, params = query_data, []
        
        try:
            if self.connection_pool:
                conn = self.connection_pool.get_connection()
            else:
                conn = mysql.connector.connect(**self.db_config)
                
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            return f"ERROR: {str(e)}"
        

    def format_results(self, results, original_query):
        if isinstance(results, str):
            return f"ERROR: {results}"
        
        if not results:
            return "No results found"
        
        output = [f"\nFound {len(results)} results for: '{original_query}'", "=" * 50]
        
        for i, row in enumerate(results, 1):
            output.append(f"Record {i}:")
            output.extend(f"   {key.replace('_', ' ').title()}: {value}" 
                         for key, value in row.items() if value is not None)
            output.append("")
        
        return "\n".join(output)

def main():
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'medilocker_5', 
        'user': 'root',
        'password': '12345678'
    }
    
    search = EfficientMediSearch(DB_CONFIG)
    
    print("\n" + "=" * 50)
    print("MEDILOCKER SMART SEARCH SYSTEM")
    print("=" * 50)
    
    print("\nQUERY EXAMPLES:")
    print("Simple: 'male patients', 'patients B+', 'patients from Pune'")
    print("Complex: 'male patients from Pune with B+ blood group'")
    print("Billing: 'cash payments', 'total billing'")
    print("General: 'MH20230001', 'count patients', 'latest 5'")
    print("Type 'quit' to exit")
    print("=" * 50)
    
    while True:
        user_input = input("\nQuery: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("Thank you for using MediLocker!")
            break
        
        if not user_input:
            continue
        
        # Get query and execute
        query_data = search.smart_search(user_input)
        results = search.execute_query(query_data)
        print(search.format_results(results, user_input))

if __name__ == "__main__":
    main()