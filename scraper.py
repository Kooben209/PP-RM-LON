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

def parseAskingPrice(aPrice):
	try:
		value = round(Decimal(sub(r'[^\d.]', '', aPrice)))
	except:
		value = 0
	return value

sleepTime = 2
if os.environ.get("MORPH_SLEEP") is not None:
	sleepTime = int(os.environ["MORPH_SLEEP"])

SoldDateCutoff = '20181201'
if os.environ.get("MORPH_SOLD_DATE_CUTOFF") is not None:
	SoldDateCutoff = os.environ["MORPH_SOLD_DATE_CUTOFF"]
	
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

cursor.execute('''SELECT * FROM data  WHERE pubDate < ?''',(SoldDateCutoff,))
all_rows = cursor.fetchall()

print(str(len(all_rows)))

sys.exit()
