import argparse
import logging
import os
import random
import re
import select
import smtplib
import ssl
import subprocess
import time
import timeit
import math
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from statistics import mean

import backoff
import requests
import schedule
import tweepy
from dotenv import load_dotenv
from tweepy import TweepyException

API_STATS_BASE = "https://api.metapool.tech/pool/stats"

class Monitor:
    def __init__(self, smtpServer, smtpSender, smtpPassword, smtpReceiver, smtpFrom, smtpPort=465):
        self.server = smtpServer
        self.port = smtpPort
        self.senderEmail = smtpSender
        self.receiverEmail = smtpReceiver
        self.password = smtpPassword
        
        if smtpFrom is not None:
            self.fromHeader = smtpFrom
        else:
            self.fromHeader = smtpSender

    def sendMessage(self, application, error, origText):
        # Try to log in to server and send email
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.server, self.port, context=context) as server:
                server.login(self.senderEmail, self.password)
                server.ehlo()
                message = MIMEMultipart()
                message.add_header('From', self.fromHeader)
                message.add_header('To', self.receiverEmail)
                message.add_header('Subject', f"Error from {application}")
                message.attach(MIMEText(f"Error message: {error}\nTry to send: {origText}", 'plain'))
                server.sendmail(self.senderEmail, self.receiverEmail, message.as_string())

        except Exception as e:
            print(f"SMTP Error: {e}")
        finally:
            server.connect(self.server, self.port)
            server.quit()

class TwitterBot:
    def __init__(self, consumerKey, consumerSecret, bearer, accessToken, accessSecret, botEnabled=True, monitor=None):
        self.consumerKey = consumerKey
        self.consumerSecret = consumerSecret
        self.accessToken = accessToken
        self.accessSecret = accessSecret
        self.bearer = bearer
        self.botEnabled = botEnabled
        self.monitor = monitor

        self.bot = tweepy.Client(bearer_token=self.bearer,
                                consumer_key=self.consumerKey,
                                consumer_secret=self.consumerSecret, 
                                access_token=self.accessToken,
                                access_token_secret=self.accessSecret)
        

    def sendMessage(self, text):
        print(f"----\nBot Twitter: {text}")
        if self.botEnabled:
            for __ in range(3):
                try:
                    self.bot.create_tweet(text=text)
                except TweepyException as e:
                    if self.monitor is not None:
                        self.monitor.sendMessage("Twitter", e, text)
                    print(e)
                    time.sleep(2)
                    continue
                else: 
                    break

    #Get desired stat from metapool API
    def getPoolStat(self, value):
        session = requests.Session()
        response = session.get(API_STATS_BASE)
        desiredStat = response.json().get(value)

        if desiredStat:
            #print(value + " = " + str(desiredStat))
            return desiredStat
        else:
            return 0

def stats(twitterBot):

    #Retrieve Pool statistics
    metaGlobalHashrate = twitterBot.getPoolStat('global_hashrate')
    metaNumWorker = twitterBot.getPoolStat('num_workers')
    metaDifficulty = twitterBot.getPoolStat('difficulty')
    metaPoolHashrate = twitterBot.getPoolStat('pool_hashrate')
    metaPendingPayout = twitterBot.getPoolStat('total_pending_payout')
    metaTotalPayout = twitterBot.getPoolStat('total_payout_amount')

    #compute hashrate unit
    metaGlobalHashrate = round((metaGlobalHashrate / 1000000000000),2)
    metaPoolHashrate = round((metaPoolHashrate / 1000000000),2)
    metaPoolHashratePercent = round(((metaPoolHashrate * 1)/metaGlobalHashrate),2)

    #Build the tweet
    tweet = ""
    tweet += f"The best Alephium Community pool"
    tweet += f"\n\n Network Hashrate : {metaGlobalHashrate} TH/s"
    tweet += f"\n Pool Hashrate : {metaPoolHashrate} GH/s ({metaPoolHashratePercent} % of total)"
    if metaNumWorker > 0:
        tweet += f"\n Current Miners : {metaNumWorker}"
    tweet += f"\n Pending Rewards : {round(metaPendingPayout)} \u2135"
    tweet += f"\n Total Rewards paid : {round(metaTotalPayout)} \u2135"
    tweet += f"\n\n#blockchain #alephium #metapool"

    twitterBot.sendMessage(tweet[:280])

@staticmethod
def humanFormat(num, round_to=2):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, round_to)
    return '{:.{}f} {}'.format(num, round_to, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

def main(botEnabled, statsEnabled):
    load_dotenv()

    TWITTER_CONSUMER_API_KEY = os.getenv("TWITTER_CONSUMER_API_KEY")
    TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
    
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_RECEIVER = os.getenv("SMTP_RECEIVER")
    SMTP_FROM = os.getenv("SMTP_FROM")

    print(
        f"Start options:\n\tBot enabled: {botEnabled}\n"
            )

    monitor = Monitor(SMTP_SERVER, SMTP_USER, SMTP_PASSWORD, SMTP_RECEIVER, SMTP_FROM)
    bot = TwitterBot(TWITTER_CONSUMER_API_KEY, TWITTER_CONSUMER_SECRET,
                                        TWITTER_BEARER_TOKEN, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET, botEnabled, monitor)
    #scheduling
    if statsEnabled:
        #schedule.every().minutes.do(stats, bot)
        schedule.every().hours.at(":00").do(stats, bot)
    
    while True:
       schedule.run_pending()
       time.sleep(1)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot", help="Enable bot message", action='store_true')
    parser.add_argument("--no-bot", help="Disable bot message", dest="bot", action='store_false')
    parser.set_defaults(bot=True)

    parser.add_argument("--stat", help="Enable stats messages", action='store_true')
    parser.add_argument("--no-stat", help="Disable stats messages", dest="stats", action='store_false')
    parser.set_defaults(stats=True)
    
    args = parser.parse_args()
    main(args.bot, args.stats)

