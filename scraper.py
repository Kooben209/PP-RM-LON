from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from   bs4 import BeautifulSoup
import sys
import time
import scraperwiki
import sqlite3
import re
from re import sub
from datetime import datetime, timedelta
from decimal import Decimal


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")

chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("disable-infobars")
chrome_options.add_argument("--disable-extensions")

driver = webdriver.Chrome(chrome_options=chrome_options,executable_path='/usr/local/bin/chromedriver')

def parseAskingPrice(aPrice):
	try:
		value = round(Decimal(sub(r'[^\d.]', '', aPrice)))
	except:
		value = 0
	return value
	
def saveToStore(data):
	scraperwiki.sqlite.execute("CREATE TABLE IF NOT EXISTS swdata ( 'propId' TEXT, link TEXT, title TEXT, address TEXT, price BIGINT, 'displayPrice' TEXT, image1 TEXT, 'pubDate' DATETIME, 'addedOrReduced' DATE, reduced BOOLEAN, location TEXT, CHECK (reduced IN (0, 1)), PRIMARY KEY('propId'))")
	scraperwiki.sqlite.execute("CREATE UNIQUE INDEX IF NOT EXISTS 'swdata_propId_unique' ON swdata ('propId')")
	scraperwiki.sqlite.execute("INSERT OR IGNORE INTO 'swdata' VALUES (?,?,?,?,?,?,?,?,?,?,?)", (data['propId'], data['link'], data['title'], data['address'], data['price'], data['displayPrice'], data['image1'], data['pubDate'], data['addedOrReduced'], data['reduced'], data['location']))
	#scraperwiki.sqlite.commit()
	
excludeAgents = ['andrew granger']

filtered_dict = {k:v for (k,v) in os.environ.items() if 'MORPH_URL' in k}

sleepTime = 5
if os.environ.get("MORPH_SLEEP") is not None:
	sleepTime = int(os.environ["MORPH_SLEEP"])

for k, v in filtered_dict.items(): 
	checkURL = v
	if os.environ.get('MORPH_DEBUG') == "1":
		print(checkURL)
	driver.get(checkURL)
	try:
		numOfPages = int(driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[1]/div[3]/div/div/div/div[2]/span[3]').text)
	except ValueError:
		numOfPages = 0	

	print("NumberOfPages:"+str(numOfPages))

	page = 0
	while page < numOfPages:
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
				reduced=False
				if advert.find("div", {"class" : "propertyCard-keywordTag matched"}) is not None:
					advertMatch = {}
					agent = advert.find("span", {"class" : "propertyCard-branchSummary-branchName"}).text
					if any(x in agent.lower() for x in excludeAgents):
						continue;

					location = k.replace("MORPH_URL_","").replace("_"," ").title()
					propLink="https://www.rightmove.co.uk"+advert.find("a", {"class" : "propertyCard-link"}).get('href')
					propId=re.findall('\d+',propLink)
					title = advert.find("h2", {"class" : "propertyCard-title"}).text
					address = advert.find("address", {"class" : "propertyCard-address"}).find("span").text
					link = advert.find("a", {"class" : "propertyCard-link"})
					price = parseAskingPrice(advert.find("div", {"class" : "propertyCard-priceValue"}).text)
					displayPrice = advert.find("div", {"class" : "propertyCard-priceValue"}).text
					image1 = advert.find("img", {"alt" : "Property Image 1"}).get('src')
					addedOrReduced = advert.find("span", {"class" : "propertyCard-branchSummary-addedOrReduced"}).text
					if addedOrReduced != None and addedOrReduced != "":
						if "Reduced" in addedOrReduced:
							reduced=True
						if "yesterday" in addedOrReduced:
							addedOrReduced=datetime.now().date()- timedelta(days=1)
						elif "today" in addedOrReduced:	
							addedOrReduced=datetime.now().date()
						else:
							dateMatch = re.search(r'\d{2}/\d{2}/\d{4}', addedOrReduced)
							addedOrReduced = datetime.strptime(dateMatch.group(), '%d/%m/%Y').date()
					else:
						addedOrReduced = datetime.now().date()
					advertMatch['propId'] = propId[0]
					advertMatch['link'] = propLink
					advertMatch['title'] = title
					advertMatch['address'] = address
					advertMatch['price'] = price
					advertMatch['displayPrice'] = displayPrice
					advertMatch['image1'] = image1
					advertMatch['pubDate'] = datetime.now()
					advertMatch['addedOrReduced'] = addedOrReduced
					advertMatch['reduced'] = reduced
					advertMatch['location'] = location

					#scraperwiki.sqlite.save(['propId'],advertMatch)
					
					saveToStore(advertMatch)
					
					matches += 1
			print("Found "+str(matches)+" Matches from "+str(numResults)+" Items of which "+str(numFeat)+" are Featured")
			if matches == 0 or (numResults-numFeat-2)>matches:
				break		
		else:
			print('No Search Results\n')
		
		if numOfPages > 1:
			if page == 0: 
				close_cookie = driver.find_element_by_css_selector('#cookiePolicy > div > button')
				print(close_cookie)
				close_cookie.click()
			time.sleep(sleepTime)
			next_page = driver.find_element_by_css_selector('.pagination-direction--next')
			next_page.click()
			time.sleep(sleepTime)
		page +=1 
	time.sleep(sleepTime)
driver.quit()
sys.exit(0)




