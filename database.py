import os,dotenv
import mysql.connector
from mysql.connector import Error,pooling


# This function should be called from app.py AFTER load_dotenv()
def create_db_pool():
    """Creates a connection pool for the database."""
    try:
        pool = pooling.MySQLConnectionPool(
            pool_name="intellidocs_pool",
            pool_size=5,
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'notes_db') # Connect directly to the DB
        )
        print("Database connection pool created successfully.")
        return pool
    except Error as e:
        print(f"Error creating connection pool: {e}")
        return None
    
cnx_pool = create_db_pool()

def get_db_connection():
    """Gets a connection from the pool."""
    if cnx_pool is None:
        print("Connection pool is not available.")
        return None
    try:
        # Get a connection from the pool
        conn = cnx_pool.get_connection()
        return conn
    except Error as e:
        print(f"Error getting connection from pool: {e}")
        return None

def init_db():
    conn = None
    cursor = None
    try:
        # Step 1: Connect to the server WITHOUT a specific database to create it
        print("Connecting to MySQL server to ensure database exists...")
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD')
        )
        cursor = conn.cursor()
        db_name = os.getenv('DB_NAME', 'notes_db')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARACTER SET 'utf8mb4'")
        print(f"Database '{db_name}' is ready.")

    except Error as e:
        print(f"Error during initial database creation: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    # Step 2: Use a connection from the pool to create the tables
    conn = get_db_connection()
    if conn is None:
        print("Could not get DB connection from pool to create tables.")
        return
    
    try:
        cursor=conn.cursor()
        print("Ensuring tables are created...")
        users_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """
        cursor.execute(users_table_sql)
        print("'users' table is ready.")

        documents_table_sql=""" 
        CREATE TABLE IF NOT EXISTS documents (
          id INT AUTO_INCREMENT PRIMARY KEY,
          user_id INT NOT NULL,
          filename VARCHAR(255) NOT NULL,
          url VARCHAR(512) NOT NULL,
          public_id VARCHAR(255) NOT NULL,
          processing_status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') NOT NULL DEFAULT 'PENDING',
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )ENGINE=InnoDB;
        """
    
        cursor.execute(documents_table_sql)
        print("'documents' table is ready.")

    except Error as e:
        print(f"Error during table creation: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close() # This returns the connection to the pool
            print("Connection returned to pool.")




# -------To add a user ---------
def add_user(email, password_hash):
    """Adds a new user to the users table. Returns True on success, False on failure."""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        # IMPORTANT: Use parameterized queries to prevent SQL injection
        sql = "INSERT INTO users (email, password_hash) VALUES (%s, %s)"
        cursor.execute(sql, (email, password_hash))
        conn.commit()
        
        # Get the ID of the row that was just inserted
        new_user_id = cursor.lastrowid 
        return new_user_id
    
    except Error as e:
        print(f"Error adding user: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# --- To retrieve a user by their email ---
def get_user_by_email(email):

    """Fetches a single user by email. Returns user data as a dict, or None if not found."""
    conn = get_db_connection()
    if conn is None: return None
    try:
        # Use a dictionary cursor to get results as dicts instead of tuples
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT * FROM users WHERE email = %s"
        cursor.execute(sql, (email,))
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ---To add a document's metadata ---
def add_document(user_id, filename, url, public_id,tags_string,summary):
    """Adds a new document record to the database. Returns True on success."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO documents (user_id, filename, url, public_id,tags,summary)
            VALUES (%s, %s, %s, %s,%s,%s)
        """
        cursor.execute(sql, (user_id, filename, url, public_id,tags_string,summary))
        conn.commit()
        new_doc_id = cursor.lastrowid 
        return new_doc_id
    except Error as e:
        print(f"Error adding document: {e}")
        conn.rollback()
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_documents_by_user(user_id):
    """Fetches all documents for a specific user, ordered by most recent."""
    conn = get_db_connection()
    if conn is None: return []
    try:
        # Using dictionary=True makes the cursor return rows as dictionaries
        cursor = conn.cursor(dictionary=True)
        
        # The SQL query to select documents for a specific user
        # 'WHERE user_id = %s' is the crucial part for security and correctness
        # 'ORDER BY created_at DESC' shows the newest documents first
        sql = "SELECT id, filename, url, created_at, tags FROM documents WHERE user_id = %s ORDER BY created_at DESC"
        
        cursor.execute(sql, (user_id,))
        
        # fetchall() gets all the rows that match the query
        documents = cursor.fetchall()
        return documents
    except Error as e:
        print(f"Error fetching documents: {e}")
        return [] # Return an empty list if an error occurs
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_document_by_id(doc_id):
    """Fetches a single document by its primary key ID."""
    conn = get_db_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT * FROM documents WHERE id = %s"
        cursor.execute(sql, (doc_id,))
        document = cursor.fetchone()
        return document
    except Error as e:
        print(f"Error fetching document by id: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def delete_document_record(doc_id):

    """Deletes a document record from the database by its ID."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        sql = "DELETE FROM documents WHERE id = %s"
        cursor.execute(sql, (doc_id,))
        conn.commit()
        return True
    except Error as e:
        print(f"Error deleting document record: {e}")
        conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def update_document_status(doc_id: int, status: str):
    """Updates the processing_status for a specific document."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        # A list of valid statuses to prevent incorrect values
        valid_statuses = ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']
        if status not in valid_statuses:
            print(f"Invalid status provided: {status}")
            return False

        cursor = conn.cursor()
        sql = "UPDATE documents SET processing_status = %s WHERE id = %s"
        cursor.execute(sql, (status, doc_id))
        conn.commit()
        return True
    except Error as e:
        print(f"Error updating document status: {e}")
        conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

