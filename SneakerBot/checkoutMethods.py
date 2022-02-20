import os
import sys
import six
import pause
import argparse
import logging.config
import re
import time
import random
import json
from selenium import webdriver
from dateutil import parser as date_parser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC

from main import LOGGER, NIKE_HOME_URL, SUBMIT_BUTTON_XPATH



def login(driver, username, password):
    try:
        LOGGER.info("Requesting page: " + NIKE_HOME_URL)
        driver.get(NIKE_HOME_URL)
    except TimeoutException:
        LOGGER.info("Page load timed out but continuing anyway")

    LOGGER.info("Waiting for login fields to become visible")
    wait_until_visible(driver=driver, xpath="//input[@name='emailAddress']")

    LOGGER.info("Entering username and password")
    email_input = driver.find_element_by_xpath("//input[@name='emailAddress']")
    email_input.clear()
    email_input.send_keys(username)
    
    password_input = driver.find_element_by_xpath("//input[@name='password']")
    password_input.clear()
    password_input.send_keys(password)

    LOGGER.info("Logging in")
    driver.find_element_by_xpath("//input[@value='SIGN IN']").click()
    
    wait_until_visible(driver=driver, xpath="//a[@data-path='myAccount:greeting']", duration=5)
    
    LOGGER.info("Successfully logged in")

def retry_login(driver, username, password):
    num_retries_attempted = 0
    num_retries = 5
    while True:
        try:            
            # Xpath to error dialog button
            xpath = "/html/body/div[2]/div[3]/div[3]/div/div[2]/input"
            wait_until_visible(driver=driver, xpath=xpath, duration=5)
            driver.find_element_by_xpath(xpath).click()
        
            password_input = driver.find_element_by_xpath("//input[@name='password']")
            password_input.clear()
            password_input.send_keys(password)

            LOGGER.info("Logging in")
            
            try:
                driver.find_element_by_xpath("//input[@value='SIGN IN']").click()
            except Exception as e:
                if num_retries_attempted < num_retries:
                    num_retries_attempted += 1
                    continue
                else:
                    LOGGER.info("Too many login attempts. Please restart app.")
                    break
                	            
            if num_retries_attempted < num_retries:
                num_retries_attempted += 1
                continue
            else:
                LOGGER.info("Too many login attempts. Please restart app.")
                break
        except Exception as e:
            LOGGER.exception("Error dialog did not load, proceed. Error: " + str(e))
            break

    wait_until_visible(driver=driver, xpath="//a[@data-path='myAccount:greeting']")
    
    LOGGER.info("Successfully logged in")
    
def select_shoe_size(driver, shoe_size, shoe_type, skip_size_selection):
    LOGGER.info("Waiting for size dropdown to appear")

    wait_until_visible(driver, class_name="size-grid-button", duration=10)

    if skip_size_selection:
        LOGGER.info("Skipping size selection...")
    else:
        LOGGER.info("Selecting size from dropdown")
    
        # Get first element found text
        size_text = driver.find_element_by_xpath("//li[@data-qa='size-available']/button").text
        
    
        special_shoe_type = False
        # Determine if size only displaying or size type + size
        if re.search("[a-zA-Z]", size_text):
    
            if shoe_type in ("Y", "C"):
                shoe_size_type = shoe_size + shoe_type
            elif shoe_size is None and shoe_type in ("XXS", "XS", "S", "M", "L", "XL"):
                shoe_size_type = shoe_type
                special_shoe_type = True  
            else:
                shoe_size_type = shoe_type + " " + shoe_size
     
            LOGGER.info("Shoe size/type=" + shoe_size_type)
            
            if special_shoe_type:
                driver.find_element_by_xpath("//li[@data-qa='size-available']").find_element_by_xpath(
                    "//button[text()='{}']".format(shoe_size_type)).click()
            else:
                driver.find_element_by_xpath("//li[@data-qa='size-available']").find_element_by_xpath(
                    "//button[text()[contains(.,'"+shoe_size_type+"')]]").click()
                
        else:
        
            driver.find_element_by_xpath("//li[@data-qa='size-available']").find_element_by_xpath(
                "//button[text()='{}']".format(shoe_size)).click()


def click_buy_button(driver):
    xpath = "//button[@data-qa='feed-buy-cta']"
    
    LOGGER.info("Waiting for buy button to become present")
    element = wait_until_present(driver, xpath=xpath, duration=10) 
    
    LOGGER.info("Clicking buy button")
    driver.execute_script("arguments[0].click();", element)


def select_payment_option(driver):
    xpath = "//input[@data-qa='payment-radio']"

    LOGGER.info("Waiting for payment checkbox to become clickable")
    wait_until_clickable(driver, xpath=xpath, duration=10)

    LOGGER.info("Checking payment checkbox")
    driver.find_element_by_xpath(xpath).click()
    
