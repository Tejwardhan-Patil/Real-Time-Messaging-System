import jwt
import datetime
from functools import wraps
from flask import request, jsonify, make_response

# Secret key for JWT encoding and decoding
SECRET_KEY = "SecretKeyForJWT"

# User database simulation
USERS_DB = {
    "person1": {"password": "password123", "role": "user"},
    "person2": {"password": "adminpassword", "role": "admin"}
}

# Function to generate JWT token
def generate_jwt_token(username):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    token = jwt.encode({
        "username": username,
        "exp": expiration_time
    }, SECRET_KEY, algorithm="HS256")
    return token

# Function to verify JWT token
def verify_jwt_token(token):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Function to extract token from request header
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return make_response(jsonify({"message": "Token is missing!"}), 401)

        try:
            data = verify_jwt_token(token)
            if data is None:
                return make_response(jsonify({"message": "Token is invalid!"}), 401)
            request.user = data["username"]
        except:
            return make_response(jsonify({"message": "Token is invalid!"}), 401)

        return f(*args, **kwargs)

    return decorated

# Function to check role-based access control (RBAC)
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            if "Authorization" in request.headers:
                token = request.headers["Authorization"].split(" ")[1]
            if not token:
                return make_response(jsonify({"message": "Token is missing!"}), 401)

            try:
                data = verify_jwt_token(token)
                if data is None:
                    return make_response(jsonify({"message": "Token is invalid!"}), 401)
                username = data["username"]
                user_role = USERS_DB.get(username, {}).get("role")
                if user_role != role:
                    return make_response(jsonify({"message": "Access denied!"}), 403)
            except:
                return make_response(jsonify({"message": "Token is invalid!"}), 401)

            return f(*args, **kwargs)

        return decorated
    return decorator

# Flask application
from flask import Flask

app = Flask(__name__)

@app.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response("Login required", 401)

    user = USERS_DB.get(auth.username)
    if user and user["password"] == auth.password:
        token = generate_jwt_token(auth.username)
        return jsonify({"token": token})

    return make_response("Invalid credentials", 401)

@app.route("/protected", methods=["GET"])
@token_required
def protected_route():
    return jsonify({"message": f"Hello, {request.user}! Welcome to the protected route."})

@app.route("/admin", methods=["GET"])
@token_required
@role_required("admin")
def admin_route():
    return jsonify({"message": f"Hello, {request.user}! You are an admin."})

# Error handler for 404 Not Found
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error": "Resource not found"}), 404)

# Error handler for 405 Method Not Allowed
@app.errorhandler(405)
def method_not_allowed(error):
    return make_response(jsonify({"error": "Method not allowed"}), 405)

# Error handler for 500 Internal Server Error
@app.errorhandler(500)
def internal_server_error(error):
    return make_response(jsonify({"error": "Internal server error"}), 500)

# JWT token blacklist
blacklist = set()

# Function to invalidate a JWT token
@app.route("/logout", methods=["POST"])
@token_required
def logout():
    token = request.headers["Authorization"].split(" ")[1]
    blacklist.add(token)
    return jsonify({"message": "Logged out successfully!"})

# Function to verify if the token is blacklisted
def is_token_blacklisted(token):
    return token in blacklist

@app.route("/blacklisted", methods=["GET"])
@token_required
def blacklisted():
    token = request.headers["Authorization"].split(" ")[1]
    if is_token_blacklisted(token):
        return jsonify({"message": "Token is blacklisted!"})
    return jsonify({"message": "Token is valid."})

# Token refresh function
@app.route("/refresh", methods=["POST"])
@token_required
def refresh_token():
    username = request.user
    token = generate_jwt_token(username)
    return jsonify({"token": token})

# Function to validate roles (for API keys)
def role_based_access(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers["Authorization"].split(" ")[1]
            decoded_token = verify_jwt_token(token)
            if decoded_token and USERS_DB[decoded_token["username"]]["role"] == role:
                return f(*args, **kwargs)
            return make_response("Forbidden", 403)
        return decorated_function
    return wrapper

@app.route("/admin-only", methods=["GET"])
@token_required
@role_based_access("admin")
def admin_only():
    return jsonify({"message": "Welcome Admin!"})

if __name__ == "__main__":
    app.run(debug=True)