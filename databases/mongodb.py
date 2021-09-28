import json
import pymongo
from datetime import datetime
from sqlalchemy.ext.declarative import DeclarativeMeta

from dotenv import dotenv_values

config = dotenv_values(".env")

client = pymongo.MongoClient(config['MONGO_DB_URL'])
db = client[config['MONGO_DB_CLIENT']]
collection_currency = db[config['MONGO_DB_COLLECTION']]


class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            return fields

        return json.JSONEncoder.default(self, obj)


def store(tweet):
    if collection_currency.find_one({"i": tweet['i']}):
        return
    collection_currency.insert_one(json.loads(json.dumps(tweet, cls=AlchemyEncoder)))


def count_in_dates(query, since, until, dates, favorite_multiplier=None, retweets_multiplier=None):
    results = []
    len_dates = len(dates)
    for i in range(len_dates):
        results.append(None)
    for i in range(len_dates - 1):
        dt_init = datetime.combine(dates[i].date(), dates[i].time())
        dt_end = datetime.combine(dates[i + 1].date(), dates[i + 1].time())
        if favorite_multiplier:
            size = 0
            for item in collection_currency.find(
                    {"d": {"$gt": dt_init.timestamp(), "$lt": dt_end.timestamp()}, "q": get_query_id(query)}):
                size += item['f'] * favorite_multiplier + item['r'] * retweets_multiplier

            results[i] = size if size > 0 else None
        else:
            size = collection_currency.find(
                {"d": {"$gt": dt_init.timestamp(), "$lt": dt_end.timestamp()}, "q": get_query_id(query)}).count()
            results[i] = size if size > 0 else None
        print(i, 'of', len_dates, size)
    return results


def get_query_id(query):
    if query == "petrobras":
        return 0
    if query == "brumadinho":
        return 1
    if query == "renner":
        return 2