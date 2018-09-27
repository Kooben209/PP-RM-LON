from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")



driver = webdriver.Chrome(chrome_options=chrome_options)
driver.get("https://www.google.com")
lucky_button = driver.find_element_by_css_selector("[name=btnI]")
lucky_button.click()

print(driver.page_source)
