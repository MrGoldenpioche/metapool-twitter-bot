# metapool-twitter-bot
Cool bot who queries metapool.tech API and create informationnal scheduled tweets.
For the moment, the scheduling of the tweets is fixed to :

 * 04:00
 * 08:00
 * 12:00
 * 16:00
 * 20:00
 * 00:00

## Get the latest version
```
git clone https://github.com/MrGoldenpioche/metapool-twitter-bot
cd metapool-twitter-bot
```

## Configure confidential settings of the bot
This script uses .env file to store sensitive datas like API secret and so on. 
You need to create this .env file on the same folder than twitter-bot.py.

`touch .env`

And add this content

```
TWITTER_CONSUMER_API_KEY=
TWITTER_CONSUMER_SECRET=
TWITTER_BEARER_TOKEN=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
SMTP_SERVER=
SMTP_PASSWORD=
SMTP_USER=
SMTP_RECEIVER=
SMTP_FROM=
```

Of you course, you need to have a twitter API account and optionnally SMTP settings for monitoring mode only

## Standalone run with bot enabled
```
python3 ./twitter-bot.py
```

## Standalone run with debugging mode
```
python3 -/twitter-bot.py --no-bot
```

## Build with dockers

```
git pull && docker-compose up --build -d
```
