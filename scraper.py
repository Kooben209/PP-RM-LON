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
driver.get("https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E984&radius=5.0&sortType=18&includeSSTC=true&keywords=probate%2Cexecutor")

if driver.find_element_by_xpath('//*[@id="l-searchResults"]/div[29]'):

	html = driver.page_source
	soup = BeautifulSoup(html, 'html.parser')
	
	searchResults = soup.find("div", {"id" : "l-searchResults"})
	matches = 0
	if searchResults is not None:
		numOfPages = driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div[3]/div/div/div/div[2]/span[3]').text
		print("NumberOfPages:"+numOfPages)
    adverts = searchResults.findAll("div", {"id" : lambda L: L and L.startswith('property-')})
		for advert in adverts:
			if advert.find("div", {"class" : "propertyCard-keywordTag matched"}) is not None:
				title = advert.find("h2", {"class" : "propertyCard-title"}).text
				address = advert.find("address", {"class" : "propertyCard-address"}).find("span").text
				link = advert.find("a", {"class" : "propertyCard-link"})
				price = advert.find("div", {"class" : "propertyCard-priceValue"}).text
				print(title+" - "+address+" - "+price)
				matches += 1
		print("Found "+str(matches)+" Matches from "+str(len(adverts))+" Items")
	else:
		print('No Search Results\n')
else:
	print('Page Element Not Found\n')

driver.quit()
