import os

class Config:
    SECRET_KEY = 'your_secret_key'
    MONGO_URI = 'mongodb://127.0.0.1:27017/test'
    JWT_SECRET_KEY = 'your_jwt_secret_key'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
