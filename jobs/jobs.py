import logging
from datetime import datetime, timedelta

from pytz import utc

from utils import cache
from utils import dataBases

mongoDataBase = dataBases.mongodb_client


def stats_sync(query=None, filter=None, action: str = None):
    from jobs.updater import sched

    if query and filter:
        if action is None:
            action = '$inc'

        mongoUpdate = mongoDataBase.update_field(database_name='tbot', collection_name='chats',
                                                 action=action, filter=filter, query=query)

        if mongoUpdate is None:
            date = datetime.now(tz=utc) + timedelta(minutes=15)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
            return sched.get_job('stats_sync').modify(next_run_time=date, args=[query, filter, action])
        else:
            return sched.get_job('stats_sync').modify(args=[])

    if not mongoDataBase.check_connection():
        return

    for chat_id in cache.stats.keys():
        # query = {}
        # filter = {'chat_id': chat_id}
        #
        # for user_id in cache.stats.get(chat_id, {}).get('members', {}).keys():
        #     if cache.stats.get(chat_id, {}).get('members', {}).get(user_id, {}).get('reactions_count', {}):
        #         for msg_id, reaction_count in cache.stats.get(chat_id, {}).get('members', {}).get(user_id, {}).pop('reactions_count').items():
        #             query[f'users.{user_id}.stats.reactions_count.{msg_id}'] = reaction_count
        #
        # if query:
        #     mongoUpdate = mongoDataBase.update_field(database_name='tbot', collection_name='chats',
        #                                              action='$set', filter=filter, query=query)
        #
        #     if mongoUpdate is None:
        #         date = datetime.now(tz=utc) + timedelta(minutes=15)
        #         date = date.strftime('%Y-%m-%d %H:%M:%S')
        #         sched.get_job('stats_sync').modify(next_run_time=date, args=[query, filter, '$set'])

        query = {'xp': 1}
        filter = {'chat_id': chat_id}
        document = mongoDataBase.get_document(database_name='tbot',
                                              collection_name='chats',
                                              filter=filter,
                                              query=query)

        chat_xp = document.get('xp', {})

        cache.stats[chat_id]['xp']['message_xp'] = chat_xp.get('message_xp', 100)
        cache.stats[chat_id]['xp']['voice_xp'] = chat_xp.get('voice_xp', 50)
        cache.stats[chat_id]['xp']['message_xp_delay'] = chat_xp.get('message_xp_delay', 60)
        cache.stats[chat_id]['xp']['messages_xp_limit'] = chat_xp.get('messages_xp_limit', 60)

        query = {}

        for user_id in cache.stats.get(chat_id, {}).get('members', {}).keys():
            try:
                voicetime = cache.stats.get(chat_id, {}).get('members', {}).get(user_id, {}).pop('voicetime')
            except KeyError:
                voicetime = 0

            if not voicetime == 0:
                query[f'users.{user_id}.stats.voicetime'] = voicetime

            try:
                messages_count = cache.stats.get(chat_id, {}).get('members', {}).get(user_id, {}).pop(
                    'messages_count')
            except KeyError:
                messages_count = 0

            if not messages_count == 0:
                query[f'users.{user_id}.stats.messages_count'] = messages_count

            try:
                messages_count_xp = cache.stats.get(chat_id, {}).get('members', {}).get(user_id, {}).pop(
                    'messages_count_xp')
            except KeyError:
                messages_count_xp = 0

            if not messages_count_xp == 0 or not voicetime == 0:
                message_xp = cache.stats.get(chat_id, {}).get('xp', {}).get('message_xp', 100)
                voice_xp = cache.stats.get(chat_id, {}).get('xp', {}).get('voice_xp', 50)

                xp = (messages_count_xp * message_xp) + ((voicetime // 60) * voice_xp)

                query[f'users.{user_id}.stats.xp'] = xp

            # del cache.stats[guild_id]['members'][member_id]['messages_count']

        mongoUpdate = mongoDataBase.update_field(database_name='tbot', collection_name='chats',
                                                      action='$inc', filter=filter, query=query)

        if mongoUpdate is None:
            date = datetime.now(tz=utc) + timedelta(minutes=15)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
            sched.get_job('stats_sync').modify(next_run_time=date, args=[query, filter])
