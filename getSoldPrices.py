import csv
import time
from datetime import datetime
import requests
import sys
import os
import json
import math
from decimal import Decimal
from re import sub
import scraperwiki
import sqlite3

import setEnvs 

SoldDateCutoff = '2018-12-01' #default date if no arg

def parseAskingPrice(aPrice):
	try:
		value = round(Decimal(sub(r'[^\d.]', '', aPrice)))
	except:
		value = 0
	return value

def getAllSoldPrices(currentMonth=SoldDateCutoff):
	sleepTime = 2
	if os.environ.get("MORPH_SLEEP") is not None:
		sleepTime = int(os.environ["MORPH_SLEEP"])

	if os.environ.get("MORPH_SOLD_DATE_CUTOFF") is not None:
		if os.environ.get("MORPH_SOLD_DATE_CUTOFF") == 'none':
			SoldDateCutoff = currentMonth
		else:
			SoldDateCutoff = os.environ["MORPH_SOLD_DATE_CUTOFF"]
	
	print('SoldDateCutoff: '+SoldDateCutoff)
	
	SoldPriceURL = ''
	if os.environ.get("MORPH_SOLD_PRICE_URL") is not None:
		SoldPriceURL = os.environ["MORPH_SOLD_PRICE_URL"]
		
	db = sqlite3.connect('data.sqlite')
	db.row_factory = sqlite3.Row
	cursor = db.cursor()

	if os.environ.get("MORPH_DB_ADD_COL") is not None:
		if os.environ.get("MORPH_DB_ADD_COL") == '1':
			cursor.execute('PRAGMA TABLE_INFO(data)')
			columns = [tup[1] for tup in cursor.fetchall()]
			if 'displaySoldPrice' not in columns:
				cursor.execute('ALTER TABLE data ADD COLUMN displaySoldPrice TEXT')
			if 'soldPrice' not in columns:
				cursor.execute('ALTER TABLE data ADD COLUMN soldPrice BIGINT')
			if 'soldDate' not in columns:
				cursor.execute('ALTER TABLE data ADD COLUMN soldDate DATETIME')
			if 'priceDifference' not in columns:
				cursor.execute('ALTER TABLE data ADD COLUMN priceDifference TEXT')
			if 'isPriceIncrease' not in columns:
				cursor.execute('ALTER TABLE data ADD COLUMN isPriceIncrease BOOLEAN')
			if 'hasMoreThanOneSaleHistoryItem' not in columns:
				cursor.execute('ALTER TABLE data ADD COLUMN hasMoreThanOneSaleHistoryItem BOOLEAN')

	cursor.execute('''SELECT * FROM data  WHERE soldPrice is null and pubDate < ?''',(SoldDateCutoff,))
	all_rows = cursor.fetchall()

	line_count = 0
	foundSoldPrices = 0
	with requests.session() as s:
		s.headers['user-agent'] = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'

		for row in all_rows:
			if os.environ.get('MORPH_DEBUG') == "1":
				print('{0} - {1} - {2}'.format(row['propId'], row['link'], row['pubDate']))
			pubDate = datetime.strptime(row['pubDate'], "%Y-%m-%d %H:%M:%S.%f")
			checkURL = row['link']
			time.sleep(sleepTime)
			r1 = s.get(checkURL)
			time.sleep(sleepTime)
			r1 = s.get(checkURL+'#historyMarket')
			time.sleep(sleepTime)
			soldPriceCheckURL = SoldPriceURL+row['propId']
			time.sleep(sleepTime)
			r1 = s.get(soldPriceCheckURL)
			salesHistoryDic=json.loads(r1.content)
			
			if salesHistoryDic:
				if len(salesHistoryDic['saleHistoryItems']) > 0:
					priceDifference = salesHistoryDic['saleHistoryItems'][0].get('priceDifference')
					isPriceIncrease = salesHistoryDic['saleHistoryItems'][0].get('isPriceIncrease',False)
					hasMoreThanOneSaleHistoryItem = salesHistoryDic['saleHistoryItems'][0].get('hasMoreThanOneSaleHistoryItem',False)
					
					if 'dateSold' in salesHistoryDic['saleHistoryItems'][0]:
						lastSoldDate = salesHistoryDic['saleHistoryItems'][0]['dateSold']
						lastSoldDate = datetime.strptime(lastSoldDate, "%Y")
						if lastSoldDate.year >= pubDate.year:
							displayLastSoldPrice = salesHistoryDic['saleHistoryItems'][0]['price']
							lastSoldPrice = parseAskingPrice(displayLastSoldPrice.strip())
							print('Recent last sold data found for '+str(row['propId']))
							cursor.execute('''UPDATE data SET hasMoreThanOneSaleHistoryItem=?, isPriceIncrease=?, priceDifference=?, displaySoldPrice = ?, soldPrice = ?, soldDate = ? WHERE propId = ? ''',(hasMoreThanOneSaleHistoryItem,isPriceIncrease,priceDifference,displayLastSoldPrice,lastSoldPrice, lastSoldDate, row['propId']))
							db.commit()
							foundSoldPrices += 1

			line_count += 1
	print(f'Processed {line_count} lines.')
	print(f'Found {foundSoldPrices} Recent Sold Prices.')
	db.close()
	
if __name__ == '__main__':
	if len(sys.argv) > 1:
		SoldDateCutoff = sys.argv[1]
	getAllSoldPrices(SoldDateCutoff)
