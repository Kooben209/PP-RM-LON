from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from   bs4 import BeautifulSoup
import sys
import time


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")

chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("disable-infobars")
chrome_options.add_argument("--disable-extensions")

driver = webdriver.Chrome(chrome_options=chrome_options,executable_path='/usr/local/bin/chromedriver')
driver.get("https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E984&radius=40.0&sortType=18&includeSSTC=true&keywords=probate%2Cexecutor")

try:
	numOfPages = int(driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div[3]/div/div/div/div[2]/span[3]').text)
except ValueError:
	numOfPages = 0	

print("NumberOfPages:"+str(numOfPages))

page = 0
while page < numOfPages:
	print(driver.current_url)
	numResults=0
	numPreFeat=0
	numNormFeat=0
	numFeat=0
	
	html = driver.page_source
	soup = BeautifulSoup(html, 'html.parser')
	
	searchResults = soup.find("div", {"id" : "l-searchResults"})
	matches = 0
	if searchResults is not None:		
		adverts = searchResults.findAll("div", {"id" : lambda L: L and L.startswith('property-')})
		numResults = len(adverts)
		numPreFeat = len(searchResults.findAll("div", {"class" : "propertyCard propertyCard--premium propertyCard--featured"}))
		numNormFeat = len(searchResults.findAll("div", {"class" : "propertyCard propertyCard--featured"}))
		numFeat = numPreFeat+numNormFeat
		
		for advert in adverts:
			if advert.find("div", {"class" : "propertyCard-keywordTag matched"}) is not None:
				title = advert.find("h2", {"class" : "propertyCard-title"}).text
				address = advert.find("address", {"class" : "propertyCard-address"}).find("span").text
				link = advert.find("a", {"class" : "propertyCard-link"})
				price = advert.find("div", {"class" : "propertyCard-priceValue"}).text
				print(title+" - "+address+" - "+price)
				matches += 1
		print("Found "+str(matches)+" Matches from "+str(numResults)+" Items of which "+str(numFeat)+" are Featured")
		if matches == 0 or (numResults-numFeat-2)>matches:
			break		
	else:
		print('No Search Results\n')
	
	if numOfPages > 1:
		if page == 0: 
			close_cookie = driver.find_element_by_css_selector('#cookiePolicy > div > button')
			close_cookie.click()
		time.sleep(5)
		next_page = driver.find_element_by_css_selector('.pagination-direction--next')
		next_page.click()
		time.sleep(5)
	page +=1 

driver.quit()

