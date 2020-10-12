import requests
from bs4 import BeautifulSoup
from datetime import datetime, time, timedelta
import random
import time as the_time
from discord import Webhook, AsyncWebhookAdapter
import aiohttp
import asyncio
import json
import os
os.chdir(os.path.dirname(os.path.realpath(__file__)))

CONFIG = {}
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'}
ads = {}
first_run = True
session = None

#CONFIG FUNCTIONS

def load_config():
    global CONFIG
    with open('config.json', 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
    parse_config(CONFIG)

def parse_config(cfg):
	for i,site in enumerate(cfg['sites']):
		cfg['sites'][i]['f'] = globals()['update_'+site['name']]
	for key in cfg['notifier']['activity_hours']:
		cfg['notifier']['activity_hours'][key] = parse_hour(cfg['notifier']['activity_hours'][key])

def parse_hour(string):
    h, m = map(int,string.split(':'))
    return time(h,m)

# SITE FUNCTIONS
     
async def update_mobile(site):
	urls = site['urls']
	platform = site['name']
	new_ads = []
	for url in urls:
		async with session.get(url) as r:
			r = requests.get(url)
			soup = BeautifulSoup(await r.text(),'html.parser')
			section = soup.find('section',{'class' : 'srp-result-block'})
			ads = section.find_all('a',{'class': 'vehicle-data'})
			for ad in ads:
				href = 'https://www.mobile.de' + ad.get('href')
				new_ads.append({
					'href' : href,
					'title' : ad.find('h3').getText(),
					'platform' : platform,
					'url' : href
				})
	return new_ads


async def update_otomoto(site):
	urls = site['urls']
	platform = site['name']
	new_ads = []
	for url in urls:
		async with session.get(url) as r:
			soup = BeautifulSoup(await r.text(),'html.parser')
			ads = soup.find_all('a',{'class': 'offer-title__link'})
			for ad in ads:
				href = ad.get('href')
				new_ads.append({
					'href' : href,
					'title' : ad.get('title'),
					'platform' : platform,
					'url' : href
				})
	return new_ads

async def update_olx(site):
	urls = site['urls']
	platform = site['name']
	new_ads = []
	for url in urls:
		async with session.get(url) as r:
			soup = BeautifulSoup(await r.text(),'html.parser')
			table = soup.find('table',{'id': 'offers_table'})
			ads = table.find_all('a',{'class': 'detailsLink'})
			for ad in ads:
				href = ad.get('href')
				new_ads.append({
					'href' : href,
					'title' : ad.findChildren()[0].get('alt'),
					'platform' : platform,
					'url' : href
				})
	return new_ads


#WEBHOOK FUNCTIONS

async def send(text):
	async with aiohttp.ClientSession() as session:
		webhook = Webhook.from_url(CONFIG['webhook']['url'], adapter=AsyncWebhookAdapter(session))
		await webhook.send(text,username=CONFIG['webhook']['name'],avatar_url=CONFIG['webhook']['avatar_url'])

def notification_text(ad, i=None):
	idx_txt = '' if i == None else f'**{i+1}.** '
	return f"{idx_txt}@everyone `[{datetime.now().strftime('%H:%M')}] {ad['platform'].upper()}` **{ad['title']}**\n{ad['href']}"

#AD FUNCTIONS

async def handle_ads(new_ads):

	for old_href in dict(ads):
		if old_href not in [ad['href'] for ad in new_ads]:
			ads.pop(old_href,None)

	to_notify = []
	for ad in new_ads:
		href = ad['href']
		if href in ads:
			continue
		else:
			ads[href] = ad
			to_notify.append(ad)
	first_run = False
	if first_run == False and len(to_notify):
		await send(f'```css\n[{datetime.now().strftime("%H:%M")}] --- {len(to_notify)} new car{"s" if len(to_notify) != 1 else ""} ---```')
		for i, ad in enumerate(to_notify):
			await send(notification_text(ad,i))
	elif not len(to_notify):
		print(datetime.now(), "No results")

async def update():
	print('update')
	ads = []
	for site in CONFIG['sites']:
		if site['active']:
			ads += await site['f'](site)
	await handle_ads(ads)


def in_rh(start,end):
	now = datetime.now().time()
	condition = now >= start and now <= end
	return condition if start < end else not condition

def time_until(time,delta = timedelta()):
	now = datetime.now()
	future = datetime.now().replace(hour=time.hour,  minute=time.minute, microsecond=0, second=0) + delta
	if future < now:
		future += timedelta(days=1)
	return future - now

async def start():
	global session
	
	load_config()
	print('Config loaded.')
	first_run = True
	session = aiohttp.ClientSession(headers=headers)
	print('Session started.')
	print(datetime.now(), '| Scraping', sum([len(site['urls']) for site in CONFIG['sites'] if site['active']]), 'urls from', len([site for site in CONFIG['sites'] if site['active']]), 'different sites.')
	start = CONFIG['notifier']['activity_hours']['start']
	end = CONFIG['notifier']['activity_hours']['end']
	while True:
		irh = in_rh(start,end)
		_min, _max = (CONFIG['notifier']['sleep']['min'], CONFIG['notifier']['sleep']['max'])
		if irh:
			await update()
			first_run = False
			if _max > time_until(end).total_seconds():
				if start > end:
					sleep_until = start
					print(datetime.now(), f'Sleeping until start ({start})')
				else:
					sleep_until = end
					print(datetime.now(), f'Sleeping until end ({end})')
				st = time_until(sleep_until).total_seconds()
			else:
				st = random.uniform(_min,_max)
				print(datetime.now(), f'Sleeping randomly for {int(st)} seconds.')
		else:
			st = time_until(CONFIG['notifier']['activity_hours']['start']).total_seconds()
			print(datetime.now(), f'Sleeping until start ({start})')
		await asyncio.sleep(st)

asyncio.run(start())