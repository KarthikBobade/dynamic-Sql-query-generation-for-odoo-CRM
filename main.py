import psycopg2
import google.generativeai as genai  # Using Gemini API
import re
import os  # For loading environment variables

# Load sensitive information from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "your_database")  # Replace with your actual DB name
DB_USER = os.getenv("DB_USER", "your_db_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_db_password")

# Gemini API Key (load from environment variable)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_api_key")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

def connect_db():
    """ Connects to the Odoo PostgreSQL database. """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD    
        )
        print("✅ Connected to Odoo Database Successfully!")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Database Connection Error: {e}")
        return None

def generate_sql_query(user_request):
    """ Uses Gemini API to generate SQL queries for Odoo's database. """
    prompt = f"""
    Convert the following natural language request into a valid SQL query for an Odoo 18 PostgreSQL database:

    Request: "{user_request}"

    - Ensure correct table names and column names as per Odoo's schema.
    - Use SQL standards with double quotes for table and column names.
    - Use WHERE conditions properly and avoid non-existent columns.
    - Example tables: "sale_order", "res_partner", "account_move", "account_move_line"
    - Example fields: "amount_total", "date_order", "state", "partner_id"

    Output only the SQL query, without any additional formatting like markdown.
    """
    
    response = model.generate_content(prompt)

    if not response.text.strip():
        print("❌ No query was generated. Please try again.")
        return None

    sql_query = response.text.strip()

    # Ensure markdown syntax (```sql ... ```) is removed properly
    sql_query = re.sub(r"```(sql)?", "", sql_query).strip()

    return sql_query

def execute_query(sql_query):
    """ Executes the generated SQL query and fetches results. """
    if not sql_query:
        print("❌ No valid SQL query was generated.")
        return
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()
            print("\n✅ Query Results:")
            for row in results:
                print(row)
    except psycopg2.Error as e:
        print(f"❌ SQL Execution Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    while True:
        user_request = input("\n📝 Enter your request (or type 'exit' to quit): ")
        if user_request.lower() == "exit":
            print("👋 Exiting... Goodbye!")
            break
        
        sql_query = generate_sql_query(user_request)
        
        if sql_query:
            print("\n🔹 Generated SQL Query:\n", sql_query)
            execute_query(sql_query)
        else:
            print("❌ No query was generated. Please try again.")
