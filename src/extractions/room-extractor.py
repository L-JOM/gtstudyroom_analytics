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
ROOM_URL = "https://libcal.library.gatech.edu/reserve/study-rooms"
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
        
def get_table_dim(html):
    rooms = []
    
    soup = BeautifulSoup(html, "html.parser")
    format_table = soup.find("table", class_="fc-datagrid-body fc-scrollgrid-sync-table")
    rows = format_table.find_all("tr")
    FIELDS = {"room_id": "", "capacity": 0,"building":"","floor": 0, "room_name":""}
    for room in rows:
        room_dict = FIELDS.copy()
        text = room.find("span", class_="fc-cell-text s-lc-filter-2597 s-lc-filter-2598").text
        room_data = re.search(r"^([\w\s-]+) \(Capacity (\d+)\)", text)
        room_name = room_data.group(1).lower()
        capacity = int(room_data.group(2))
        
        room_dict["room_name"] = room_name
        room_id = re.search(r"([\w\s]+[\da-zA-z]+)", room_name).group()
        room_dict["room_id"] = room_id.strip().replace(' ', '_')
        room_dict["capacity"] = capacity
        
        building = re.search(r"^([A-Za-z\s]+)\s+([A-Za-z\d]?)\w*", room_name)
        room_dict["building"] = building.group(1)
        room_dict["floor"] = building.group(2)
        rooms.append(room_dict)
    return rooms

def scrape_room_dim(driver):
    html = driver.page_source
    return get_table_dim(html)


# with setup(ROOM_URL) as driver:
#     output_dir_data_raw = os.path.join(BASE_DIR, "..", "..", "data", "raw")
#     os.makedirs(output_dir_data_raw, exist_ok=True)
#     booking_data_path = os.path.join(output_dir_data_raw, "rooms.json")
#     with open(booking_data_path, "w", encoding="utf-8") as outfile:
#         booking_data = scrape_room_dim(driver)
#         json.dump(booking_data, outfile)

