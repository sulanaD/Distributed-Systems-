from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
import psycopg2

from config import Config
from auth import create_user, authenticate_user, get_user_by_id, save_tax_calculation, get_user_calculations
from tax_calculator import calculate_tax, get_tax_brackets_info

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)

CORS(app, supports_credentials=True)
jwt = JWTManager(app)

# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate email format (basic)
    if '@' not in data['email']:
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password length
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    try:
        user = create_user(
            email=data['email'].lower().strip(),
            password=data['password'],
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip()
        )
        
        if user:
            # Create access token (identity must be a string)
            access_token = create_access_token(identity=str(user['id']))
            return jsonify({
                'message': 'Registration successful',
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name']
                },
                'access_token': access_token
            }), 201
        else:
            return jsonify({'error': 'Registration failed'}), 500
            
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error': 'Email already registered'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = authenticate_user(data['email'].lower().strip(), data['password'])
    
    if user:
        access_token = create_access_token(identity=str(user['id']))
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name']
            },
            'access_token': access_token
        }), 200
    else:
        return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    user_id = int(get_jwt_identity())
    user = get_user_by_id(user_id)
    
    if user:
        return jsonify({'user': user}), 200
    else:
        return jsonify({'error': 'User not found'}), 404

# ==================== TAX CALCULATION ROUTES ====================

@app.route('/api/tax/calculate', methods=['POST'])
@jwt_required()
def calculate_tax_route():
    """Calculate tax for authenticated user"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data.get('gross_income'):
        return jsonify({'error': 'gross_income is required'}), 400
    
    try:
        gross_income = float(data['gross_income'])
        deductions = float(data.get('deductions', 0))
        
        if gross_income < 0:
            return jsonify({'error': 'gross_income must be positive'}), 400
        
        if deductions < 0:
            return jsonify({'error': 'deductions must be positive'}), 400
            
    except ValueError:
        return jsonify({'error': 'Invalid number format'}), 400
    
    # Calculate tax
    result = calculate_tax(gross_income, deductions)
    
    # Save calculation to database
    save_result = data.get('save', True)
    if save_result:
        saved = save_tax_calculation(user_id, result)
        if saved:
            result['calculation_id'] = saved['id']
            result['calculated_at'] = saved['calculated_at'].isoformat()
    
    return jsonify(result), 200

@app.route('/api/tax/history', methods=['GET'])
@jwt_required()
def get_tax_history():
    """Get tax calculation history for authenticated user"""
    user_id = int(get_jwt_identity())
    limit = request.args.get('limit', 10, type=int)
    
    calculations = get_user_calculations(user_id, limit)
    
    # Convert datetime objects to strings
    for calc in calculations:
        if calc.get('calculated_at'):
            calc['calculated_at'] = calc['calculated_at'].isoformat()
    
    return jsonify({'calculations': calculations}), 200

@app.route('/api/tax/brackets', methods=['GET'])
def get_tax_brackets():
    """Get current tax bracket information (public endpoint)"""
    brackets = get_tax_brackets_info()
    return jsonify({
        'financial_year': '2024-2025',
        'brackets': brackets,
        'medicare_levy_rate': '2%'
    }), 200

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Australian Tax Calculator API'}), 200

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)
