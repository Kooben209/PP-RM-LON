from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
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
from getSoldPrices import getAllSoldPrices
import requests
import random

import json

import setEnvs

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")

chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("disable-infobars")
chrome_options.add_argument("--disable-extensions")

driverException = False
#driver = webdriver.Chrome(chrome_options=chrome_options,executable_path='/usr/local/bin/chromedriver')
driver = webdriver.Chrome(chrome_options=chrome_options)

def parseAskingPrice(aPrice):
	try:
		value = round(Decimal(sub(r'[^\d.]', '', aPrice)))
	except:
		value = 0
	return value
	
def saveToStore(data):
	scraperwiki.sqlite.execute("CREATE TABLE IF NOT EXISTS 'data' ( 'propId' TEXT, link TEXT, title TEXT, address TEXT, price BIGINT, 'displayPrice' TEXT, image1 TEXT, 'pubDate' DATETIME, 'addedOrReduced' DATE, reduced BOOLEAN, location TEXT, displaySoldPrice TEXT,soldPrice BIGINT,soldDate DATETIME,priceDifference TEXT,isPriceIncrease BOOLEAN,hasMoreThanOneSaleHistoryItem BOOLEAN, hashTagLocation TEXT, postContent TEXT, CHECK (reduced IN (0, 1)),  PRIMARY KEY('propId'))")
	scraperwiki.sqlite.execute("CREATE UNIQUE INDEX IF NOT EXISTS 'data_propId_unique' ON 'data' ('propId')")
	scraperwiki.sqlite.execute("INSERT OR IGNORE INTO 'data' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (data['propId'], data['link'], data['title'], data['address'], data['price'], data['displayPrice'], data['image1'], data['pubDate'], data['addedOrReduced'], data['reduced'], data['location'],None,None,None,None,None,None,data['hashTagLocation'],data['postContent']))
	changes = scraperwiki.sqlite.execute("SELECT changes();")
	return changes['data'][0][0]
 	#scraperwiki.sqlite.commit()
	
excludeAgents = []
if os.environ.get("MORPH_EXCLUDE_AGENTS") is not None:
	excludeAgentsString = os.environ["MORPH_EXCLUDE_AGENTS"]
	excludeAgents = excludeAgentsString.lower().split("^")

filtered_dict = {k:v for (k,v) in os.environ.items() if 'MORPH_URL' in k}

postTemplates = {k:v for (k,v) in os.environ.items() if 'ENTRYTEXT' in k}
sleepTime = 5

if os.environ.get("MORPH_DB_ADD_COL") is not None:
    if os.environ.get("MORPH_DB_ADD_COL") == '1':
        try:
            scraperwiki.sqlite.execute('ALTER TABLE data ADD COLUMN hashTagLocation TEXT')
        except:
            print('col - hashTagLocation exists')
        try:
            scraperwiki.sqlite.execute('ALTER TABLE data ADD COLUMN postContent TEXT')
        except:
            print('col - postContent exists')

remoteEndpoint='#'
if os.environ.get("MORPH_REMOTE_ENDPOINT") is not None:
	remoteEndpoint = os.environ["MORPH_REMOTE_ENDPOINT"]

if os.environ.get("MORPH_SLEEP") is not None:
	sleepTime = int(os.environ["MORPH_SLEEP"])

for k, v in filtered_dict.items(): 
	checkURL = v
	if os.environ.get('MORPH_MAXDAYS') == "0":
		checkURL = checkURL.replace("&maxDaysSinceAdded=1","")
		
	if os.environ.get('MORPH_DEBUG') == "1":
		print(checkURL)
	try:
		if driverException == True:
			driver = webdriver.Chrome(chrome_options=chrome_options)
			driverException = False
		driver.get(checkURL)
		numOfPages = int(driver.find_element_by_css_selector("span[class='pagination-pageInfo'][data-bind='text: total']").text)
	except ValueError:
		numOfPages = 0	
	except WebDriverException as e:
		print(k.replace("MORPH_URL_","").replace("_"," ").title())
		print("WebDriverException Exception: {0} Message: {1}".format("e message", str(e)))		
		driverException = True
		driver.quit()
		continue

	print("NumberOfPages:"+str(numOfPages))
	
	matchesList = []

	page = 0
	while page < numOfPages:
		numResults=0
		numPreFeat=0
		numNormFeat=0
		numFeat=0
		
		try:
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
						postKey = random.choice(list(postTemplates))

						if advert.find("div", {"class" : "propertyCard-branchLogo"}).find("a" , {"class" : "propertyCard-branchLogo-link"}) is not None:
							agent = advert.find("div", {"class" : "propertyCard-branchLogo"}).find("a" , {"class" : "propertyCard-branchLogo-link"}).get("title")
							if any(x in agent.lower() for x in excludeAgents):
								continue

						hashTagLocation = k.replace("MORPH_URL_","").replace("_"," ").title().replace(" ","")
						location = k.replace("MORPH_URL_","").replace("_"," ").title()
						propLink="https://www.rightmove.co.uk"+advert.find("a", {"class" : "propertyCard-link"}).get('href')
						propId=re.findall('\d+',propLink)
						title = advert.find("h2", {"class" : "propertyCard-title"}).text
						address = advert.find("address", {"class" : "propertyCard-address"}).text
						link = advert.find("a", {"class" : "propertyCard-link"})
						price = parseAskingPrice(advert.find("div", {"class" : "propertyCard-priceValue"}).text)
						displayPrice = advert.find("div", {"class" : "propertyCard-priceValue"}).text
						if advert.find("img", {"alt" : "Property Image 1"}) is None:
							image1 = advert.findAll("img")[0].get('src')
						else:
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
						advertMatch['hashTagLocation'] = address
						advertMatch['postContent'] = postTemplates[postKey].format(title, hashTagLocation, displayPrice)
                        
						#scraperwiki.sqlite.save(['propId'],advertMatch)
						dbChanges = saveToStore(advertMatch)
						if dbChanges > 0:
							matchesList.append(advertMatch)
       
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
				time.sleep(sleepTime)
				next_page = driver.find_element_by_css_selector('.pagination-direction--next')
				next_page.click()
				time.sleep(sleepTime)
				
		except WebDriverException as e:
			print(k.replace("MORPH_URL_","").replace("_"," ").title())
			print("WebDriverException Exception: {0} Message: {1}".format("e message", str(e)))		
			driverException = True
			driver.quit()
			break
		page +=1 
	time.sleep(sleepTime)
 
	#post all matches to remote data store api
	numMatches = len(matchesList)
	if remoteEndpoint != '#' and numMatches > 0:
		r = requests.post(remoteEndpoint, json=json.dumps(matchesList, default=str))
		if r.status_code == 200:
			print('{0} Record(s) posted to endpoint'.format(str(numMatches)))
		elif r.status_code == 409:
			print('Database Conflict Error when posting {0} record(s) to endpoint'.format(str(numMatches)))
		elif r.status_code == 500:
			print('Internal Server Error when posting {0} record(s) to endpoint'.format(str(numMatches)))
		else:
			print('Unspecified Error when posting {0} record(s) to endpoint'.format(str(numMatches)))

driver.quit()

today = datetime.today()
timestr = today.strftime('%Y-%m-%d')

currentMonth=timestr
with requests.session() as s:
	s.headers['user-agent'] = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'
	r1 = s.get('https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads')
	soup = BeautifulSoup(r1.content, 'html.parser')
	currentMonthText = soup.find("h2", {"id" : lambda L: L and L.startswith('current-month-')})
	if currentMonthText is not None:
		currentMonth = currentMonthText.text.replace('Current month (','').replace(' data)','').strip()
		currentMonth = datetime.strptime(currentMonth,'%B %Y').strftime('%Y-%m-%d')

if os.environ.get('MORPH_RUN_SOLD_PRICES') == "1":
	getAllSoldPrices(currentMonth)
	
sys.exit(0)
