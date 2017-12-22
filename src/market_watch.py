from binance.client import Client
from src.util import MarketUtilities
import pymongo
from src.stream import BinanceStream
import time
from multiprocessing import Process
from src.notify import ClientNotif


class MarketWatch(object):
    # secret: <your secret here>
    # key: <your key here>
    f = open("../.authentication", "r")
    raw_file_data = f.readlines()
    file_info = {}
    for row in raw_file_data:
        split = row.split(":")
        file_info[split[0]] = split[1]

    key = file_info['key']
    secret = file_info['secret']

    def __init__(self):
        self.client = Client(self.key, self.secret)
        self.mongo_client = pymongo.MongoClient('localhost', 27017)
        self.db = self.mongo_client.crypto_data
        self.stream = BinanceStream(self.client)
        self.stream.update_crypto_data(self.db)
        # Put username and secret for TextMagic below
        self.notify = ClientNotif('','', self.db)

    def run(self, period):
        start_time = time.time()
        while True:
            self.stream.update_crypto_data(self.db)
            time.sleep(1)
            market_opportunity = self.field_check(period)
            if market_opportunity is not None:
                print("Market Opportunity Found")
                # self.client.order_limit_buy()
                self.notify.message_all("Market Opportunity Found: " + market_opportunity["symbol"])
                print("Following Opp, Splitting Process")
                p = Process(target=self.follow_opp, args=(market_opportunity, period))
                p.start()

    def field_check(self, period):
        for ticker in self.client.get_all_tickers():
            # Need to filter by volume
            # If the amount we own is greater than .1% [determine the right percent] of the volume, ignore
            asset = self.db.find({'symbol', ticker['symbol']})
            if MarketUtilities.is_flaggable(asset, period):
                return asset

    def follow_opp(self, asset, period):
        """
        While an opportunity exists on this asset, follow it closely
        :param asset: The asset and corresponding data
        :param period: The period to watch
        :return: Nothing
        """
        while True:
            time.sleep(1)
            if not MarketUtilities.is_flaggable(asset, period):
                print("No Longer an Opportunity, Drop Asset")
                self.notify.message_all("No Longer an Opportunity, Drop Asset: " + asset["symbol"])
                self.client.order_limit_sell()







