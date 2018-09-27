from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")

chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("disable-infobars")
chrome_options.add_argument("--disable-extensions")

driver = webdriver.Chrome(chrome_options=chrome_options,executable_path='/usr/local/bin/chromedriver')
driver.get("https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E984&radius=5.0&sortType=18&includeSSTC=true&keywords=probate%2Cexecutor")
#lucky_button = driver.find_element_by_css_selector("[name=btnI]")
#lucky_button.click()

print(driver.page_source)

driver.quit()
