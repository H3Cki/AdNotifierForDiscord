# AdNotifierForDiscord

Since notifications from sites OLX, OTOMOTO and Mobile.de are unreliable and I found myself forgetting about checking my bookmarked searches regularly, I made a scraping script that sends a notification to Discord using a webhook.

`! Mobile.de scraping is supported but it's disabled by default due to Mobile's terms of use prohibiting automated access.`

# Dependencies
```
``

# How to run
Requires Python 3.6 or higher.
```
pip install requirements.txt
python notifier.py
```


# Config
Configure the notifier by changing `config.json`.

```json
{
    "sites": [
         {
            "name": "otomoto",
            "active": true,
            "urls": []
        },
        {
            "name": "olx",
            "active": true,
            "urls": []
        },
        {
            "name": "mobile",
            "active": false,
            "urls": []
        }
    ],
    "webhook": {
        "name": "Notifier",
        "url": "",
        "avatar_url": ""
    },
    "notifier": {
        "activity_hours": {
            "start": "7:30",
            "end": "20:30"
        },
        "sleep": {
            "min": 300,
            "max": 1800
        }
    }
}
```

### sites
`name`    - name of the website, used later in config parsing  
`active`  - true if notifier should check this website  
`urls`    - list of search urls for this website  

### webhook
`name`  - name of the discord webhoon  
`url`   - url of the webhook (it can be obtained from channel settings)  
`avatar_url`  - avatar of the webhook  

### notifier

**activity_hours** - time window during which notifier is active.  
If `start` is less than `end` notifier will work in between set `start` and `end` hours.  
If `start` is greater then `end` notifier will work from `start` to `end` hour of the next day.

**sleep** - minimum and maximum number of seconds used to randomly sleep after each update.


# Config parsing
Script will iterate throught websites in `config["sites"]` to find coroutines that handle it's urls.  
Those functions must be named `update_x` where `x` is the website name.

Example for ebay:
```py
async def update_ebay(site):
  if site["active"]:
    print(f'{site["name"]} is ready and has {len(site["urls"])} search urls to check')
  else:
    print(f'{site["name"]} is inactive")
 ```
