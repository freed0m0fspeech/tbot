from datetime import datetime, timedelta

from pytz import utc

from utils import cache
from utils import dataBases

mongoDataBase = dataBases.mongodb_client


def stats_sync(query=None, filter=None):
    from jobs.updater import sched

    if query and filter:
        mongoUpdate = mongoDataBase.update_field(database_name='tbot', collection_name='chats',
                                                 action='$inc', filter=filter, query=query)

        if mongoUpdate is None:
            date = datetime.now(tz=utc) + timedelta(minutes=15)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
            return sched.get_job('stats_sync').modify(date=date, args=[query, filter])
        else:
            return sched.get_job('stats_sync').modify(args=[])

    if not mongoDataBase.check_connection():
        return

    try:
        for chat_id in cache.stats.keys():
            query = {}
            filter = {'chat_id': chat_id}

            for user_id in cache.stats.get(chat_id, {}).get('members', {}).keys():
                try:
                    voicetime = cache.stats.get(chat_id, {}).get('members', {}).get(user_id, {}).pop('voicetime')
                except Exception as e:
                    voicetime = None

                if voicetime:
                    query[f'users.{user_id}.stats.voicetime'] = voicetime

                try:
                    messages_count = cache.stats.get(chat_id, {}).get('members', {}).get(user_id, {}).pop(
                        'messages_count')
                except Exception as e:
                    messages_count = None

                if messages_count:
                    query[f'users.{user_id}.stats.messages_count'] = messages_count

                # del cache.stats[guild_id]['members'][member_id]['messages_count']

            mongoUpdate = mongoDataBase.update_field(database_name='tbot', collection_name='chats',
                                                          action='$inc', filter=filter, query=query)

            if mongoUpdate is None:
                date = datetime.now(tz=utc) + timedelta(minutes=15)
                date = date.strftime('%Y-%m-%d %H:%M:%S')
                sched.get_job('stats_sync').modify(next_run_time=date, args=[query, filter])
    except Exception as e:
        print(e)
