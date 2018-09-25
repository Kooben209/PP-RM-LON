from   bs4 import BeautifulSoup
from splinter import Browser
import sys
import time


#browser = Browser('firefox', headless=True)
#browser = Browser('chrome', headless=True)
browser = Browser('phantomjs', load_images=False)

browser.visit('https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E984&radius=5.0&sortType=18&includeSSTC=true&keywords=probate%2Cexecutor')
time.sleep(10)
#if browser.is_element_present_by_xpath('//*[@id="l-searchResults"]/div[29]'):
	
html = browser.html

soup = BeautifulSoup(html, 'html.parser')

print(soup)

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
#else:
#	print('Page Element Not Found\n')
browser.quit()
sys.exit(0)

