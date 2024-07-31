import pytest
from app import app, mongo
from flask import session

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_register_user(client):
    mongo.db.users.delete_one({'username': 'testuser1'})
    
    response = client.post('/register', data={
        'username': 'testuser1',
        'password': 'password123'
    })
    
    assert response.status_code == 302
    
    with client.session_transaction() as sess:
        assert 'username' in sess
        assert sess['username'] == 'testuser1'
