import mysql.connector

class EfficientMediSearch:
    def __init__(self, db_config):
        self.db_config = db_config
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(
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
            'healthid': 'HEALTHID_PATTERN',
            'blood_group': 'BLOOD_GROUP_PATTERN', 
            'limit': 'LIMIT_PATTERN'
        }
    
    def _setup_keywords(self):
        self.keyword_map = {
            'doctor': ['doctor', 'dr', 'specialist', 'physician'],
            'admission': ['admission', 'admitted', 'admit', 'discharge'],
            'billing': ['bill', 'billing', 'payment', 'paid', 'amount'],
            'patient': ['patient', 'patients', 'people']
        }
        
        self.medical_terms = {
            'cities': [
                'pune', 'mumbai', 'delhi', 'bangalore', 'chennai', 
                'kolkata', 'hyderabad', 'ahmedabad', 'jaipur', 'lucknow'
            ]
        }
        
        self.specializations = {
            'cardiology': 'Cardiology', 'heart': 'Cardiology',
            'dermatology': 'Dermatology', 'skin': 'Dermatology',
            'orthopedics': 'Orthopedics', 'bone': 'Orthopedics'
        }
        
        self.payment_modes = {
            'cash': 'Cash', 'card': 'Card', 'upi': 'UPI', 'insurance': 'Insurance'
        }

    def _manual_lower(self, text):
        """Manual lowercase conversion"""
        if text is None:
            return ""
        result = []
        for char in text:
            if 'A' <= char <= 'Z':
                result.append(chr(ord(char) + 32))
            else:
                result.append(char)
        return ''.join(result)

    def _manual_strip(self, text):
        """Manual whitespace removal"""
        if text is None:
            return ""
        
        # Find start (skip whitespace)
        start = 0
        while start < len(text) and text[start] in ' \t\n\r':
            start += 1
        
        # Find end (skip whitespace)
        end = len(text)
        while end > start and text[end-1] in ' \t\n\r':
            end -= 1
        
        return text[start:end]

    def _manual_any_contains(self, text, keyword_list):
        """Manual any() + contains check"""
        for keyword in keyword_list:
            if self._manual_contains(text, keyword):
                return True
        return False

    def _manual_contains(self, text, keyword):
        """Manual substring search"""
        if not text or not keyword:
            return False
        
        text_len = len(text)
        keyword_len = len(keyword)
        
        for i in range(text_len - keyword_len + 1):
            match = True
            for j in range(keyword_len):
                if text[i + j] != keyword[j]:
                    match = False
                    break
            if match:
                return True
        return False

    def _extract_blood_group(self, text):
        """Manual blood group extraction"""
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
        text_upper = self._manual_upper(text)
        
        for bg in blood_groups:
            if self._manual_contains(text_upper, bg):
                return bg
        return None

    def _manual_upper(self, text):
        """Manual uppercase conversion"""
        if text is None:
            return ""
        result = []
        for char in text:
            if 'a' <= char <= 'z':
                result.append(chr(ord(char) - 32))
            else:
                result.append(char)
        return ''.join(result)

    def _extract_limit(self, input_lower):
        """Manual limit extraction"""
        limit_words = ['last', 'latest', 'recent', 'top', 'first']
        
        # Find limit word
        limit_word = None
        for word in limit_words:
            if self._manual_contains(input_lower, word):
                limit_word = word
                break
        
        if not limit_word:
            return None
        
        # Extract number after limit word
        words = self._manual_split(input_lower)
        for i in range(len(words)):
            if words[i] == limit_word and i + 1 < len(words):
                next_word = words[i + 1]
                if self._is_number(next_word):
                    return int(next_word)
        return None

    def _manual_split(self, text):
        """Manual string split"""
        if not text:
            return []
        
        words = []
        current_word = []
        in_word = False
        
        for char in text:
            if char in ' \t\n\r':
                if in_word:
                    words.append(''.join(current_word))
                    current_word = []
                    in_word = False
            else:
                current_word.append(char)
                in_word = True
        
        if current_word:
            words.append(''.join(current_word))
        
        return words

    def _is_number(self, text):
        """Check if string is a number"""
        if not text:
            return False
        
        for char in text:
            if char < '0' or char > '9':
                return False
        return True

    def _get_city_condition(self, input_lower):
        """Extract city condition from query"""
        for city in self.medical_terms['cities']:
            if self._manual_contains(input_lower, city):
                return {
                    'condition': "Address LIKE %s",
                    'param': '%' + self._manual_upper_first(city) + '%'
                }
        return None

    def _manual_upper_first(self, text):
        """Manual capitalize first letter"""
        if not text:
            return ""
        if len(text) == 1:
            return self._manual_upper(text)
        return self._manual_upper(text[0]) + text[1:]

    def smart_search(self, user_input):
        input_lower = self._manual_lower(self._manual_strip(user_input))
        
        # HealthID detection (simplified)
        health_id = self._extract_health_id(user_input)
        if health_id:
            return self._healthid_query(health_id, input_lower)
        
        # Check for complex patient queries
        if (self._manual_any_contains(input_lower, ['patient', 'patients']) and 
            self._is_complex_query(input_lower)):
            return self._handle_complex_patient_query(input_lower)
        
        # Route by keyword categories
        for category in self.keyword_map:
            keywords = self.keyword_map[category]
            if self._manual_any_contains(input_lower, keywords):
                method_name = '_' + category + '_query'
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    return method(input_lower)
        
        return self._patient_query(input_lower)

    def _extract_health_id(self, text):
        """Manual HealthID extraction"""
        if len(text) < 10:
            return None
        
        # Look for pattern: 2 letters + 8 digits
        for i in range(len(text) - 9):
            # Check first 2 are uppercase letters
            valid = True
            for j in range(2):
                if not ('A' <= text[i+j] <= 'Z'):
                    valid = False
                    break
            
            if valid:
                # Check next 8 are digits
                for j in range(2, 10):
                    if not ('0' <= text[i+j] <= '9'):
                        valid = False
                        break
                
                if valid:
                    return text[i:i+10]
        
        return None

    def _is_complex_query(self, input_lower):
        """Check if query has multiple filters"""
        filters_count = 0
        
        # Gender filter
        if (self._manual_contains(input_lower, 'male') or 
            self._manual_contains(input_lower, 'female')):
            filters_count += 1
        
        # Blood group filter
        if self._extract_blood_group(input_lower):
            filters_count += 1
        
        # City filter
        if any(self._manual_contains(input_lower, city) for city in self.medical_terms['cities']):
            filters_count += 1
        
        return filters_count >= 2

    def _handle_complex_patient_query(self, input_lower):
        """Handle multiple filters for patient queries"""
        limit = self._extract_limit(input_lower) or 10
        conditions = []
        params = []
        
        # Gender filter
        if self._manual_contains(input_lower, 'male'):
            conditions.append("Gender = 'M'")
        elif self._manual_contains(input_lower, 'female'):
            conditions.append("Gender = 'F'")
        
        # Blood group filter
        blood_group = self._extract_blood_group(input_lower)
        if blood_group:
            conditions.append("BloodGroup = %s")
            params.append(blood_group)
        
        # City filter
        city_condition = self._get_city_condition(input_lower)
        if city_condition:
            conditions.append(city_condition['condition'])
            params.append(city_condition['param'])
        
        # Build the SQL query
        if conditions:
            where_clause = self._manual_join(conditions, " AND ")
            sql = "SELECT * FROM patient WHERE " + where_clause + " ORDER BY AdmissionDate DESC LIMIT %s"
            params.append(limit)
            return sql, params
        
        # Fallback to simple query
        return self._patient_query(input_lower)

    def _manual_join(self, items, separator):
        """Manual list joining"""
        if not items:
            return ""
        
        result = []
        for i, item in enumerate(items):
            if i > 0:
                result.append(separator)
            result.append(item)
        
        return ''.join(result)

    def _healthid_query(self, health_id, input_lower):
        if self._manual_contains(input_lower, 'admission'):
            query = """
                SELECT a.AdmissionID, p.Name, r.RoomType, a.AdmitDate, a.DischargeDate
                FROM admission a
                JOIN patient p ON a.HealthID = p.HealthID
                JOIN room r ON a.RoomID = r.RoomID
                WHERE p.HealthID = %s
                ORDER BY a.AdmitDate DESC
            """
        elif self._manual_contains(input_lower, 'billing'):
            query = """
                SELECT b.BillID, p.Name, b.TotalAmount, b.PaymentMode, b.PaymentDate
                FROM billing b
                JOIN patient p ON b.HealthID = p.HealthID
                WHERE p.HealthID = %s
                ORDER BY b.PaymentDate DESC
            """
        else:
            query = "SELECT * FROM patient WHERE HealthID = %s"
        
        return query, [health_id]

    def _doctor_query(self, input_lower):
        limit = self._extract_limit(input_lower) or 10
        
        for key, spec in self.specializations.items():
            if self._manual_contains(input_lower, key):
                return "SELECT * FROM doctor WHERE Specialization = %s LIMIT %s", [spec, limit]
        
        return "SELECT * FROM doctor LIMIT %s", [limit]

    def _admission_query(self, input_lower):
        limit = self._extract_limit(input_lower) or 10
        
        if (self._manual_contains(input_lower, 'current') or 
            self._manual_contains(input_lower, 'active') or 
            self._manual_contains(input_lower, 'ongoing')):
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
            if self._manual_contains(input_lower, key):
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
        if (self._manual_contains(input_lower, 'total') or 
            self._manual_contains(input_lower, 'sum') or 
            self._manual_contains(input_lower, 'revenue')):
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
        blood_group = self._extract_blood_group(input_lower)
        if blood_group:
            return "SELECT * FROM patient WHERE BloodGroup = %s ORDER BY AdmissionDate DESC LIMIT %s", [blood_group, limit]
        
        # Gender filter
        if self._manual_contains(input_lower, 'female'):
            return "SELECT * FROM patient WHERE Gender = 'F' ORDER BY AdmissionDate DESC LIMIT %s", [limit]
        elif self._manual_contains(input_lower, 'male'):
            return "SELECT * FROM patient WHERE Gender = 'M' ORDER BY AdmissionDate DESC LIMIT %s", [limit]
        
        # City filter
        city_condition = self._get_city_condition(input_lower)
        if city_condition:
            return "SELECT * FROM patient WHERE Address LIKE %s ORDER BY AdmissionDate DESC LIMIT %s", [city_condition['param'], limit]
        
        # Count query
        if (self._manual_contains(input_lower, 'count') or 
            self._manual_contains(input_lower, 'how many') or 
            self._manual_contains(input_lower, 'total')):
            return "SELECT COUNT(*) as TotalPatients FROM patient", []
        
        # Default: all patients
        return "SELECT * FROM patient ORDER BY AdmissionDate DESC LIMIT %s", [limit]

    def execute_query(self, query_data):
        """Execute query with parameters"""
        if type(query_data) == tuple:
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
            return "ERROR: " + str(e)

    def format_results(self, results, original_query):
        if type(results) == str and results.startswith("ERROR"):
            return "ERROR: " + results
        
        if not results:
            return "No results found"
        
        output = []
        output.append("")
        output.append("Found " + str(len(results)) + " results for: '" + original_query + "'")
        output.append("=" * 50)
        
        for i in range(len(results)):
            output.append("Record " + str(i + 1) + ":")
            row = results[i]
            for key in row:
                value = row[key]
                if value is not None:
                    display_key = key.replace('_', ' ')
                    # Manual title case
                    words = display_key.split(' ')
                    title_words = []
                    for word in words:
                        if word:
                            title_words.append(self._manual_upper(word[0]) + word[1:].lower())
                        else:
                            title_words.append('')
                    display_key = ' '.join(title_words)
                    output.append("   " + display_key + ": " + str(value))
            output.append("")
        
        return '\n'.join(output)

def main():
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'medilocker_5', 
        'user': 'root',
        'password': '12345678'
    }
    
    search = EfficientMediSearch(DB_CONFIG)
    
    print("")
    print("=" * 50)
    print("MEDILOCKER SMART SEARCH SYSTEM")
    print("=" * 50)
    
    print("")
    print("QUERY EXAMPLES:")
    print("Simple: 'male patients', 'patients B+', 'patients from Pune'")
    print("Complex: 'male patients from Pune with B+ blood group'")
    print("Billing: 'cash payments', 'total billing'")
    print("General: 'MH20230001', 'count patients', 'latest 5'")
    print("Type 'quit' to exit")
    print("=" * 50)
    
    while True:
        user_input = input("\nQuery: ")
        user_input = user_input.strip()
        
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