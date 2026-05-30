import mysql.connector
from mysql.connector import Error

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Change this to your MySQL username
    'password': '12345678',  # Change this to your MySQL password
    'database': 'medilocker_5'
}

def connect_to_database():
    """Establish connection to MySQL database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("✓ Successfully connected to MediLocker database\n")
            return connection
    except Error as e:
        print(f"✗ Error connecting to database: {e}")
        return None

def execute_query(connection, query):
    """Execute SQL query and return results"""
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        return columns, results
    except Error as e:
        print(f"✗ Error executing query: {e}")
        return None, None

def display_results(columns, results):
    """Display query results in a formatted table"""
    if not results:
        print("No data found.")
        return
    
    # Print column headers
    header = " | ".join(columns)
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in results:
        print(" | ".join(str(value) for value in row))
    print()

def show_help():
    """Display help message with example queries"""
    print("\n" + "=" * 60)
    print("                    HELP MENU")
    print("=" * 60)
    print("\n📋 Examples of queries you can ask:")
    print("-" * 60)
    print("  - Show all patients")
    print("  - Show all doctors")
    print("  - Count patients")
    print("  - Show patient name Aarav")
    print("  - Show patient HealthID MH20230001")
    print("  - Show male patients")
    print("  - Show female patients")
    print("  - Show patients blood group B+")
    print("  - Show doctor cardiology")
    print("  - Show patients from Pune")
    print("  - Show admissions")
    print("  - Show billing")
    print("  - Show insurance")
    print("  - Show prescriptions")
    print("  - Show visits")
    print("  - Show ICU rooms")
    print("  - Show general rooms")
    print("  - Show admitted patients")
    print("  - Show total billing amount")
    print("  - Show cash payments")
    print("  - Show card payments")
    print("  - Type 'help' to see this menu again")
    print("  - Type 'exit' to quit")
    print("=" * 60 + "\n")

def nl_to_sql(natural_query):
    """Convert natural language query to SQL"""
    query = natural_query.lower().strip()
    
    # Pattern 1: Show/Display all patients
    if "show all patient" in query or "display all patient" in query or "list all patient" in query:
        return "SELECT * FROM patient;"
    
    # Pattern 2: Show all doctors
    if "show all doctor" in query or "display all doctor" in query or "list all doctor" in query:
        return "SELECT * FROM doctor;"
    
    # Pattern 3: Show patient details by name
    if "show patient" in query and "name" in query:
        # Extract name from query
        words = query.split()
        try:
            name_index = words.index("name") + 1
            if name_index < len(words):
                name = words[name_index].capitalize()
                return f"SELECT * FROM patient WHERE Name LIKE '%{name}%';"
        except:
            pass
    
    # Pattern 4: Show patient by HealthID
    if "healthid" in query or "health id" in query:
        words = query.replace("-", " ").split()
        for word in words:
            if word.startswith("mh"):
                health_id = word.upper()
                return f"SELECT * FROM patient WHERE HealthID = '{health_id}';"
    
    # Pattern 5: Show admissions
    if "show admission" in query or "display admission" in query:
        return "SELECT * FROM admission;"
    
    # Pattern 6: Count patients
    if "count patient" in query or "how many patient" in query or "number of patient" in query:
        return "SELECT COUNT(*) as TotalPatients FROM patient;"
    
    # Pattern 7: Show billing information
    if "show bill" in query or "billing" in query:
        return "SELECT * FROM billing;"
    
    # Pattern 8: Show insurance details
    if "show insurance" in query or "insurance" in query:
        return "SELECT * FROM insurance;"
    
    # Pattern 9: Show prescriptions
    if "show prescription" in query or "prescription" in query:
        return "SELECT * FROM prescription;"
    
    # Pattern 10: Show visits
    if "show visit" in query or "display visit" in query:
        return "SELECT * FROM visit;"
    
    # Pattern 11: Show rooms
    if "show room" in query or "display room" in query:
        return "SELECT * FROM room;"
    
    # Pattern 12: Show patients by gender
    if "male patient" in query:
        return "SELECT * FROM patient WHERE Gender = 'M';"
    if "female patient" in query:
        return "SELECT * FROM patient WHERE Gender = 'F';"
    
    # Pattern 13: Show patients by blood group
    if "blood group" in query:
        words = query.split()
        for i, word in enumerate(words):
            if word in ["a+", "b+", "o+", "ab+", "a-", "b-", "o-", "ab-"]:
                blood_group = word.upper()
                return f"SELECT * FROM patient WHERE BloodGroup = '{blood_group}';"
    
    # Pattern 14: Show doctor by specialization
    if "doctor" in query and ("cardiology" in query or "dermatology" in query or 
                               "orthopedics" in query or "pediatrics" in query):
        specializations = ["Cardiology", "Dermatology", "Orthopedics", "Gynecology", 
                          "Pediatrics", "ENT", "Neurology", "Oncology", "Ophthalmology"]
        for spec in specializations:
            if spec.lower() in query:
                return f"SELECT * FROM doctor WHERE Specialization = '{spec}';"
    
    # Pattern 15: Show total billing amount
    if "total bill" in query or "total amount" in query:
        return "SELECT SUM(TotalAmount) as TotalBilling FROM billing;"
    
    # Pattern 16: Show patients from specific city
    if "patient from" in query or "patients in" in query:
        cities = ["pune", "mumbai", "delhi", "bangalore", "kolkata", "chennai", 
                 "hyderabad", "ahmedabad", "jaipur"]
        for city in cities:
            if city in query:
                city_name = city.capitalize()
                return f"SELECT * FROM patient WHERE Address LIKE '%{city_name}%';"
    
    # Pattern 17: Show ICU rooms
    if "icu room" in query:
        return "SELECT * FROM room WHERE RoomType = 'ICU';"
    
    # Pattern 18: Show general rooms
    if "general room" in query:
        return "SELECT * FROM room WHERE RoomType = 'General';"
    
    # Pattern 19: Join query - patient with admission
    if "patient with admission" in query or "admitted patient" in query:
        return """SELECT p.HealthID, p.Name, p.Age, a.AdmitDate, a.DischargeDate 
                  FROM patient p 
                  JOIN admission a ON p.HealthID = a.HealthID;"""
    
    # Pattern 20: Payment by mode
    if "cash payment" in query:
        return "SELECT * FROM billing WHERE PaymentMode = 'Cash';"
    if "card payment" in query:
        return "SELECT * FROM billing WHERE PaymentMode = 'Card';"
    if "upi payment" in query:
        return "SELECT * FROM billing WHERE PaymentMode = 'UPI';"
    if "insurance payment" in query:
        return "SELECT * FROM billing WHERE PaymentMode = 'Insurance';"
    
    return None

def main():
    """Main function to run the NL2SQL system"""
    print("=" * 60)
    print("    MEDILOCKER - NATURAL LANGUAGE TO SQL CONVERTER")
    print("=" * 60)
    print("\nWelcome to MediLocker NL2SQL System!")
    print("This system converts natural language queries to SQL.")
    print("Type 'help' to see example queries.\n")
    
    # Connect to database
    connection = connect_to_database()
    if not connection:
        return
    
    # Main query loop
    while True:
        print("-" * 60)
        natural_query = input("Enter your query(help / Exit): ").strip()
        
        if natural_query.lower() == 'exit':
            print("\nThank you for using MediLocker NL2SQL System!")
            break
        
        if natural_query.lower() == 'help':
            show_help()
            continue
        
        if not natural_query:
            print("Please enter a valid query.\n")
            continue
        
        # Convert natural language to SQL
        sql_query = nl_to_sql(natural_query)
        
        if sql_query:
            print(f"\n📝 Generated SQL Query:")
            print(f"   {sql_query}\n")
            
            # Execute the query
            columns, results = execute_query(connection, sql_query)
            
            if columns and results:
                print(f"📊 Query Results ({len(results)} rows):\n")
                display_results(columns, results)
            elif columns:
                print("Query executed successfully but returned no results.\n")
        else:
            print("❌ Sorry, I couldn't understand your query.")
            print("   Please try rephrasing or use one of the example queries.")
            print("   Type 'help' to see all available queries.\n")
    
    # Close database connection
    if connection.is_connected():
        connection.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()