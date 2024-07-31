import pytest
from app import app, mongo
from flask import session
import bcrypt

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

@pytest.fixture
def setup_test_users():
    users = mongo.db.users
    users.delete_one({'username': 'testuser1'})
    users.delete_one({'username': 'admin'})
    hashpass_user = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())
    hashpass_admin = bcrypt.hashpw('1212'.encode('utf-8'), bcrypt.gensalt())
    users.insert_one({'username': 'testuser1', 'password': hashpass_user, 'isadmin': False})
    users.insert_one({'username': 'admin', 'password': hashpass_admin, 'isadmin': True})

    yield

    users.delete_one({'username': 'testuser1'})
    users.delete_one({'username': 'admin'})

def test_login_valid_user(client, setup_test_users):
    response = client.post('/login', data={
        'username': 'testuser1',
        'password': 'password123'
    })
    assert response.status_code == 302

    with client.session_transaction() as sess:
        assert 'username' in sess
        assert sess['username'] == 'testuser1'

def test_login_invalid_user(client, setup_test_users):
    response = client.post('/login', data={
        'username': 'testuser1',
        'password': 'wrongpassword'
    })
    assert response.status_code == 200

    with client.session_transaction() as sess:
        assert 'username' not in sess

def test_login_valid_admin(client, setup_test_users):
    response = client.post('/login', data={
        'username': 'admin',
        'password': '1212'
    })
    assert response.status_code == 302

    with client.session_transaction() as sess:
        assert 'username' in sess
        assert sess['username'] == 'admin'

def test_login_invalid_admin(client, setup_test_users):
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'wrongpassword'
    })
    assert response.status_code == 200

    with client.session_transaction() as sess:
        assert 'username' not in sess
