from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
from bs4 import BeautifulSoup
import regex as re
from datetime import datetime
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKING_URL = "https://libcal.library.gatech.edu/spaces/bookings?lid=18640&gid=39399"
NOW = datetime.now().isoformat()


@contextmanager
def setup(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(url)
        driver.implicitly_wait(100)
        yield driver
    finally:
        driver.quit()
        
def transform_datetime(date):
    cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date)
    dt = datetime.strptime(cleaned, "%I:%M%p %a %b %d %Y")
    return dt.isoformat()
        
def html_scrape(html, now_time):
    table_data_list = []
    
    soup = BeautifulSoup(html, "html.parser")
    table_body = soup.find("tbody")
    rows = table_body.find_all("tr")
    
    for row in rows:
        booking_info = {}
        table_data = row.find_all("td")
        booking_info["booking_name"] = table_data[0].text.lower()
        time = table_data[1].text
        start_time_temp, end_time_temp = time.split(" - ")
        
        end_time_match = re.match(r"^(\d+:\d+[ap]m) (.*)$", end_time_temp)
        end_time = end_time_match.group(1)
        end_time_date = end_time_match.group(2)
        

        if len(start_time_temp) <= 7:
            booking_info["start_time"] = transform_datetime(start_time_temp + " " + end_time_date)
        else:
            start_time_match= re.match(r"^(\d+:\d+[ap]m) (.*)$", start_time_temp)
            start_time = start_time_match.group(1)
            start_time_date = start_time_match.group(2)
            booking_info["start_time"] = transform_datetime(start_time + " " + start_time_date)
            
        booking_info["end_time"] = transform_datetime(end_time + " " + end_time_date) 
        
        room_name = table_data[2].text.lower()
        
        booking_info["room_id"] = room_name.replace(" ", "_")
        
        booking_info["room_name"] = room_name
        
        booking_info["category"] = table_data[3].text.lower()
        
        booking_info["scraped_time"] = now_time
        
        
        table_data_list.append(booking_info)
        
    return table_data_list

def scrape_bookings(driver):
    bookings = []
    dropdown = Select(driver.find_element(By.ID, "d"))
    dropdown.select_by_value("180")
    wait = WebDriverWait(driver, 10)
    
    
    while True:
        
        next_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.page-link.next")))
        
        html = driver.page_source
        data = html_scrape(html, NOW)
        bookings.extend(data)
        
        aria_disabled = driver.execute_script(
            "return arguments[0].getAttribute('aria-disabled');", next_btn
        )
        if aria_disabled == "true":
            print("Scrape Successful")
            break
        
        old_first_row = driver.find_elements(By.CSS_SELECTOR, "table.dataTable tbody tr")[0]
        
        driver.execute_script("arguments[0].click();", next_btn)

        wait.until(EC.staleness_of(old_first_row))
        
    return bookings


# with setup(BOOKING_URL) as driver:
#     output_dir_data_raw = os.path.join(BASE_DIR, "..", "..", "data", "raw")
#     os.makedirs(output_dir_data_raw, exist_ok=True)
#     booking_data_path = os.path.join(output_dir_data_raw, "booking.json")
#     with open(booking_data_path, "w", encoding="utf-8") as outfile:
#         booking_data = scrape_bookings(driver)
#         json.dump(booking_data, outfile)


def lambda_executor():