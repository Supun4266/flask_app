import pytest
from app import app, mongo
from flask import session
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from werkzeug.datastructures import FileStorage
from io import BytesIO
import tempfile

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    temp_upload_dir = tempfile.TemporaryDirectory()
    app.config['UPLOAD_FOLDER'] = temp_upload_dir.name

    with app.test_client() as client:
        yield client

    temp_upload_dir.cleanup()

@pytest.fixture
def setup_test_admin():
    users = mongo.db.users
    users.delete_one({'username': 'admin'})
    hashpass_admin = bcrypt.hashpw('1212'.encode('utf-8'), bcrypt.gensalt())
    users.insert_one({'username': 'admin', 'password': hashpass_admin, 'isadmin': True})

    yield

    users.delete_one({'username': 'admin'})

def login_as_admin(client):
    response = client.post('/login', data={
        'username': 'admin',
        'password': '1212'
    })
    return response

def get_jwt_token():
    payload = {'user': 'admin', 'exp': datetime.utcnow() + timedelta(hours=1)}
    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm="HS256")
    return token

def test_add_post(client, setup_test_admin):
    login_as_admin(client)
    token = get_jwt_token()

    data = {
        'title': 'Test Post',
        'image': (BytesIO(b'my file contents'), 'test_image.jpg')
    }
    response = client.post('/add_post', data=data, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'}, follow_redirects=True)
    
    print(response.data)

    assert response.status_code == 200
    post = mongo.db.posts.find_one({'title': 'Test Post'})
    assert post is not None
    assert post['title'] == 'Test Post'

def test_update_post(client, setup_test_admin):
    login_as_admin(client)
    token = get_jwt_token()

    post_id = mongo.db.posts.insert_one({'title': 'Test Post', 'content': 'This is a test post.', 'image': 'test_image.jpg'}).inserted_id
    data = {
        'title': 'Updated Test Post',
        'image': (BytesIO(b'updated file contents'), 'updated_test_image.jpg')
    }
    response = client.post(f'/edit_post/{post_id}', data=data, content_type='multipart/form-data', headers={'Authorization': f'Bearer {token}'}, follow_redirects=True)
    
    print(response.data)

    assert response.status_code == 200
    post = mongo.db.posts.find_one({'_id': post_id})
    assert post['title'] == 'Updated Test Post'
    assert post['image'] == 'updated_test_image.jpg'

def test_delete_post(client, setup_test_admin):
    login_as_admin(client)
    token = get_jwt_token()

    post_id = mongo.db.posts.insert_one({'title': 'Test Post', 'content': 'This is a test post.', 'image': 'test_image.jpg'}).inserted_id
    response = client.post(f'/delete_post/{post_id}', headers={'Authorization': f'Bearer {token}'}, follow_redirects=True)
    
    print(response.data)

    assert response.status_code == 200
    post = mongo.db.posts.find_one({'_id': post_id})
    assert post is None