def input_address(driver, shipping_address):
    LOGGER.info("Inputting address")
    LOGGER.info("First Name=" + shipping_address["first_name"])
    LOGGER.info("Last Name=" + shipping_address["last_name"])
    LOGGER.info("Address=" + shipping_address["address"])
    LOGGER.info("Apt=" + shipping_address["apt"])
    LOGGER.info("City=" + shipping_address["city"])
    LOGGER.info("State=" + shipping_address["state"])
    LOGGER.info("Zip Code=" + shipping_address["zip_code"])
    LOGGER.info("Phone Number=" + shipping_address["phone_number"])
    
    first_name = shipping_address["first_name"]
    last_name = shipping_address["last_name"]
    address = shipping_address["address"]
    apt = shipping_address["apt"]
    city = shipping_address["city"]
    st = shipping_address["state"]
    zip_code = shipping_address["zip_code"]
    phone_number = shipping_address["phone_number"]
        
    xpath = "//input[@data-qa='first-name-shipping']"

    LOGGER.info("Waiting for shipping options become visible")
    wait_until_visible(driver, xpath=xpath, duration=10)
    
    sa_input = driver.find_element_by_id("first-name-shipping")
    sa_input.clear()
    sa_input.send_keys(first_name)
    
    sa_input = driver.find_element_by_id("last-name-shipping")
    sa_input.clear()
    sa_input.send_keys(last_name)
    
    sa_input = driver.find_element_by_id("shipping-address-1")
    sa_input.clear()
    sa_input.send_keys(address)
    
    sa_input = driver.find_element_by_id("shipping-address-2")
    sa_input.clear()
    sa_input.send_keys(apt)
    
    sa_input = driver.find_element_by_id("city")
    sa_input.clear()
    sa_input.send_keys(city)
    
    sa_input = driver.find_element_by_id("state")
    sa_input.clear()
    sa_input.send_keys(st)
    
    sa_input = driver.find_element_by_id("zipcode")
    sa_input.clear()
    sa_input.send_keys(zip_code)
    
    sa_input = driver.find_element_by_id("phone-number")
    sa_input.clear()
    sa_input.send_keys(phone_number)
       
def select_shipping_option(driver, shipping_option):
    LOGGER.info("Selecting shipping")
    if shipping_option!="STANDARD":
        element = wait_until_present(driver, el_id=shipping_option, duration=10) 
        driver.execute_script("arguments[0].click();", element)
           
def input_cvv(driver, cvv):    
    xpath = "//div[@data-qa='payment-section']"

    LOGGER.info("Waiting for payment section to become visible")
    wait_until_visible(driver, xpath=xpath, duration=10)
    
    LOGGER.info("Waiting for cvv to become visible")
    
    WebDriverWait(driver, 10, 0.01).until(EC.frame_to_be_available_and_switch_to_it(driver.find_element_by_css_selector("iframe[title='creditCardIframeForm']")))
    
    idName = "cvNumber"
    wait_until_visible(driver, el_id=idName)
    cvv_input = driver.find_element_by_id("cvNumber")
    cvv_input.clear()
    cvv_input.send_keys(cvv)

    driver.switch_to.parent_frame()
       
def click_save_button(driver, xpath_o=None, check_disabled=True):
    if xpath_o:
        xpath = xpath_o
    else:
        xpath = "//button[text()='Save & Continue']"

    LOGGER.info("Waiting for save button class to become visible")
    
    element = wait_until_present(driver, xpath=xpath, duration=10)
    
    if check_disabled:
        wait = WebDriverWait(driver, 10, 0.01)
        wait.until(lambda d: 'disabled' not in element.get_attribute('class'))

    wait_until_clickable(driver, xpath=xpath, duration=10)

    LOGGER.info("Clicking save button")
    driver.find_element_by_xpath(xpath).click()
        
def click_add_new_address_button(driver):
    xpath = "//button[text()='Add New Address']"

    LOGGER.info("Waiting for Add New Address button to become clickable")
    wait_until_clickable(driver, xpath=xpath, duration=10)

    LOGGER.info("Clicking Add New Address button")
    driver.find_element_by_xpath(xpath).click()
    
def check_add_new_address_button(driver):
    xpath = "//button[text()='Add New Address']"

    LOGGER.info("Waiting for Add New Address button to become clickable")
    wait_until_clickable(driver, xpath=xpath, duration=.2)
    
def check_shipping(driver):
    xpath = "//span[@data-qa='shipping-method-date']"

    LOGGER.info("Waiting for shipping options become visible")
    wait_until_visible(driver, xpath=xpath, duration=.2)
    
def check_payment(driver):
    xpath = "//div[@data-qa='payment-section']"

    LOGGER.info("Waiting for payment section to become visible")
    wait_until_visible(driver, xpath=xpath, duration=.2)
    
