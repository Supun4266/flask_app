from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

users = [
    {"username": "user1", "password": "password123"},
    {"username": "user2", "password": "password123"},
    {"username": "user3", "password": "password123"},
]

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def register_user(user):
    driver.get("http://127.0.0.1:5000/register")
    time.sleep(1)
    
    username_field = driver.find_element(By.ID, "username")
    time.sleep(1)
    
    password_field = driver.find_element(By.ID, "password")
    time.sleep(1)
    
    submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    time.sleep(1)
    
    username_field.send_keys(user["username"])
    time.sleep(1)
    
    password_field.send_keys(user["password"])
    time.sleep(1)
    
    submit_button.click()
    time.sleep(2)

for user in users:
    register_user(user)

driver.quit()
