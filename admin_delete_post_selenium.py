from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

admin_credentials = {
    "username": "Admin",
    "password": "1212"
}

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

def login_as_admin():
    driver.get("http://127.0.0.1:5000/login")
    time.sleep(1)
    
    username_field = driver.find_element(By.ID, "username")
    time.sleep(1)
    
    password_field = driver.find_element(By.ID, "password")
    time.sleep(1)
    
    submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    time.sleep(1)
    
    username_field.send_keys(admin_credentials["username"])
    time.sleep(1)
    
    password_field.send_keys(admin_credentials["password"])
    time.sleep(1)
    
    submit_button.click()
    time.sleep(2)

def delete_first_post():
    driver.get("http://127.0.0.1:5000/admin")
    time.sleep(1)
    
    delete_buttons = driver.find_elements(By.XPATH, "//form[contains(@action, '/delete_post/')]/button[@type='submit']")
    time.sleep(1)
    
    if delete_buttons:
        delete_buttons[0].click()
        time.sleep(1)
        print("First post deleted.")
    else:
        print("No posts found to delete.")
    
    time.sleep(2)

login_as_admin()
delete_first_post()

driver.quit()
