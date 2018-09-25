import scraperwiki
import requests
import sqlite3
from   bs4 import BeautifulSoup
import sys
import time

from splinter import Browser

browser = Browser('firefox', headless=True)

browser.visit('https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E984&radius=5.0&sortType=18&includeSSTC=true&keywords=probate%2Cexecutor')

if browser.is_element_present_by_xpath('//*[@id="l-searchResults"]/div[29]'):
	time.sleep(3)
	html = browser.html
	soup = BeautifulSoup(html, 'html.parser')

	searchResults = soup.find("div", {"id" : "l-searchResults"})
	matches = 0
	if searchResults is not None:
		adverts = searchResults.findAll("div", {"id" : lambda L: L and L.startswith('property-')})
		for advert in adverts:
			if advert.find("div", {"class" : "propertyCard-keywordTag matched"}) is not None:
				matches += 1
		print("Found "+str(matches)+" Matches from "+str(len(adverts))+" Items")
	else:
		print('No Search Results\n')

browser.quit()
sys.exit(0)