def check_submit_button(driver, xpath_o=None):
    if xpath_o:
        xpath = xpath_o
    else:
        xpath = "//button[text()='Submit Order']"

    LOGGER.info("Waiting for submit button to become clickable")
    wait_until_clickable(driver, xpath=xpath, duration=.2)

def click_submit_button(driver, xpath_o=None):
    if xpath_o:
        xpath = xpath_o
    else:
        xpath = "//button[text()='Submit Order']"

    element = wait_until_present(driver, xpath=xpath, duration=10)
    wait = WebDriverWait(driver, 10, 0.01)
    wait.until(lambda d: 'disabled' not in element.get_attribute('class'))
    
    LOGGER.info("Waiting for submit button to become clickable")
    wait_until_clickable(driver, xpath=xpath, duration=10)

    LOGGER.info("Clicking submit button")
    driver.find_element_by_xpath(xpath).click()

def poll_checkout_phase_one(driver):
    #Loop to determine which element appears first
    #Limit this loop as "Verify Phone Number" dialog may appear
    checkout_num_retries_attempted = 0
    checkout_num_retries = 25
    skip_add_address = False
    skip_select_shipping = False
    skip_payment = False
    while True:
        try:
            check_add_new_address_button(driver=driver)
            LOGGER.info("New Address button appeared!")
            break
        except Exception as e:
            LOGGER.exception("Failed visibility check for Add New Address button: " + str(e))
            
        try:
            check_shipping(driver=driver)
            LOGGER.info("Shipping options appeared!")
            skip_add_address = True
            break
        except Exception as e:
            LOGGER.exception("Failed visibility check for Shipping options: " + str(e))
            
        try:
            check_payment(driver=driver)
            LOGGER.info("Payment appeared!")
            skip_add_address = True
            skip_select_shipping = True
            break
        except Exception as e:
            LOGGER.exception("Failed visibility check for Payment: " + str(e))
        
        try:
            xpath = SUBMIT_BUTTON_XPATH
            check_submit_button(driver=driver, xpath_o=xpath)
            LOGGER.info("Submit Button appeared!")
            skip_add_address = True
            skip_select_shipping = True
            skip_payment = True
            break
        except Exception as e:
            LOGGER.exception("Failed visibility check for Submit Button: " + str(e))
            
        if checkout_num_retries_attempted < checkout_num_retries:
            checkout_num_retries_attempted += 1
            continue
        else:
            LOGGER.info("Too many iterations through checkout element check. Terminating check...")
            break
            
        return skip_add_address, skip_select_shipping, skip_payment
        
def poll_checkout_phase_two(driver):
    #Loop again to determine which element appears first
    # as we don't know which will appear next
    checkout_num_retries_attempted = 0
    checkout_num_retries = 25
    skip_payment = False
    while True:
                            
        try:
            check_payment(driver=driver)
            LOGGER.info("Payment appeared!")
            break
        except Exception as e:
            LOGGER.exception("Failed visibility check #2 for Payment: " + str(e))
    
        try:
            xpath = SUBMIT_BUTTON_XPATH
            check_submit_button(driver=driver, xpath_o=xpath)
            LOGGER.info("Submit Button appeared!")
            skip_payment = True
            break
        except Exception as e:
            LOGGER.exception("Failed visibility check #2 for Submit Button: " + str(e))
        
        if checkout_num_retries_attempted < checkout_num_retries:
            checkout_num_retries_attempted += 1
            continue
        else:
            LOGGER.info("Too many iterations through checkout element check #2. Terminating check...")
            break
        
        return skip_payment

def wait_until_clickable(driver, xpath=None, class_name=None, el_id=None, duration=10000, frequency=0.01):
    if xpath:
        WebDriverWait(driver, duration, frequency).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    elif class_name:
        WebDriverWait(driver, duration, frequency).until(EC.element_to_be_clickable((By.CLASS_NAME, class_name)))
    elif el_id:
        WebDriverWait(driver, duration, frequency).until(EC.element_to_be_clickable((By.ID, el_id)))


def wait_until_visible(driver, xpath=None, class_name=None, el_id=None, duration=10000, frequency=0.01):
    if xpath:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    elif class_name:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.CLASS_NAME, class_name)))
    elif el_id:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.ID, el_id)))
        
def wait_until_present(driver, xpath=None, class_name=None, el_id=None, duration=10000, frequency=0.01):
    if xpath:
        return WebDriverWait(driver, duration, frequency).until(EC.presence_of_element_located((By.XPATH, xpath)))
    elif class_name:
        return WebDriverWait(driver, duration, frequency).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))
    elif el_id:
        return WebDriverWait(driver, duration, frequency).until(EC.presence_of_element_located((By.ID, el_id)))