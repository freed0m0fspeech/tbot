import asyncio
import datetime
import gettext
import math
import os
import random
import pyrogram
import pytz
import speech_recognition
import time
# import youtube_dl
import yt_dlp
from datetime import timedelta

from pymongo import ReturnDocument
from pyrogram.enums import MessagesFilter, ParseMode, ChatType, ChatMemberStatus
from pyrogram.raw import types as raw_types
from pyrogram.raw.functions import phone
from pyrogram import types
from pyrogram.raw import base
from pyrogram.types import ChatPermissions
from plugins.Bots.PyrogramBot.bot import PyrogramBot
from pyrogram import errors, ContinuePropagation
from plugins.Helpers import youtube_dl, media_convertor
from pyrogram.client import Client
from plugins.DataBase.mongo import MongoDataBase
from plugins.Google.google import Google
from utils import cache


class PyrogramBotHandler:
    """
    Pyrogram Handler
    """

    def __init__(self, webSerber, pyrogramBot: PyrogramBot, mongoDataBase: MongoDataBase):
        self.webServer = webSerber
        self.pyrogramBot = pyrogramBot
        self.groupCall = pyrogramBot.groupCall
        self.mongoDataBase = mongoDataBase
        # Cached chats
        # self.chats = {}
        #
        # query = {'_id': 0, 'chat_id': 1, 'users': 1, 'media': 1, 'call_id': 1, 'xp': 1}
        # for chat in self.mongoDataBase.get_documents(database_name='dbot', collection_name='guilds', query=query):
        #     self.chats[chat.get('chat_id', '')] = chat

    #
    # Horoscope
    #

    async def horoscope_command(self, client: Client, message: types.Message):
        # TODO horoscope command
        return

    """
    Get horoscope data through site (https://ignio.com/r/export/utf/xml/daily/com.xml) [XML document]
    Return text of horoscope of horo_sign for current day in format: horo_sign: horoscope
    Return False if request failed

    async with aiohttp.ClientSession() as session:
        async with session.get('https://ignio.com/r/export/utf/xml/daily/com.xml') as response:
            if response.status == 200:
                string_xml = await response.text()
                horoscope = xml.etree.ElementTree.fromstring(string_xml)
                #  for sign in horoscope.findall('aries'):
                text = ''
                for sign in horoscope:
                    if sign.tag == 'date':
                        continue

                    if sign.tag == horo_sign:
                        # string = ''
                        for day in sign:
                            if day.tag == 'today':
                                # string += day.tag + ':' + day.text
                                return sign.tag + ': ' + day.text
            else:
                return False
    """

    async def language_command(self, client: Client, message: types.Message):
        chat_member = await self.pyrogramBot.bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

        if not chat_member.status == ChatMemberStatus.OWNER:
            # TODO print message
            return

        try:
            language_code = message.text.split(" ", maxsplit=1)[1]
        except IndexError:
            # language_code = message.from_user.language_code
            language_code = 'ru'

        language = self.webServer.languages.get(language_code)

        if language:
            language.install()

            query = {'language_code': language_code}

            return self.mongoDataBase.update_field(database_name='tbot', collection_name='init', action='$set',
                                                   query=query)

    # ------------------------------------------------------------------------------------------------------------------
    # Message ----------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    async def type_command(self, client: Client, msg: types.Message):
        try:
            orig_text = msg.text.split(" ", maxsplit=1)[1]
        except IndexError:
            return

        text = orig_text
        tbp = ""  # to be printed
        typing_symbol = "▒"

        msg = await self.pyrogramBot.user.send_message(msg.chat.id, text)

        while (tbp != orig_text):
            try:
                await msg.edit(tbp + typing_symbol)
                time.sleep(0.05)  # 50 ms

                tbp = tbp + text[0]
                text = text[1:]

                await msg.edit(tbp)
                time.sleep(0.05)

            except errors.FloodWait as e:
                time.sleep(e.x)

    async def mute_command(self, client: Client, message: types.Message):
        try:
            parameters = message.text.split(" ", maxsplit=2)
            username = parameters[1]
            duration = parameters[2]
        except IndexError:
            return

            # return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
            #                                                text="✖️{text}".format(
            #                                                    text=_("Enter correct duration in minutes"))
            #                                                )

        try:
            duration = int(duration)
        except ValueError:
            return

        if 0 < duration < 61:
            try:
                member = await self.pyrogramBot.bot.get_chat_member(chat_id=message.chat.id,
                                                                    user_id=message.from_user.id)
                user = await self.pyrogramBot.bot.get_users(user_ids=username)
            except (errors.ChatInvalid, errors.PeerIdInvalid, errors.UserInvalid, errors.UsernameInvalid):
                return

            if member.custom_title.lower() == 'судья':
                await self.pyrogramBot.bot.restrict_chat_member(chat_id=message.chat.id,
                                                                user_id=user.id,
                                                                permissions=ChatPermissions(),
                                                                until_date=datetime.datetime.now() + timedelta(
                                                                    minutes=duration))
                # user_mention = f"[@{username}](tg://user?id={username.id})"

                await message.delete()

                return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                               text="✔️{user} {was_muted_by} {by_user} {on} {duration}m".format(
                                                                   was_muted_by=_("was muted by"),
                                                                   on=_("on"),
                                                                   duration=duration,
                                                                   user=user.mention(f"@{user.username}"),
                                                                   by_user=message.from_user.mention(
                                                                       f"@{message.from_user.username}"))
                                                               )
            else:
                return
        else:
            return

            # return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
            #                                                text="✖️{text}".format(
            #                                                    text=_("Enter correct duration in minutes"))
            #                                                )

    # ------------------------------------------------------------------------------------------------------------------
    # Player -----------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    async def volume_command(self, client: Client, message: types.Message):
        volume = message.text.split(" ", maxsplit=1)[1]

        await self.groupCall.client.set_my_volume(volume=volume)
        print(f'Volume set to {volume}')

    async def pause_command(self, client: Client, message: types.Message):
        if not self.groupCall.client.is_connected:
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(
                                                               text=_("I am not in voice channel (/join)"))
                                                           )
        else:
            if self.groupCall.client.is_audio_running:
                if self.groupCall.client.is_audio_paused:
                    await self.groupCall.client.set_audio_pause(False, False)
                    return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                                   text="✔️{text}".format(text=_("Audio resumed"))
                                                                   )
                else:
                    await self.groupCall.client.set_audio_pause(True, False)
                    return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                                   text="✔️{text}".format(text=_("Audio paused"))
                                                                   )
            else:
                if self.groupCall.client.is_video_running:
                    if self.groupCall.client.is_video_paused:
                        await self.groupCall.client.set_video_pause(False, False)
                        return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                                       text="✔️{text}".format(text=_("Video resumed"))
                                                                       )
                    else:
                        await self.groupCall.client.set_video_pause(True, False)
                        return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                                       text="✔️{text}".format(text=_("Video paused"))
                                                                       )
                else:
                    return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                                   text="✖️{text}".format(
                                                                       text=_("Media is not playing"))
                                                                   )

    async def skip_command(self, client: Client, message: types.Message):
        if not self.groupCall.client.is_connected:
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(
                                                               text=_("I am not in voice channel (/join)"))
                                                           )

        if not self.groupCall.client.is_audio_running and not self.groupCall.client.is_video_running:
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(text=_("Media is not playing"))
                                                           )

        await self.groupCall.client.stop_media()
        return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                       text="✔️{text}".format(text=_("Media skip"))
                                                       )

    async def leave_command(self, client: Client, message: types.Message):
        if not self.groupCall.client.is_connected:
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(
                                                               text=_("I am not in voice channel (/join)"))
                                                           )

        await self.groupCall.client.leave()
        return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                       text="✔️{text}".format(text=_("Thank you for kicking me out"))
                                                       )

    async def queue_command(self, client: Client, message: types.Message):
        try:
            text = message.text.split(" ", maxsplit=1)[1]
            try:
                page = int(text)
            except Exception:
                # await message.reply_text('Wrong format of command. Use command /queue or /queue [page]')
                # print('not int in queue [number]')
                page = 1
        except IndexError:
            # blank command
            page = 1

        query = {'media.queue': 1}

        document = self.mongoDataBase.get_document(database_name='tbot',
                                                   collection_name='chats',
                                                   filter={'chat_id': message.chat.id},
                                                   query=query)

        try:
            document = document['media']['queue']
        except (IndexError, KeyError):
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(text=_("Media queue is empty"))
                                                           )

        queue_count = len(document)
        document_slice = document[(page - 1) * 10:page * 10 + 1]

        if not document_slice:
            page = 1
            document_slice = document[:11]

        texts = []
        user_ids = []

        for queue in document_slice:
            texts.append(queue.get('text'))
            user_ids.append(queue.get('user'))

        users_objects = await self.pyrogramBot.bot.get_users(user_ids)
        queries = []
        for i, (text, user_id) in enumerate(zip(texts, user_ids)):
            if i == 10:
                break

            for user_object in users_objects:
                if user_object.id == user_id:
                    user_mention = f"[@{user_object.username}](tg://user?id={user_object.id})"

                    # query = f"({i + 1 + (page - 1) * 10}) `{text}` {_('added by')} {user_mention}"
                    query = "({element}) `{text}` {added_by} {user_mention}".format(element=i + 1 + (page - 1) * 10,
                                                                                    text=text,
                                                                                    added_by=_("added  by"),
                                                                                    user_mention=user_mention)

                    queries.append(query)
                    break

        if queries:
            queries = '\n'.join(queries)
            # text_reply = f"{message.chat.title} {_('media queue')} ({queue_count}):\n\n{queries}"
            text_reply = "{chat_title} {media_queue} ({queue_count}):\n\n{queries}".format(
                chat_title=message.chat.title,
                media_queue=_("media queue"),
                queue_count=queue_count,
                queries=queries)
        else:
            # empy page
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(text=_("Media queue is empty"))
                                                           )

        count_of_buttons = min(10, math.ceil(queue_count / 10))

        if count_of_buttons > 1:
            inlineKeyboardButtons = [types.InlineKeyboardButton(text=f"⏮", callback_data=f'/queue 1'),
                                     types.InlineKeyboardButton(text=f"◀", callback_data=f'/queue {page - 1}'),
                                     types.InlineKeyboardButton(text=f"▶", callback_data=f'/queue {page + 1}'),
                                     types.InlineKeyboardButton(text=f"⏭", callback_data=f'/queue {count_of_buttons}')]
            # for i in range(count_of_buttons):
            #    inlineKeyboardButtons.append(InlineKeyboardButton(text=f"{i+1}", callback_data=f'/queue {i+1}'))

            reply_markup = types.InlineKeyboardMarkup([inlineKeyboardButtons])
        else:
            reply_markup = None

        await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                text=text_reply,
                                                disable_notification=True,
                                                disable_web_page_preview=True,
                                                reply_markup=reply_markup)

    async def queue_callback_query(self, client: Client, callback_query: types.CallbackQuery):
        try:
            text = callback_query.data.split(" ", maxsplit=1)[1]
            try:
                page = int(text)
            except Exception:
                # print('not int in queue [number]')
                page = 1
        except IndexError:
            # print('blank command')
            page = 1

        message = callback_query.message

        query = {'media.queue': 1}

        document = self.mongoDataBase.get_document(database_name='tbot',
                                                   collection_name='chats',
                                                   filter={'chat_id': message.chat.id},
                                                   query=query)

        try:
            document = document['media']['queue']
        except (IndexError, KeyError):
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(text=_("Media queue is empty"))
                                                           )

        queue_count = len(document)
        document_slice = document[(page - 1) * 10:page * 10 + 1]

        if not document_slice:
            page = 1
            document_slice = document[:11]

        texts = []
        user_ids = []

        for queue in document_slice:
            texts.append(queue.get('text'))
            user_ids.append(queue.get('user'))

        users_objects = await self.pyrogramBot.bot.get_users(user_ids)
        queries = []
        for i, (text, user_id) in enumerate(zip(texts, user_ids)):
            if i == 10:
                break

            for user_object in users_objects:
                if user_object.id == user_id:
                    user_mention = f"[@{user_object.username}](tg://user?id={user_object.id})"
                    # query = f"({i + 1 + (page - 1) * 10}) `{text}` {_('added by')} {user_mention}"
                    query = "({element}) `{text}` {added_by} {user_mention}".format(element=i + 1 + (page - 1) * 10,
                                                                                    text=text,
                                                                                    added_by=_("added  by"),
                                                                                    user_mention=user_mention)
                    queries.append(query)
                    break

        if queries:
            queries = '\n'.join(queries)
            # text_reply = f"{message.chat.title} {_('media queue')} ({queue_count}):\n\n{queries}"
            text_reply = "{chat_title} {media_queue} ({queue_count}):\n\n{queries}".format(
                chat_title=message.chat.title,
                media_queue=_("media queue"),
                queue_count=queue_count,
                queries=queries)
        else:
            # text_reply = f"{message.chat.title} {_('media queue')} ({queue_count}):\n\n{_('Empty page')}"
            text_reply = "{chat_title} {media_queue} ({queue_count}):\n\n{queries}".format(
                chat_title=message.chat.title,
                media_queue=_("media queue"),
                queue_count=queue_count,
                queries=_("Empty page"))

        count_of_buttons = min(10, math.ceil(queue_count / 10))

        if count_of_buttons > 1:
            inlineKeyboardButtons = [types.InlineKeyboardButton(text=f"⏮", callback_data=f'/queue 1'),
                                     types.InlineKeyboardButton(text=f"◀", callback_data=f'/queue {page - 1}'),
                                     types.InlineKeyboardButton(text=f"▶", callback_data=f'/queue {page + 1}'),
                                     types.InlineKeyboardButton(text=f"⏭", callback_data=f'/queue {count_of_buttons}')]
            # for i in range(count_of_buttons):
            #    inlineKeyboardButtons.append(InlineKeyboardButton(text=f"{i+1}", callback_data=f'/queue {i+1}'))

            reply_markup = types.InlineKeyboardMarkup([inlineKeyboardButtons])
        else:
            reply_markup = None

        try:
            await self.pyrogramBot.bot.edit_message_text(chat_id=message.chat.id,
                                                         message_id=message.message_id,
                                                         text=text_reply,
                                                         disable_web_page_preview=True,
                                                         reply_markup=reply_markup)
        except errors.MessageNotModified:
            # print('Same page')
            await callback_query.answer()

        # try:
        #    callback_query.answer('button', show_alert=True)
        # except (IndexError, KeyError):
        #    callback_query.answer(f"callback_query.answer Error", show_alert=True)

    async def now_command(self, client: Client, message: types.Message):
        if not self.groupCall.client.is_audio_running and not self.groupCall.client.is_video_running:
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(text=_("Media is not playing"))
                                                           )

        query = {'media.now': 1}
        document = self.mongoDataBase.get_document(database_name='tbot',
                                                   collection_name='chats',
                                                   filter={'chat_id': message.chat.id},
                                                   query=query)

        try:
            document = document['media']['now']
        except (IndexError, KeyError):
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(text=_("Media is not playing"))
                                                           )

        now = {
            'title': document.get('title'),
            'url': document.get('url'),
            'webpage_url': document.get('webpage_url'),
            'channel_url': document.get('channel_url'),
            'thumbnail': document.get('thumbnail'),
            'uploader': document.get('uploader'),
            'uploader_url': document.get('uploader_url'),
            # 'thumbnail': document.get('thumbnail'),
            'channel': document.get('channel'),
            'duration': document.get('duration'),
            'protocol': document.get('protocol'),
            'user': document.get('user')
        }

        user = await self.pyrogramBot.bot.get_users(now['user'])
        duration = f"({timedelta(seconds=int(now['duration']))})"
        title = f"[{now['title']}]({now['webpage_url']})"
        channel = f"[{now['uploader']}]({now['uploader_url']})"
        user_mention = f"[@{user.username}](tg://user?id={now['user']})"

        # text_reply = f"{_('Now playing')}\n" \
        #             f"{_('Title')}: {title}\n" \
        #             f"{_('Uploader')}: {channel}\n" \
        #             f"{_('Duration')}: {duration}\n" \
        #             f"{_('Added by')}{user_mention}\n"

        text_reply = "{now_playing_text}\n" \
                     "{title_text}: {title}\n" \
                     "{uploader_text}: {uploader}\n" \
                     "{duration_text}: {duration}\n" \
                     "{added_by_text}: {user_mention}\n".format(now_playing_text=_("Now playing"),
                                                                title_text=_('Title'),
                                                                title=title,
                                                                uploader_text=_('Uploader'),
                                                                uploader=channel,
                                                                duration_text=_('Duration'),
                                                                duration=duration,
                                                                added_by_text=_('Added by'),
                                                                user_mention=user_mention)

        try:
            await self.pyrogramBot.bot.send_photo(chat_id=message.chat.id,
                                                  photo=now['thumbnail'],
                                                  caption=text_reply,
                                                  disable_notification=True)
        except errors.WebpageMediaEmpty:
            await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                    text=text_reply,
                                                    disable_notification=True,
                                                    disable_web_page_preview=True)
            # print('not supported image for send_photo')
            # print(now['thumbnail'])

    async def lyrics_command(self, client: Client, message: types.Message):
        try:
            text = message.text.split(" ", maxsplit=1)[1]
        except IndexError:
            # print('blank command')
            text = ''

        if text:
            # FIXME check if it returns error
            lyrics = self.webServer.google.lyrics(song_name=text)
        else:
            if not self.groupCall.client.is_audio_running and not self.groupCall.client.is_video_running:
                return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                               text="✖️{text}\n{tip}".format(
                                                                   text=_("Media is not playing"),
                                                                   tip=_("Use /lyrics [song title] instead"))
                                                               )

            query = {'media.now': 1}
            document = self.mongoDataBase.get_document(database_name='tbot',
                                                       collection_name='chats',
                                                       filter={'chat_id': message.chat.id},
                                                       query=query)

            try:
                document = document['media']['now']
            except (IndexError, KeyError):
                return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                               text="✖️{text}".format(text=_("Media is not playing"))
                                                               )

            now = {
                'title': document.get('title'),
                'url': document.get('url'),
                'webpage_url': document.get('webpage_url'),
                'channel_url': document.get('channel_url'),
                'thumbnail': document.get('thumbnail'),
                'uploader': document.get('uploader'),
                'uploader_url': document.get('uploader_url'),
                # 'thumbnail': document.get('thumbnail'),
                'channel': document.get('channel'),
                'duration': document.get('duration'),
                'protocol': document.get('protocol'),
                'user': document.get('user')
            }
            lyrics = self.webServer.google.lyrics(song_name=now['title'])

        if not lyrics:
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(text=_("Lyrics not found"))
                                                           )

        text_reply = f"[{lyrics['title']}]({lyrics['link']}):\n{lyrics['lyrics']}"

        await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                text=text_reply,
                                                disable_notification=True,
                                                disable_web_page_preview=True)

    async def clear_command(self, client: Client, message: types.Message):
        try:
            text = message.text.split(" ", maxsplit=1)[1]
            try:
                count = int(text)
            except Exception:

                return
        except IndexError:
            # print('blank command')
            count = 0

        if count == 0:
            query = {'media.queue': -1}
            if self.mongoDataBase.update_field(database_name='tbot',
                                               collection_name='chats',
                                               action='$unset',
                                               filter={'chat_id': message.chat.id},
                                               query=query) is None:
                print('Something wrong with DataBase')

            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✔️{text}".format(text=_("Media queue cleared"))
                                                           )
        else:
            # a value of -1 to remove the first element of an array and 1 to remove the last element in an array.
            query = {'media.queue': int(-1 * math.copysign(1, count))}
            for i in range(abs(count)):
                if self.mongoDataBase.update_field(database_name='tbot',
                                                   collection_name='chats',
                                                   action='$pop',
                                                   filter={'chat_id': message.chat.id},
                                                   query=query) is None:
                    print('Something wrong with DataBase')

            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✔️{count} {tracks_cleared}".format(count=abs(count),
                                                                                                    tracks_cleared=_(
                                                                                                        "track(s) cleared"))
                                                           )

    async def join_command(self, client: Client, message: types.Message):
        if not self.groupCall.client.is_connected:
            try:
                await self.groupCall.client.join(group=int(message.chat.id))  # , join_as=-1001571685575)
            except Exception:
                peer = await self.pyrogramBot.user.resolve_peer(message.chat.id)
                startGroupCall = phone.CreateGroupCall(peer=raw_types.InputPeerChannel(channel_id=peer.channel_id,
                                                                                       access_hash=peer.access_hash),
                                                       random_id=int(self.pyrogramBot.bot.rnd_id()) // 9000000000)
                try:
                    await self.pyrogramBot.user.invoke(startGroupCall)
                    await self.groupCall.client.join(group=message.chat.id)
                except errors.ChatAdminRequired:
                    await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                            text="✖️{text}".format(
                                                                text=_("I need manage voice permission"))
                                                            )

                    return False

            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✔️{text}".format(
                                                               text=_("Successfully connected to voice channel"))
                                                           )
        else:
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(
                                                               text=_("I am already in voice channel"))
                                                           )

    async def play_command(self, client: Client, message: types.Message):
        # TODO autoconnect
        # print(message.chat.id)

        # print(self.groupCall.client.is_audio_running, self.groupCall.client.is_video_running)
        # print(self.groupCall.client.is_audio_paused, self.groupCall.client.is_video_paused)

        try:
            text = message.text.split(" ", maxsplit=1)[1]
            query = {'media.queue': {'text': text, 'user': message.from_user.id}}

            if self.mongoDataBase.update_field(database_name='tbot', collection_name='chats', action='$push',
                                               filter={'chat_id': message.chat.id}, query=query) is None:
                print('Something wrong with DataBase')

            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✔️{text}".format(text=_("Successfully added to queue"))
                                                           )
        except IndexError:
            # print('blank command')
            pass

        if self.groupCall.client.is_audio_running or self.groupCall.client.is_video_running:
            # return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
            #                                               text="✖️Media currently playing")
            return

        if not self.groupCall.client.is_connected:
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(
                                                               text=_("I need to be in voice channel (/join)"))
                                                           )
            # await self.join_command(client=client, message=message)

        while True:
            while self.groupCall.client.is_audio_running or self.groupCall.client.is_video_running:
                await asyncio.sleep(1)
            else:
                if not self.groupCall.client.is_connected:
                    return

                query = {'media.queue': -1}
                document = self.mongoDataBase.update_field(database_name='tbot', collection_name='chats',
                                                           action='$pop', filter={'chat_id': message.chat.id},
                                                           query=query, return_document=ReturnDocument.BEFORE)

                if not document:
                    return

                try:
                    # print(document)
                    text = document['media']['queue'][0]['text']
                    user = document['media']['queue'][0]['user']
                except (IndexError, KeyError):
                    query = {'media.now': 1}
                    if self.mongoDataBase.update_field(database_name='tbot', collection_name='chats', action='$unset',
                                                       filter={'chat_id': message.chat.id}, query=query) is None:
                        print('Something wrong with DataBase')
                    return

                # queue = document['media']['queue']

                search_engine = None
                lip_sync = False

                ydl_opts = {
                    'format': 'bestaudio/best[height<=?720][width<=?1280]',
                    'quiet': True,
                    'ignoreerrors': True,
                    'noplaylist': True,
                }

                if '@video@' in text:
                    text = text.replace('@video@', '', 1)
                    if '@sync@' in text:
                        text = text.replace('@sync@', '', 1)
                        lip_sync = True
                    ydl_opts['format'] = 'best'

                if '@yt@' in text:
                    text = text.replace('@yt@', '', 1)
                    search_engine = 'ytsearch'
                else:
                    if '@sc@' in text:
                        text = text.replace('@sc@', '', 1)
                        search_engine = 'scsearch'

                text = text.strip()

                info = youtube_dl.get_best_info_media(title=text, ydl_opts=ydl_opts, search_engine=search_engine)

                if not info:
                    return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                                   text="✖️{text}".format(text=_("Media load failed"))
                                                                   )
                # print(info)
                # 'userID': data['userID'],

                if isinstance(info, list):
                    # print(len(info))
                    # print(info)
                    info = info[0]

                # print(info)

                filter = {'chat_id': message.chat.id}

                now = {
                    'title': info.get('title'),
                    'url': info.get('url'),
                    'webpage_url': info.get('webpage_url'),
                    'channel_url': info.get('channel_url'),
                    'uploader': info.get('uploader'),
                    'uploader_url': info.get('uploader_url'),
                    'thumbnail': info.get('thumbnail'),
                    # 'thumbnail': document['thumbnails'][len(document.get('thumbnails'))],
                    'channel': info.get('channel'),
                    'duration': info.get('duration'),
                    'protocol': info.get('protocol'),
                    'user': user
                }

                query = {'media.now': {'title': now['title'],
                                       'url': now['url'],
                                       'webpage_url': now['webpage_url'],
                                       'channel_url': now['channel_url'],
                                       'uploader': info.get('uploader'),
                                       'uploader_url': info.get('uploader_url'),
                                       'thumbnail': now['thumbnail'],
                                       'channel': now['channel'],
                                       'duration': now['duration'],
                                       'user': now['user']}}

                if self.mongoDataBase.update_field(database_name='tbot', collection_name='chats', action='$set',
                                                   filter=filter, query=query) is None:
                    print('Something wrong with DataBase')

                # print('start playing')
                if info.get('ext') in self.groupCall.audio_formats:
                    try:
                        await self.groupCall.client.start_audio(source=info['url'], repeat=False)
                    except Exception:
                        return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                                       text="✖️{text}".format(
                                                                           text=_("Audio playout failed"))
                                                                       )
                else:
                    if info.get('ext') in self.groupCall.video_formats:
                        try:
                            await self.groupCall.client.start_video(source=info['url'], repeat=False,
                                                                    enable_experimental_lip_sync=lip_sync)
                        except Exception:
                            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                                           text="✖️{text}".format(
                                                                               text=_("Video playout failed"))
                                                                           )
                    else:
                        return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                                       text="✖️{text}".format(
                                                                           text=_("Media playout failed"))
                                                                       )

                user = await self.pyrogramBot.bot.get_users(now['user'])

                duration = f"({timedelta(seconds=int(now['duration']))})"

                title = f"[{now['title']}]({now['webpage_url']})"
                channel = f"[{now['uploader']}]({now['uploader_url']})"
                user_mention = f"[@{user.username}](tg://user?id={now['user']})"

                # text_reply = f"{_('Playing from queue')}\n" \
                #             f"{_('Title')}: {title}\n" \
                #             f"{_('Uploader')}: {channel}\n" \
                #             f"{_('Duration')}: {duration}\n" \
                #             f"{_('Added by')} {user_mention}\n"

                text_reply = "{playing_text}\n" \
                             "{title_text}: {title}\n" \
                             "{uploader_text}: {uploader}\n" \
                             "{duration_text}: {duration}\n" \
                             "{added_by_text}: {user_mention}\n".format(playing_text=_("Playing from queue"),
                                                                        title_text=_('Title'),
                                                                        title=title,
                                                                        uploader_text=_('Uploader'),
                                                                        uploader=channel,
                                                                        duration_text=_('Duration'),
                                                                        duration=duration,
                                                                        added_by_text=_('Added by'),
                                                                        user_mention=user_mention)

                try:
                    await self.pyrogramBot.bot.send_photo(chat_id=message.chat.id, photo=now['thumbnail'],
                                                          caption=text_reply, disable_notification=True)
                except errors.WebpageMediaEmpty:
                    # print('not supported image for send_photo')
                    # print(now['thumbnail'])
                    await self.pyrogramBot.bot.send_message(chat_id=message.chat.id, text=text_reply,
                                                            disable_notification=True, disable_web_page_preview=True)
                # reply_markup=reply_markup)

    async def answer_inline_result(self, client: Client, chosen_inline_result: types.ChosenInlineResult):
        # chosen_inline_result.result_id
        # inlineQueryResultArticle = InlineQueryResultArticle()
        # print(chosen_inline_result)
        print('choosen_inline_result')
        # result = self.pyrogramBot.user.get_inline_bot_results(bot='@F0S_bot', query=chosen_inline_result.query)
        # print(result)

    async def play_inline_query(self, client: Client, inline_query: types.InlineQuery):
        # query_message = inline_query.query
        # from_user = inline_query.from_user
        # print(query_message)

        try:
            text = inline_query.query.split(" ", maxsplit=1)[1]
            # text = inline_query.query
        except IndexError:
            return

        try:
            ydl_opts = {
                'skip_download': True,
                'quiet': True,
                'ignoreerrors': True,
                'noplaylist': True,
            }
            search_engine = None
            video = ''
            sync = ''

            if '@video@' in text:
                text = text.replace('@video@', '', 1)
                video = '@video@'
                if '@sync@' in text:
                    text = text.replace('@sync@', '', 1)
                    sync = '@sync@'

            if '@yt@' in text:
                text = text.replace('@yt@', '', 1)
                search_engine = 'ytsearch'
            else:
                if '@sc@' in text:
                    text = text.replace('@sc@', '', 1)
                    search_engine = 'scsearch'

            text = text.strip()

            info = youtube_dl.get_info_media(title=text,
                                             ydl_opts=ydl_opts,
                                             search_engine=search_engine,
                                             result_count=1)

            results = []

            if not isinstance(info, list):
                info = [info]

            for result in info:
                if not result:
                    # print('AttributeError, no results')
                    return

                res = {
                    'title': result.get('title'),
                    'webpage_url': result.get('webpage_url'),
                    'thumbnail': result.get('thumbnail'),
                    'channel': result.get('channel'),
                    'uploader': result.get('uploader'),
                    'duration': result.get('duration'),
                    'protocol': result.get('protocol')
                }

                message_text = f"/play {res['webpage_url']} {video} {sync}"
                # print(f"{input_message_content}")
                duration = f"({timedelta(seconds=int(res['duration']))})"
                # print(res)
                results.append(types.InlineQueryResultArticle(
                    title=f"{duration} {res['title']}",
                    input_message_content=types.InputTextMessageContent(message_text=message_text,
                                                                        parse_mode=ParseMode.MARKDOWN,
                                                                        disable_web_page_preview=True),
                    url=res['webpage_url'],
                    description=res['uploader'],
                    thumb_url=res['thumbnail']
                    # reply_markup=InlineKeyboardMarkup([
                    #    [InlineKeyboardButton(text="Add to queue", callback_data=f'/callback')]
                    # ])
                ))

            # 604800 - 7 days, 21600, 21600 - 6 hours
            return await inline_query.answer(results=results, cache_time=21600)
        except errors.QueryIdInvalid:
            # print(exceptions.QueryIdInvalid)
            return

    async def start_command(self, client: Client, message: types.Message):
        await message.reply('Start message')

    async def help_command(self, client: Client, message: types.Message):
        await message.reply('Help message')

    async def echo_command(self, client: Client, message: types.Message):
        try:
            await message.reply(text=message.text.split(" ", maxsplit=1)[1])
        except IndexError:
            return

    # ------------------------------------------------------------------------------------------------------------------
    # SPEECH RECOGNITION -----------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    async def speech_to_text_command(self, client: Client, message: types.Message):
        try:
            language = message.text.split(" ", maxsplit=1)[1]
        except IndexError:
            language = 'ru-RU'

        if not message.reply_to_message or not message.reply_to_message.voice:
            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text="✖️{text}".format(
                                                               text=_("Message does not contain voice message"))
                                                           )

        file_id = message.reply_to_message.voice.file_id
        source = await self.pyrogramBot.bot.download_media(message=file_id, file_name='downloads/')
        converted_source = media_convertor.convert_audio_file(source)
        os.remove(source)
        recognizer = speech_recognition.Recognizer()
        text = ''

        if message.reply_to_message.voice.duration < 60:
            audio_file = speech_recognition.AudioFile(converted_source)

            with audio_file as source:
                audio_data = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio_data=audio_data, language=language)
            except (speech_recognition.UnknownValueError,
                    speech_recognition.RequestError,
                    speech_recognition.WaitTimeoutError):
                await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                        text="✖️{text}".format(text=_("Speech Recognition Error"))
                                                        )
        else:
            # TODO long file recognition
            text = 'Long voice audio recognition not yet supported.' \
                   'You can only use < 60 sec voice audio recognition'
            """
            audio_segment = AudioSegment.from_wav(file=converted_source)
            chunks = split_on_silence(audio_segment=audio_segment, min_silence_len=1000, silence_thresh=-16)

            i = 0
            # process each chunk
            for chunk in chunks:
                # Create 0.5 seconds silence chunk
                chunk_silent = AudioSegment.silent(duration=10)

                # add 0.5 sec silence to beginning and
                # end of audio chunk. This is done so that
                # it doesn't seem abruptly sliced.
                audio_chunk = chunk_silent + chunk + chunk_silent

                # specify the bitrate to be 192 k
                audio_chunk.export("downloads/chunk{0}.wav".format(i), bitrate='192k', format="wav")

                # the name of the newly created chunk
                filename = 'downloads/chunk' + str(i) + '.wav'

                print("Processing chunk " + str(i))

                # get the name of the newly created chunk
                # in the AUDIO_FILE variable for later use.
                file = filename

                # recognize the chunk
                with speech_recognition.AudioFile(file) as src:
                    # remove this if it is not working
                    # correctly.
                    recognizer.adjust_for_ambient_noise(src)
                    audio_listened = recognizer.listen(src)

                try:
                    # try converting it to text
                    chunk_text = recognizer.recognize_google(audio_data=audio_listened, language=language)
                    print(chunk_text)
                    text = text + chunk_text
                except (speech_recognition.UnknownValueError,
                        speech_recognition.RequestError,
                        speech_recognition.WaitTimeoutError):
                    print('speech_recognition.Error')

                i += 1
            """

        os.remove(converted_source)

        if text:
            if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
                link = message.reply_to_message.link

                await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                        text=f"[{text}]({link})")
            else:
                await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                        text=f"{text}")

        # https://cloud.google.com/speech-to-text/docs/languages
        # recognize_bing()
        # recognize_google()
        # recognize_google_cloud()
        # recognize_ibm()
        # recognize_sphinx()

    #
    # XP check
    #

    async def stats_command(self, client: Client, message: types.Message):
        # TODO add addition info and parameters

        chat = message.chat
        try:
            query = message.text.split(" ", maxsplit=1)[1]

            if query == 'random':
                max_value = await self.pyrogramBot.user.search_messages_count(chat_id=chat.id)

                # random_value = random.random()
                # min_value + (random_value * (max_value - min_value))

                try:
                    # get history onlu for user bots
                    async for random_message in self.pyrogramBot.user.get_chat_history(chat_id=chat.id,
                                                                                       offset=random.randint(0,
                                                                                                             max_value),
                                                                                       limit=1):
                        random_message = random_message
                except ValueError:
                    return await self.pyrogramBot.bot.send_message(chat_id=chat.id,
                                                                   text="✖️{text} {chat_title}".format(
                                                                       text=_("No messages in"),
                                                                       chat_title=chat.title)
                                                                   )

                link = random_message.link
                return await self.pyrogramBot.bot.send_message(
                    chat_id=chat.id,
                    text="✔️{random_text} [{message_text}]({link})".format(random_text=_("Random"),
                                                                           message_text=_("message"),
                                                                           link=link)
                )
            else:
                user_name = query

            try:
                user = await self.pyrogramBot.bot.get_users(user_name)
            except (errors.UsernameInvalid, errors.PeerIdInvalid):
                return await self.pyrogramBot.bot.send_message(chat_id=chat.id,
                                                               text="✖️{text} {user_name}".format(
                                                                   text=_("No stats found about"),
                                                                   user_name=user_name),
                                                               disable_notification=True
                                                               )

            query = {'_id': 0, f'users': 1, 'xp': 1}
            document = self.mongoDataBase.get_document(database_name='tbot', collection_name='chats',
                                                       filter={'chat_id': chat.id}, query=query)

            if not document:
                print('Something wrong with DataBase')

            voicetime = document.get('users', {}).get(f'{user.id}', {}).get('stats', {}).get('voicetime', 0)

            # query = ""
            # query_filter = MessagesFilter.EMPTY

            # Search only for userbots
            # messages_count = await self.pyrogramBot.user.search_messages_count(chat_id=chat.id, from_user=user.id,
            #                                                                    query=query, filter=query_filter)
            messages_count = document.get('users', {}).get(f'{user.id}', {}).get('stats', {}).get('messages_count', 0)

            user_mention = f"[@{user.username}](tg://user?id={user.id})"
            # date = datetime.timedelta(seconds=seconds)
            hours_in_voice_channel = round(voicetime / 3600, 1)

            message_xp = document.get('xp', {}).get('message_xp', 100)
            voice_xp = document.get('xp', {}).get('voice_xp', 50)
            xp_factor = document.get('xp', {}).get('xp_factor', 100)  # threshold

            xp = (messages_count * message_xp) + ((voicetime // 60) * voice_xp)

            lvl = 0.5 + math.sqrt(1 + 8 * (xp) / (xp_factor)) / 2
            lvl = int(lvl) - 1

            xp_for_level = lvl / 2 * (2 * xp_factor + (lvl - 1) * xp_factor)

            xp_have = int(xp - xp_for_level)
            xp_need = (lvl + 1) * xp_factor

            return await self.pyrogramBot.bot.send_message(
                chat_id=chat.id,
                text="{user_mention} {lvl_text}: {lvl} {xp_text}: {xp}\n{messages_text}: {messages_count} | {voice_time_text}: {voice_time}h\n\n"
                     "{message_xp} {xp_per_messaage_text}\n{voice_xp} {xp_per_voice_second_text}".format(
                    user_mention=user_mention,
                    lvl_text=_("lvl"),
                    lvl=lvl,
                    xp_text=_("xp"),
                    xp=f"{xp_have} | {xp_need}",
                    messages_text=_("messages"),
                    messages_count=messages_count,
                    voice_time_text=_("voice time"),
                    voice_time=hours_in_voice_channel,
                    message_xp=message_xp,
                    xp_per_messaage_text=_("xp per message"),
                    voice_xp=voice_xp,
                    xp_per_voice_second_text=_("xp per voice minute")),
                disable_notification=True

                # text=f"{user_mention} {_('xp')}: {round(xp)} {_('messages')}: {messages_count} {_('voice time')}: {date}\n\n"
                #     f"({message_xp}{_('xp per message')} | {voice_xp} {_('xp per voice second')})"
            )
        except IndexError:
            query = {'_id': 0, f'users': 1, 'xp': 1}
            document = self.mongoDataBase.get_document(database_name='tbot', collection_name='chats',
                                                       filter={'chat_id': chat.id}, query=query)

            if not document:
                print('Something wrong with DataBase')

            message_xp = document.get('xp', {}).get('message_xp', 100)
            voice_xp = document.get('xp', {}).get('voice_xp', 50)
            xp_factor = document.get('xp', {}).get('xp_factor', 100)  # threshold

            # query = ""
            # query_filter = MessagesFilter.EMPTY

            stats = []
            async for member in self.pyrogramBot.user.get_chat_members(chat_id=chat.id):
                # messages_count = await self.pyrogramBot.user.search_messages_count(chat_id=chat.id,
                #                                                                    from_user=member.user.id,
                #                                                                    query=query, filter=query_filter)

                user = member.user

                messages_count = document.get('users', {}).get(f'{user.id}', {}).get('stats', {}).get('messages_count',
                                                                                                      0)
                voicetime = document.get('users', {}).get(f'{user.id}', {}).get('stats', {}).get('voicetime', 0)

                xp = (messages_count * message_xp) + ((voicetime // 60) * voice_xp)
                stat = (user, messages_count, voicetime, xp)
                stats.append(stat)

            # sort data by id=3 value - xp
            stats.sort(reverse=True, key=lambda x: x[3])

            # [0:10:2]  # start 0, stop: 10, step:2
            # [0:9]  # start 0, stop: 9, step:1
            # [9:]  # start 9, stop: end of string, step:1
            # [9::2]  # start 9, stop: end of string, step:2
            # [::2]  # start 0, stop: end of string, step:2

            # top 10 users
            top_list = "{top_members_text} {chat_title}\n\n".format(top_members_text=_("Top members of"),
                                                                    chat_title=chat.title)
            i = 0
            for user, messages_count, voicetime, xp in stats[0:10]:
                # date = datetime.timedelta(seconds=seconds)
                i += 1

                user_mention = f"[@{user.username}](tg://user?id={user.id})"

                hours_in_voice_channel = round(voicetime / 3600, 1)

                lvl = 0.5 + math.sqrt(1 + 8 * (xp) / (xp_factor)) / 2
                lvl = int(lvl) - 1

                xp_for_level = lvl / 2 * (2 * xp_factor + (lvl - 1) * xp_factor)

                xp_have = int(xp - xp_for_level)
                xp_need = (lvl + 1) * xp_factor

                top_list = "{top_list}{i}.{user_mention} {lvl_text}: {lvl} {xp_text}: {xp}\n{messages_text}: {messages_count} | {voice_time_text}: {voice_time}h\n".format(
                    top_list=top_list,
                    i=i,
                    user_mention=user_mention,
                    lvl_text=_("lvl"),
                    lvl=lvl,
                    xp_text=_("xp"),
                    xp=f"{xp_have} | {xp_need}",
                    messages_text=_("messages"),
                    messages_count=messages_count,
                    voice_time_text=_("voice time"),
                    voice_time=hours_in_voice_channel)

                # top_list = f"{top_list}{i}.{user_mention} {_('xp')}: {round(xp)} {_('messages')}: {messages_count} {_('voice time')}: {date}\n"

            top_list = "{top_list}\n\n{message_xp} {xp_per_messaage_text}\n{voice_xp} {xp_per_voice_second_text}".format(
                top_list=top_list,
                message_xp=message_xp,
                xp_per_messaage_text=_("xp per message"),
                voice_xp=voice_xp,
                xp_per_voice_second_text=_("xp per voice minute"))
            # top_list = f"{top_list}\n\n({message_xp}{_('xp per message')} | {voice_xp} {_('xp per voice second')})"

            return await self.pyrogramBot.bot.send_message(chat_id=chat.id, text=top_list, disable_notification=True)

        # query = ""
        # query_filter = "empty"

        # Search only for userbots
        # messages_count = await self.pyrogramBot.user.search_messages_count(chat_id=chat.id, from_user=user.id,
        #                                                                   query=query, filter=query_filter)

        # stat = (user.username, messages_count)
        # print(user.username, messages_count)

        # return

        # print(messages_count)
        """
        query = {'_id': 0, f'users.{user.id}.messages_count': 1, f'users.{user.id}.voice_time': 1}
        document = self.mongoDataBase.get_document(database_name='tbot', collection_name='chats',
                                                filter={'chat_id': message.chat.id}, query=query)

        try:
            info = document['users'][f'{user.id}']
        except(IndexError, KeyError, TypeError):
            user_mention = f"[@{user.username}](tg://user?id={user.id})"

            return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                           text=f"✖️No stats found about {user_mention}")

        user_mention = f"[@{user.username}](tg://user?id={user.id})"

        return await self.pyrogramBot.bot.send_message(chat_id=message.chat.id,
                                                       text=f"{user_mention} stats:\n"
                                                            f"Messages: {info.get('messages_count')}\n"
                                                            f"Voice time: {info.get('voice_time')} minutes")
        """

    # ------------------------------------------------------------------------------------------------------------------
    # RAW UPDATE HANDLER -----------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    async def raw_update_handler(self, client: Client, update: base.Update, users: dict, chats: dict):
        """
        Raw Updates Handler

        # MIN_CHANNEL_ID = -1002147483647
        # MAX_CHANNEL_ID = -1000000000000
        # MIN_CHAT_ID = -2147483647
        # MAX_USER_ID_OLD = 2147483647
        # MAX_USER_ID = 999999999999

        # MAX - ID = NEW ID
        """

        # (client.get_chat_member(userid)).status - member admin permissions

        # APRIL FOOLS --------------------------------------------------------------------------------------------------
        """
        if isinstance(update, raw_types.UpdateNewChannelMessage):
            update: raw_types.UpdateNewChannelMessage
            # self.pyrogramBot.bot: pyrogram.Client

            # chat = list(chats.items())[0][1]
            # chat_id = -1000000000000 - chat.id
            # user = list(users.items())[0][1]

            if random.randint(1, 4) == 1:
                # print(1)
                chat_id = -1000000000000 - update.message.peer_id.channel_id
                message_id = update.message.id
                emoji = "🎉🔥🤮🤯👍👎💩🤩😱😁🤬😢🥰👏❤🤔"
                # "️"
                # print(message_id, chat_id, update)

                # print(message_id, chat_id, update)

                while True:
                    try:
                        if await self.pyrogramBot.user.send_reaction(chat_id=chat_id, message_id=message_id, emoji=random.choice(emoji)):
                            return
                    except errors.FloodWait as e:
                        await asyncio.sleep(e.x)
                    except Exception as e:
                        return print(e)

        # chat_member = await self.pyrogramBot.bot.get_chat_member(chat_id=chat_id, user_id='me')
        """
        # --------------------------------------------------------------------------------------------------------------

        # TODO add handle of another update types

        # New message in channel
        if isinstance(update, raw_types.update_new_channel_message.UpdateNewChannelMessage):
            update: raw_types.update_new_channel_message.UpdateNewChannelMessage

            user = list(users.items())[0][1]
            chat = list(chats.items())[0][1]

            # query = {f'users.{user.id}.stats.messages_count': 1}
            #
            # if self.mongoDataBase.update_field(database_name='tbot', collection_name='chats', action='$inc',
            #                                        filter={'chat_id': -1000000000000 - chat.id},
            #                                        query=query) is None:
            #     print('Something wrong with DataBase. Messages count not increased')

            last_message = cache.stats[-1000000000000 - chat.id]['members'][user.id]['last_message']
            last_message_seconds = None
            if last_message:
                last_message_seconds = (
                            datetime.datetime.now(tz=pytz.utc).replace(tzinfo=None) - datetime.datetime.strptime(
                        last_message, '%Y-%m-%d %H:%M:%S')).total_seconds()

            messages_count = 1
            messages_count += cache.stats.get(-1000000000000 - chat.id, {}).get('members', {}).get(user.id, {}).get(
                'messages_count', 0)

            cache.stats[-1000000000000 - chat.id]['members'][user.id]['messages_count'] = messages_count
            message_xp_delay = cache.stats.get(-1000000000000 - chat.id, {}).get('xp', {}).get('message_xp_delay', 60)

            # Count messages only every 60 seconds
            if not last_message_seconds or last_message_seconds > message_xp_delay:
                date = datetime.datetime.now(tz=pytz.utc)
                date = date.strftime('%Y-%m-%d %H:%M:%S')

                messages_count_xp = 1
                messages_count_xp += cache.stats.get(-1000000000000 - chat.id, {}).get('members', {}).get(user.id, {}).get(
                    'messages_count_xp', 0)

                cache.stats[-1000000000000 - chat.id]['members'][user.id]['messages_count_xp'] = messages_count_xp
                cache.stats[-1000000000000 - chat.id]['members'][user.id]['last_message'] = date

            # execute another commands
            # raise StopPropagation

        if isinstance(update, raw_types.update_group_call.UpdateGroupCall):
            update: raw_types.update_group_call.UpdateGroupCall

            # chat = list(chats.items())[0][1]
            # chat_member = await self.pyrogramBot.bot.get_chat_member(chat_id=-1000000000000 - chat.id, user_id='me')

            # if chat_member.status != 'administrator':
            #    raise ContinuePropagation

            try:
                # New created group call
                version = update.call.version

                if version == 1:
                    query = {f'call_id': update.call.id}

                    return self.mongoDataBase.update_field(database_name='tbot', collection_name='chats', action='$set',
                                                           filter={'chat_id': -1000000000000 - update.chat_id},
                                                           query=query)
            except AttributeError:
                # Group call ended
                query = {f'call_id': 1}

                return self.mongoDataBase.update_field(database_name='tbot', collection_name='chats',
                                                       action='$unset',
                                                       filter={'chat_id': -1000000000000 - update.chat_id},
                                                       query=query)

                # query = {f'call_id': update.call.id}
                # return self.mongoDataBase.update_field(database_name='tbot', collection_name='chats',
                #                                       action='$setOnInsert', filter={'chat_id': update.chat_id},
                #                                       query=query)

        if isinstance(update, raw_types.update_group_call_participants.UpdateGroupCallParticipants):
            update: raw_types.update_group_call_participants.UpdateGroupCallParticipants

            for participant in update.participants:
                participant: raw_types.GroupCallParticipant
                if participant.left:
                    # User leaves group call
                    voicetime = time.time() - participant.date

                    user = list(users.items())[0][1]
                    # chat = list(chats.items())[0][1]

                    # getGroupCall = phone.GetGroupCall(call=update.call, limit=1)
                    # groupCall = await self.pyrogramBot.user.send(getGroupCall)
                    # groupCall: raw_types.GroupCall
                    # print(groupCall)
                    # chat = await self.pyrogramBot.bot.get_chat(chat_id=groupCall.title)

                    # query = {f'users.{user.id}.stats.voicetime': voicetime}
                    #
                    # return self.mongoDataBase.update_field(database_name='tbot', collection_name='chats',
                    #                                        action='$inc', filter={'call_id': update.call.id},
                    #                                        query=query)

                    tbot_document = self.mongoDataBase.get_document(database_name='tbot', collection_name='chats',
                                                                    filter={'call_id': update.call.id},
                                                                    query={'_id': 0, 'chat_id': 1})
                    chat_id = tbot_document.get('chat_id', '')

                    if chat_id:
                        voicetime += cache.stats.get(chat_id, {}).get('members', {}).get(user.id, {}).get('voicetime',
                                                                                                          0)
                        cache.stats[chat_id]['members'][user.id]['voicetime'] = voicetime

        raise ContinuePropagation

        """
        try:
            # UpdateNewChannelMessage
            if isinstance(update, raw_types.update_new_channel_message.UpdateNewChannelMessage):
                update: raw_types.update_new_channel_message.UpdateNewChannelMessage

                message = update.message
                if isinstance(message, raw_types.Message):
                    message: raw_types.Message

                    user = list(users.items())[0][1]
                    channel = list(chats.items())[0][1]
                    # chats[id_of_chat]

                    if isinstance(user, raw_types.User):
                        user: raw_types.User
                    else:
                        raise ContinuePropagation

                    if isinstance(channel, raw_types.Channel):
                        channel: raw_types.Channel
                    else:
                        raise ContinuePropagation
                else:
                    # FIXME
                    raise ContinuePropagation

                '''
                for user_id, user in users.items():
                    if isinstance(user, raw_types.User):
                        user: raw_types.User
    
                for chat_id, chat in chats.items():
                    if isinstance(chat, raw_types.Channel):
                        chat: raw_types.Channel
                '''
                query = {f'users.{user.id}.messages_count': 1, f'users.{user.id}.voice_time': 0}

                channel_id = -1000000000000 - channel.id

                self.mongoDataBase.update_field(database_name='tbot', collection_name='chats', action='$inc',
                                           filter={'chat_id': channel_id}, query=query)
            else:
                raise ContinuePropagation
        except Exception:
            # TODO Exceptions
            pass

        # update.continue_propagation()
        raise ContinuePropagation
        """

    # ------------------------------------------------------------------------------------------------------------------
    # Something else ---------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # url = urls.split('&')
    # for item in url:
    #    print(item)

    # if info['duration'] >= YoutubeHelper.max_track_duration:
    #    return None
    # if info['duration'] <= 0.1:
    #    return None

    # if 'entries' in info:
    #    for video in info['entries']:
    # url = video['url']
    #        url = video['formats']['480p']['url']
    # else:
    # url = info['url']
    #    url = info['formats']['url']

    # Source = "https://www.youtube.com/watch?v=A7k2CMRBq4U"

    # with youtube_dl.YoutubeDL(dict(forceurl=True)) as ydl:
    # r = ydl.extract_info(Source, download=False)
    #   media_url = r['formats'][-1]['webhook_url']

    # print(media_url)
    # SOURCE = "https://www.youtube.com/watch?v=p0lbm5J0uUs"
    # video = pafy.new(SOURCE)
    # source = video.getbest().url

    # source = "https://cf-media.sndcdn.com/UPc0t917g9OV.128.mp3?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiKjovL2NmLW1lZGlhLnNuZGNkbi5jb20vVVBjMHQ5MTdnOU9WLjEyOC5tcDMqIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNjM1ODIyNDA1fX19XX0_&Signature=FdEBG9g8KB4JCLZmYWbPkCyD-QJJNrae5l4R1iyR6a96iLmBrDafuDKttVUIp0HvH5N5Sj6ez6AsHwfCIH6ZoxdvElrLCGs9YxGYsH8uSLUo7a8r74VbMY9V-XFxRLQCusIhxjrJocwATxhG-brwQELjnuOaNtWZHbEN7RRto9L-99jyVJN-6gDd-oAB5Sh8y3EGunfebhAU1hAqf-YFG1Ue1oSvvKzQEhqjECx3RI0UUvzeyKkSd3srskqh-klzazZ0fcSBzlTvUQlrrHtIistwtgSxWK65WaI4qLluHrg8y8j-K2S6kVUMwBQfTKVrybOLwq5M~R9Qx7TNUjKEaA__&Key-Pair-Id=APKAI6TU7MMXM5DG6EPQ"

    # @staticmethod
    # def on_played_data(self, gc, length, fifo=av.AudioFifo(format='s16le')):
    #    data = fifo.read(length / 4)
    #    if data:
    #        data = data.to_ndarray().tobytes()
    #    return data

    # async def start(self, user_bot, message: Message):
    # group_call_factory = GroupCallFactory(user_bot, GroupCallFactory.MTPROTO_CLIENT_TYPE.PYROGRAM)
    # group_call_raw = group_call_factory.get_raw_group_call(on_played_data=self.on_played_data)
    # group_call_raw.play_on_repeat = False

    # if not group_call_raw.is_connected:
    #    await group_call_raw.start(message.chat.id)
    # else:
    #    await message.reply_text(text="I'm already connected")
