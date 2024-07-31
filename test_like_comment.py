import pytest
from app import app, mongo
from flask import session
import bcrypt
import jwt
import os
from datetime import datetime, timedelta

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    with app.test_client() as client:
        yield client

@pytest.fixture
def setup_test_user():
    # Set up a test user in the database
    users = mongo.db.users
    users.delete_one({'username': 'testuser'})
    hashpass_user = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())
    users.insert_one({'username': 'testuser', 'password': hashpass_user, 'isadmin': False})

    yield

    # Clean up the test user after the test
    users.delete_one({'username': 'testuser'})

def login_as_user(client):
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    return response

def get_jwt_token(username='testuser'):
    payload = {'user': username, 'exp': datetime.utcnow() + timedelta(hours=1)}
    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm="HS256")
    return token

def test_like_post(client, setup_test_user):
    login_as_user(client)
    token = get_jwt_token('testuser')

    post_id = mongo.db.posts.insert_one({'title': 'Test Post', 'content': 'This is a test post.', 'image': 'test_image.jpg', 'likes': 0, 'liked_by': []}).inserted_id
    response = client.post(f'/like_post/{post_id}', headers={'Authorization': f'Bearer {token}'}, follow_redirects=True)
    
    print(response.data)  # Debugging: Print response data

    assert response.status_code == 200  # Expecting success after redirection
    post = mongo.db.posts.find_one({'_id': post_id})
    assert 'testuser' in post['liked_by']
    assert post['likes'] == 1

def test_comment_post(client, setup_test_user):
    login_as_user(client)
    token = get_jwt_token('testuser')

    post_id = mongo.db.posts.insert_one({'title': 'Test Post', 'content': 'This is a test post.', 'image': 'test_image.jpg', 'likes': 0, 'liked_by': [], 'comments': []}).inserted_id
    response = client.post(f'/comment_post/{post_id}', data={'comment': 'This is a test comment.'}, headers={'Authorization': f'Bearer {token}'}, follow_redirects=True)
    
    print(response.data)  # Debugging: Print response data

    assert response.status_code == 200  # Expecting success after redirection
    post = mongo.db.posts.find_one({'_id': post_id})
    assert any(comment['text'] == 'This is a test comment.' for comment in post['comments'])
