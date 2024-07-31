import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from flask_pymongo import PyMongo
import bcrypt
import jwt
import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
mongo = PyMongo(app)

# Ensure uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            return redirect(url_for('login'))
        try:
            jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        except:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        username = request.form['username']
        password = request.form['password']
        
        print(f"Received registration request for username: {username}")
        
        existing_user = users.find_one({'username': username})
        
        if existing_user is None:
            hashpass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'username': username, 'password': hashpass, 'isadmin': False})
            print(f"User {username} registered successfully.")
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        
        print("Username already exists!")
        flash('That username already exists!', 'danger')
        return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = mongo.db.users
        user = users.find_one({'username': username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            token = jwt.encode({'user': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['JWT_SECRET_KEY'], algorithm="HS256")
            session['token'] = token
            session['username'] = username  # Store the username in the session
            if user.get('isadmin', False):
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        return 'Invalid credentials!'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('token', None)
    session.pop('username', None)  # Remove the username from the session
    return redirect(url_for('home'))

@app.route('/admin')
@token_required
def admin_dashboard():
    token = session.get('token')
    decoded_token = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
    users = mongo.db.users
    user = users.find_one({'username': decoded_token['user']})
    if not user['isadmin']:
        return redirect(url_for('home'))
    posts = mongo.db.posts.find()
    return render_template('admin.html', posts=posts)

@app.route('/user_dashboard')
@token_required
def user_dashboard():
    token = session.get('token')
    decoded_token = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
    users = mongo.db.users
    user = users.find_one({'username': decoded_token['user']})
    if user.get('isadmin', False):
        return redirect(url_for('admin_dashboard'))
    posts = mongo.db.posts.find()
    return render_template('user_dashboard.html', posts=posts)

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        username = session['username']
        posts = mongo.db.posts.find()
        return render_template('user_dashboard.html', posts=posts, username=username)
    else:
        return redirect(url_for('login'))

@app.route('/add_post', methods=['GET', 'POST'])
@token_required
def add_post():
    token = session.get('token')
    decoded_token = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
    users = mongo.db.users
    user = users.find_one({'username': decoded_token['user']})
    
    if not user['isadmin']:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        title = request.form['title']
        if 'image' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['image']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            posts = mongo.db.posts
            posts.insert_one({'title': title, 'image': filename, 'likes': 0, 'liked_by': [], 'comments': []})
            return redirect(url_for('admin_dashboard'))
    
    return render_template('add_post.html')

@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
@token_required
def edit_post(post_id):
    token = session.get('token')
    decoded_token = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
    users = mongo.db.users
    user = users.find_one({'username': decoded_token['user']})
    
    if not user['isadmin']:
        return redirect(url_for('home'))
    
    posts = mongo.db.posts
    post = posts.find_one({'_id': ObjectId(post_id)})
    
    if request.method == 'POST':
        title = request.form['title']
        update_data = {'title': title}
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                update_data['image'] = filename
        posts.update_one({'_id': ObjectId(post_id)}, {'$set': update_data})
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_post.html', post=post)

@app.route('/delete_post/<post_id>', methods=['POST'])
@token_required
def delete_post(post_id):
    token = session.get('token')
    decoded_token = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
    users = mongo.db.users
    user = users.find_one({'username': decoded_token['user']})
    
    if not user['isadmin']:
        return redirect(url_for('home'))
    
    posts = mongo.db.posts
    posts.delete_one({'_id': ObjectId(post_id)})
    return redirect(url_for('admin_dashboard'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/posts')
@token_required
def posts():
    posts = mongo.db.posts.find()
    return render_template('posts.html', posts=posts)

@app.route('/like_post/<post_id>', methods=['POST'])
def like_post(post_id):
    username = session.get('username')
    if not username:
        return jsonify({'status': 'not_authenticated'}), 401
    
    posts = mongo.db.posts
    post = posts.find_one({'_id': ObjectId(post_id)})
    if username in post['liked_by']:
        posts.update_one({'_id': ObjectId(post_id)}, {'$inc': {'likes': -1}, '$pull': {'liked_by': username}})
    else:
        posts.update_one({'_id': ObjectId(post_id)}, {'$inc': {'likes': 1}, '$push': {'liked_by': username}})
    post = posts.find_one({'_id': ObjectId(post_id)})  # Re-fetch post to get updated data
    return jsonify({'status': 'success', 'likes': post['likes']})

@app.route('/comment_post/<post_id>', methods=['POST'])
def comment_post(post_id):
    username = session.get('username')
    if not username:
        return jsonify({'status': 'not_authenticated'}), 401
    
    comment_text = request.form['comment']
    posts = mongo.db.posts
    comment_data = {'author': username, 'text': comment_text, 'id': str(ObjectId())}
    posts.update_one({'_id': ObjectId(post_id)}, {'$push': {'comments': comment_data}})
    post = posts.find_one({'_id': ObjectId(post_id)})  # Re-fetch post to get updated data
    return jsonify({'status': 'success', 'comment': comment_data})

@app.route('/delete_comment/<post_id>/<comment_id>', methods=['POST'])
def delete_comment(post_id, comment_id):
    if 'username' not in session:
        return jsonify({'status': 'not_authenticated'})

    post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
    if post:
        comments = post.get('comments', [])
        comment_to_remove = next((comment for comment in comments if comment['id'] == comment_id), None)
        if comment_to_remove and comment_to_remove['author'] == session['username']:
            new_comments = [comment for comment in comments if comment['id'] != comment_id]
            mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {'$set': {'comments': new_comments}})
            return jsonify({'status': 'success'})
        return jsonify({'status': 'not_authorized'})
    
    return jsonify({'status': 'error'})

@app.route('/most_liked')
def most_liked():
    posts = mongo.db.posts.find().sort('likes', -1)
    return render_template('most_liked.html', posts=posts)

@app.route('/admin/interactions')
@token_required
def admin_interactions():
    token = session.get('token')
    decoded_token = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
    users = mongo.db.users
    user = users.find_one({'username': decoded_token['user']})
    if not user['isadmin']:
        return redirect(url_for('home'))
    posts = mongo.db.posts.find()
    return render_template('admin_interactions.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True)
