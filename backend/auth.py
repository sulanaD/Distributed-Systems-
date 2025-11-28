import bcrypt
from database import execute_query

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_user(email: str, password: str, first_name: str, last_name: str) -> dict:
    """Create a new user in the database"""
    password_hash = hash_password(password)
    
    query = """
        INSERT INTO users (email, password_hash, first_name, last_name)
        VALUES (%s, %s, %s, %s)
        RETURNING id, email, first_name, last_name, created_at
    """
    
    user = execute_query(query, (email, password_hash, first_name, last_name), fetch_one=True)
    return dict(user) if user else None

def get_user_by_email(email: str) -> dict:
    """Get a user by email"""
    query = "SELECT * FROM users WHERE email = %s"
    user = execute_query(query, (email,), fetch_one=True)
    return dict(user) if user else None

def get_user_by_id(user_id: int) -> dict:
    """Get a user by ID"""
    query = "SELECT id, email, first_name, last_name, created_at FROM users WHERE id = %s"
    user = execute_query(query, (user_id,), fetch_one=True)
    return dict(user) if user else None

def authenticate_user(email: str, password: str) -> dict:
    """Authenticate a user by email and password"""
    user = get_user_by_email(email)
    
    if user and verify_password(password, user['password_hash']):
        # Remove password hash from returned user
        del user['password_hash']
        return user
    
    return None

def save_tax_calculation(user_id: int, calculation: dict) -> dict:
    """Save a tax calculation to the database"""
    query = """
        INSERT INTO tax_calculations 
        (user_id, financial_year, gross_income, taxable_income, tax_payable, medicare_levy, total_tax, net_income)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, calculated_at
    """
    
    result = execute_query(query, (
        user_id,
        calculation['financial_year'],
        calculation['gross_income'],
        calculation['taxable_income'],
        calculation['income_tax'],
        calculation['medicare_levy'],
        calculation['total_tax'],
        calculation['net_income']
    ), fetch_one=True)
    
    return dict(result) if result else None

def get_user_calculations(user_id: int, limit: int = 10) -> list:
    """Get tax calculation history for a user"""
    query = """
        SELECT * FROM tax_calculations 
        WHERE user_id = %s 
        ORDER BY calculated_at DESC 
        LIMIT %s
    """
    
    results = execute_query(query, (user_id, limit), fetch_all=True)
    return [dict(r) for r in results] if results else []
