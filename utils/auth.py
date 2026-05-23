import os
import jwt
import bcrypt
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_URI  = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
JWT_SECRET = os.getenv("JWT_SECRET", "secondbrain_secret_2024")

client = MongoClient(MONGO_URI)
db     = client["secondbrain"]
users  = db["users"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_user(username: str, email: str, password: str) -> dict:
    # Check if email already exists
    if users.find_one({"email": email}):
        return {"success": False, "error": "Email already registered"}

    # Check if username already exists
    if users.find_one({"username": username}):
        return {"success": False, "error": "Username already taken"}

    user = {
        "username":   username,
        "email":      email,
        "password":   hash_password(password),
        "created_at": datetime.datetime.now().isoformat()
    }
    users.insert_one(user)
    return {"success": True}


def login_user(email: str, password: str) -> dict:
    user = users.find_one({"email": email})

    if not user:
        return {"success": False, "error": "No account found with this email"}

    if not verify_password(password, user["password"]):
        return {"success": False, "error": "Incorrect password"}

    # Generate JWT token
    token = jwt.encode({
        "user_id":  str(user["_id"]),
        "username": user["username"],
        "email":    user["email"],
        "exp":      datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, JWT_SECRET, algorithm="HS256")

    return {
        "success":  True,
        "token":    token,
        "username": user["username"],
        "email":    user["email"]
    }


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"success": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"success": False, "error": "Session expired. Please login again."}
    except jwt.InvalidTokenError:
        return {"success": False, "error": "Invalid session. Please login again."}