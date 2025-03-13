import os

from collections import defaultdict
from dotenv import load_dotenv
from plugins.DataBase.mongo import (
    MongoDataBase
)

load_dotenv()


class DataBases():

    def __init__(self):
        self.mongodb_client = self.__get_mongodb_client()

    @staticmethod
    def __get_mongodb_client():
        MONGODATABASE_USER = os.getenv('MONGODATABASE_USER', '')
        MONGODATABASE_PASSWORD = os.getenv('MONGODATABASE_PASSWORD', '')
        MONGODATABASE_HOST = os.getenv('MONGODATABASE_HOST', '')

        # client
        return MongoDataBase(host=MONGODATABASE_HOST, user=MONGODATABASE_USER, passwd=MONGODATABASE_PASSWORD)


class Cache():
    def __init__(self, databases: DataBases):
        # Cached guilds
        # self.chats = {}
        #
        # query = {'_id': 0}
        # for chat in databases.mongodb_client.get_documents(database_name='tbot', collection_name='chats', query=query):
        #     self.chats[chat.get('chat_id', '')] = chat

        # count of defaultdict - count inner dicts
        self.stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))))

        query = {'_id': 0, 'xp': 1, 'chat_id': 1}
        for chat in databases.mongodb_client.get_documents(database_name='tbot', collection_name='chats', query=query):
            chat_xp = chat.get('xp', {})

            self.stats[chat.get('chat_id', '')]['xp']['message_xp'] = chat_xp.get('message_xp', 100)
            self.stats[chat.get('chat_id', '')]['xp']['voice_xp'] = chat_xp.get('voice_xp', 50)
            self.stats[chat.get('chat_id', '')]['xp']['message_xp_delay'] = chat_xp.get('message_xp_delay', 60)
            self.stats[chat.get('chat_id', '')]['xp']['message_xp_limit'] = chat_xp.get('message_xp_limit', 60)


dataBases = DataBases()
cache = Cache(dataBases)
# mongoDataBase = dataBases.mongodb_client