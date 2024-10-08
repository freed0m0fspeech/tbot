"""
WebServerHandler plugin to work with Handler
"""
import asyncio
import json
import os
import textwrap
from datetime import datetime

import pyrogram.types
import rsa

from json import dumps, JSONDecodeError
from math import sqrt
from bson import json_util
from dotenv import load_dotenv
from pyrogram.enums import MessagesFilter
from pyrogram.errors import FloodWait
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, InlineQueryHandler, ChosenInlineResultHandler, \
    RawUpdateHandler
from pyrogram import filters, errors
from aiohttp.web import Response, Request, json_response
from pytz import utc

from plugins.Bots.AiogramBot.handlers import AiogramBotHandler
from plugins.Bots.PyrogramBot.handlers import PyrogramBotHandler
from plugins.Twitch.handlers import TwitchHandler
from pyrogram.types import ChatPrivileges

load_dotenv()

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split(' ')


class WebServerHandler:
    """
    Class to work with Handler
    """

    def __init__(self, webServer):
        self.webServer = webServer
        self.mongoDataBase = webServer.mongoDataBase
        self.__register_routes()

        if webServer.aiogramBot:
            self.aiogramBot = webServer.aiogramBot
            self.aiogramBotHandler = AiogramBotHandler(webSerber=self.webServer, aiogramBot=self.aiogramBot,
                                                       mongoDataBase=self.mongoDataBase)
            self.__register_handlers_aiogramBot()

            if webServer.twitch:
                self.twitch = webServer.twitch
                if webServer.eventSub:
                    self.eventSub = webServer.eventSub
                    self.twitchHandler = TwitchHandler(webSerber=self.webServer, aiogramBot=self.aiogramBot,
                                                       eventSub=self.eventSub, mongoDataBase=self.mongoDataBase)
                    self.__register_handlers_twitch()

        if webServer.pyrogramBot:
            self.pyrogramBot = webServer.pyrogramBot
            self.pyrogramBotHandler = PyrogramBotHandler(webSerber=self.webServer, pyrogramBot=self.pyrogramBot,
                                                         mongoDataBase=self.mongoDataBase)
            self.__register_handlers_pyrogramBot()

    # ------------------------------------------------------------------------------------------------------------------
    # Register ---------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # Routes -----------------------------------------------------------------------------------------------------------
    def __register_routes(self):
        self.webServer.client.router.add_route('GET', '/', self.__default_handler)
        self.webServer.client.router.add_route('POST', '/', self.__default_handler)
        self.webServer.client.router.add_route('GET', '/member/{chat:[^\\/]+}/{user:[^\\/]+}',
                                               self.__member_parameters_handler)
        self.webServer.client.router.add_route('GET', '/user/{user:[^\\/]+}',
                                               self.__user_parameters_handler)
        self.webServer.client.router.add_route('GET', '/chat/{chat:[^\\/]+}',
                                               self.__chat_parameters_handler)
        self.webServer.client.router.add_route('POST', '/send/{chat:[^\\/]+}',
                                               self.__send_message_handler)
        self.webServer.client.router.add_route('POST', '/manage/{chat:[^\\/]+}/{user:[^\\/]+}',
                                               self.__manage_chat_handler)

    # Aiogram ----------------------------------------------------------------------------------------------------------
    def __register_handlers_aiogramBot(self):
        self.aiogramBot.dispatcher.register_message_handler(self.aiogramBotHandler.start_command,
                                                            commands=['start'])
        self.aiogramBot.dispatcher.register_message_handler(self.aiogramBotHandler.help_command,
                                                            commands=['help'])
        self.aiogramBot.dispatcher.register_message_handler(self.aiogramBotHandler.echo_command,
                                                            commands=['echo'])

    # Pyrogram ---------------------------------------------------------------------------------------------------------
    def __register_handlers_pyrogramBot(self):
        # User ---------------------------------------------------------------------------------------------------------
        # MessageHandler
        # self.pyrogramBot.user.add_handler(
        #    MessageHandler(callback=self.pyrogramBotHandler.type_command,
        #                   filters=filters.regex(r'/type.*')))  # filters.command("type", prefixes="/")))
        # Bot ----------------------------------------------------------------------------------------------------------

        # raw update handler
        # -1 - group value to handle multiple handlers, lower value - higher priority
        # self.pyrogramBot.bot.add_handler(RawUpdateHandler(callback=self.pyrogramBotHandler.raw_update_handler), -1)
        # FIXME
        # only user can add raw update handler
        self.pyrogramBot.user.add_handler(RawUpdateHandler(callback=self.pyrogramBotHandler.raw_update_handler))
        # self.pyrogramBot.user.add_handler(MessageHandler(callback=self.pyrogramBotHandler.on_message_bot, filters=filters.private))

        for command, chat_type in self.pyrogramBot.MessageHandlerCommands.items():
            callback = getattr(self.pyrogramBotHandler, f'{command}_command')
            filter_chat_type = getattr(filters, chat_type)

            self.pyrogramBot.bot.add_handler(
                MessageHandler(callback=callback, filters=filters.command(f'{command}') & filter_chat_type)
            )

        for command, chat_type in self.pyrogramBot.InlineQueryHandlerCommands.items():
            callback = getattr(self.pyrogramBotHandler, f'{command}_inline_query')
            # filter_chat_type = getattr(filters, chat_type)

            self.pyrogramBot.bot.add_handler(
                InlineQueryHandler(callback=callback, filters=filters.regex(rf'/{command}.*'))
                # filters.command(f'{command}'))
            )

        for command, chat_type in self.pyrogramBot.CallbackQueryHandlerCommands.items():
            callback = getattr(self.pyrogramBotHandler, f'{command}_callback_query')
            # filter_chat_type = getattr(filters, chat_type)

            self.pyrogramBot.bot.add_handler(
                CallbackQueryHandler(callback=callback, filters=filters.command(f'{command}'))
            )
        # MessageHandler
        # PLAYER
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.play_command,
        #                                                filters=filters.regex(r'/play.*')))
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.skip_command,
        #                                                filters=filters.regex(r'/skip.*')))
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.pause_command,
        #                                                filters=filters.regex(r'/pause.*')))
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.clear_command,
        #                                                filters=filters.regex(r'/clear.*')))
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.now_command,
        #                                                filters=filters.regex(r'/now.*')))
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.queue_command,
        #                                                filters=filters.regex(r'/queue.*')))
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.leave_command,
        #                                                filters=filters.regex(r'/leave.*')))
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.join_command,
        #                                                filters=filters.regex(r'/join.*')))
        # SPEECH RECOGNITION
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.speech_to_text_command,
        #                                                filters=filters.regex(r'/speech_to_text.*')))
        # DEFAULT
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.start_command,
        #                                                filters=filters.regex(r'/start.*')))
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.help_command,
        #                                                filters=filters.regex(r'/help.*')))
        # self.pyrogramBot.bot.add_handler(MessageHandler(callback=self.pyrogramBotHandler.echo_command,
        #                                                filters=filters.regex(r'/echo.*')))
        # CallbackQueryHandler
        # self.pyrogramBot.bot.add_handler(CallbackQueryHandler(callback=self.pyrogramBotHandler.queue_callback_query,
        #                                                      filters=filters.regex(r'/queue.*')))
        # InlineQueryHandler
        # self.pyrogramBot.bot.add_handler(InlineQueryHandler(callback=self.pyrogramBotHandler.play_inline_query,
        #                                                    filters=filters.regex(r'/play.*')))
        # ChoosenInlineResultHandler
        # self.pyrogramBot.bot.add_handler(
        #    ChosenInlineResultHandler(callback=self.pyrogramBotHandler.answer_inline_result))

    # Twitch -----------------------------------------------------------------------------------------------------------
    def __register_handlers_twitch(self):
        self.webServer.client.router.add_route('POST', f'/webhook/{os.getenv("TOKEN")}/twitch/callback',
                                               self.twitchHandler.twitch_callback_handler)

    # self.webServer.client.router.add_route('POST', f'/webhook/{os.getenv("TOKEN")}/twitch',
    #                                         self.__twitch_event_handler)

    # ------------------------------------------------------------------------------------------------------------------
    # Routes Handler --------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    async def __default_handler(self, request: 'Request'):
        return Response(text="I'm Web handler")

    async def __send_message_handler(self, request: 'Request'):
        # if request.headers.get('Origin', '').split("//")[-1].split("/")[0].split('?')[0] not in ALLOWED_HOSTS:
        #     if not os.getenv('DEBUG', False):
        #         return Response(status=403)

        chat = request.match_info['chat']

        try:
            data = await request.json()
        except JSONDecodeError:
            data = {}

        if not data.get('publicKey', '') == os.getenv('RSA_PUBLIC_KEY', ''):
            if not os.getenv('DEBUG', False):
                return Response(status=403)

        text = data.get('text', '')
        pin = data.get('pin', '')
        if text:
            try:
                message = await self.pyrogramBot.bot.send_message(
                    chat_id=chat,
                    text=text,
                    disable_web_page_preview=True,
                )
                if pin == 'true':
                    await message.pin()
            except FloodWait as e:
                await asyncio.sleep(e.value)

        return Response()

    async def __member_parameters_handler(self, request: 'Request'):
        # if request.headers.get('Origin', '').split("//")[-1].split("/")[0].split('?')[0] not in ALLOWED_HOSTS:
        #     if not os.getenv('DEBUG', False):
        #         return Response(status=403)

        user = request.match_info['user']
        # chat_id = request.match_info['chat_id']
        chat = request.match_info['chat']

        try:
            data = await request.json()
        except JSONDecodeError:
            data = {}

        if not data.get('publicKey', '') == os.getenv('RSA_PUBLIC_KEY', ''):
            if not os.getenv('DEBUG', False):
                return Response(status=403)

        try:
            member = await self.pyrogramBot.bot.get_chat_member(chat, user)
            # chat = await self.pyrogramBot.user.get_chat(chat)
            # user = await self.pyrogramBot.user.get_users(user)

            date = datetime.now(tz=utc)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        except (errors.ChatInvalid, errors.PeerIdInvalid, errors.UserInvalid, errors.UsernameInvalid, errors.UserNotParticipant):
            return Response(status=422)

        # query = ""
        # query_filter = MessagesFilter.EMPTY
        #
        # # Search only for userbots
        # messages_count = await self.pyrogramBot.user.search_messages_count(chat_id=chat.id, from_user=user.id,
        #                                                                    query=query,
        #                                                                    filter=query_filter)
        #
        # query = {'_id': 0, f'users.{user.id}.stats': 1, 'xp': 1}
        # document = self.mongoDataBase.get_document(database_name='tbot', collection_name='chats',
        #                                            filter={'chat_id': chat.id}, query=query)

        # message_xp = document.get('xp', {}).get('message_xp', 100)
        # voice_xp = document.get('xp', {}).get('voice_xp', 50)
        # xp_factor = document.get('xp', {}).get('xp_factor', 100)  # threshold

        # voicetime = document.get('users', {}).get(f'{user.id}', {}).get('stats', {}).get('voicetime', 0)

        # xp = (messages_count * message_xp) + ((voicetime // 60) * voice_xp)

        # lvl = 0.5 + sqrt(1 + 8 * (xp) / (xp_factor)) / 2
        # lvl = int(lvl) - 1
        #
        # xp_for_level = lvl / 2 * (2 * xp_factor + (lvl - 1) * xp_factor)
        #
        # xp_have = int(xp - xp_for_level)
        # xp_need = (lvl + 1) * xp_factor

        # member_parameters = {
        #     # 'status': member.status,
        #     # 'user': member.user,
        #     # 'chat': member.chat,
        #     'joined_date': json.dumps(member.joined_date, default=json_util.default),
        #     'custom_title': member.custom_title,
        #     'until_date': json.dumps(member.until_date, default=json_util.default),  # banned until date
        #     # 'invited_by': member.invited_by,
        #     # 'promoted_by': member.promoted_by,
        #     # 'restricted_by': member.restricted_by,
        #     'is_member': member.is_member,
        #     'can_be_edited': member.can_be_edited,
        #     # 'permissions': member.permissions,
        #     # 'privileges', member.privileges,
        #     # 'messages_count': messages_count,
        #     # 'lvl': lvl,
        #     # 'xp_have': xp_have,
        #     # 'xp_need': xp_need,
        #     # 'xp': xp,
        #     # 'xp_factor': xp_factor,
        #     # 'voicetime': voicetime,
        #     'date': date,
        # }

        member_parameters = {}
        for attr in [attr for attr in dir(member) if not attr.startswith('_')]:
            try:
                value = getattr(member, attr)

                member_parameters[attr] = json.dumps(value, default=json_util.default)
            except Exception as e:
                # Not serializable
                pass

        # async for photo in self.pyrogramBot.bot.get_chat_photos(member.user.id):
        #     print(photo.thumbs[1].file_id)
        #     break

        member_parameters['date'] = date

        response = {
            'member_parameters': member_parameters
        }
        # 'user': user.username,
        # 'chat.title': chat.title,
        # 'chat.members_count': chat.members_count,
        # 'member.joined_date': json.dumps(member.joined_date, default=json_util.default),
        # 'member.messages_count': messages_count,
        # 'member.custom_title': member.custom_title,

        return json_response(response)

    async def __user_parameters_handler(self, request: 'Request'):
        # if request.headers.get('Origin', '').split("//")[-1].split("/")[0].split('?')[0] not in ALLOWED_HOSTS:
        #     if not os.getenv('DEBUG', False):
        #         return Response(status=403)

        user = request.match_info['user']

        try:
            data = await request.json()
        except JSONDecodeError:
            data = {}

        if not data.get('publicKey', '') == os.getenv('RSA_PUBLIC_KEY', ''):
            if not os.getenv('DEBUG', False):
                return Response(status=403)

        try:
            user = await self.pyrogramBot.bot.get_users(user)

            date = datetime.now(tz=utc)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        except (errors.UsernameInvalid, errors.PeerIdInvalid, errors.UserInvalid):
            return Response(status=422)

        # user_parameters = {
        #     'id': user.id,
        #     'is_self': user.is_self,
        #     'is_contact': user.is_contact,
        #     'is_mutual_contact': user.is_mutual_contact,
        #     'is_deleted': user.is_deleted,
        #     'is_bot': user.is_bot,
        #     'is_verified': user.is_verified,
        #     'is_restricted': user.is_restricted,
        #     'is_scam': user.is_scam,
        #     'is_fake': user.is_fake,
        #     'is_support': user.is_support,
        #     'is_premium': user.is_premium,
        #     'first_name': user.first_name,
        #     'last_name': user.last_name,
        #     # 'status': user.status,
        #     'last_online_date': json.dumps(user.last_online_date, default=json_util.default),
        #     'next_offline_date': json.dumps(user.next_offline_date, default=json_util.default),
        #     'username': user.username,
        #     'language_code': user.language_code,
        #     # 'emoji_status': user.emoji_status,
        #     'dc_id': user.dc_id,
        #     'phone_number': user.phone_number,
        #     # 'photo': user.photo,
        #     # 'restrictions': user.restrictions,
        #     'mention': user.mention,
        #     'date': date,
        # }

        user_parameters = {}
        for attr in [attr for attr in dir(user) if not attr.startswith('_')]:
            try:
                value = getattr(user, attr)

                user_parameters[attr] = json.dumps(value, default=json_util.default)
            except Exception as e:
                # Not serializable
                pass

        user_parameters['date'] = date

        response = {
            'user_parameters': user_parameters,
        }

        return json_response(response)

    async def __chat_parameters_handler(self, request: 'Request'):
        # if request.headers.get('Origin', '').split("//")[-1].split("/")[0].split('?')[0] not in ALLOWED_HOSTS:
        #     if not os.getenv('DEBUG', False):
        #         return Response(status=403)

        chat = request.match_info['chat']

        try:
            data = await request.json()
        except JSONDecodeError:
            data = {}

        if not data.get('publicKey', '') == os.getenv('RSA_PUBLIC_KEY', ''):
            if not os.getenv('DEBUG', False):
                return Response(status=403)

        try:
            chat = int(chat)
            chat = await self.pyrogramBot.bot.get_chat(chat)

            date = datetime.now(tz=utc)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        except (errors.ChatInvalid, errors.PeerIdInvalid, errors.UsernameNotOccupied, ValueError):
            return Response(status=422)

        query = {'_id': 0, 'users': 1, 'xp': 1}
        document = self.mongoDataBase.get_document(database_name='tbot', collection_name='chats',
                                                   filter={'chat_id': chat.id}, query=query)

        message_xp = document.get('xp', {}).get('message_xp', 100)
        voice_xp = document.get('xp', {}).get('voice_xp', 50)
        xp_factor = document.get('xp', {}).get('xp_factor', 100)  # threshold

        members_parameters = {}
        async for member in self.pyrogramBot.bot.get_chat_members(chat_id=chat.id):
            if member.user.is_bot:
                continue
            # Search only for userbots
            # query = ""
            # query_filter = MessagesFilter.EMPTY
            #
            # messages_count = await self.pyrogramBot.user.search_messages_count(chat_id=chat.id,
            #                                                                    from_user=member.user.id,
            #                                                                    query=query, filter=query_filter)

            messages_count = document.get('users', {}).get(f'{member.user.id}', {}).get('stats', {}).get('messages_count', 0)
            # reactions_count = document.get('users', {}).get(f'{member.user.id}', {}).get('stats', {}).get('reactions_count', {})
            voicetime = document.get('users', {}).get(f'{member.user.id}', {}).get('stats', {}).get('voicetime', 0)

            # xp = (messages_count * message_xp) + ((voicetime // 60) * voice_xp)
            xp = document.get('users', {}).get(f'{member.user.id}', {}).get('stats', {}).get('xp', 0)

            # lvl = 0.5 + sqrt(1 + 8 * (xp) / (xp_factor)) / 2
            # lvl = int(lvl) - 1
            #
            # xp_for_level = lvl / 2 * (2 * xp_factor + (lvl - 1) * xp_factor)
            #
            # xp_have = int(xp - xp_for_level)
            # xp_need = (lvl + 1) * xp_factor

            date = datetime.now(tz=utc)
            date = date.strftime('%Y-%m-%d %H:%M:%S')

            # member_parameters = {
            #     'messages_count': messages_count,
            #     # 'lvl': lvl,
            #     # 'xp_have': xp_have,
            #     # 'xp_need': xp_need,
            #     'xp': xp,
            #     'xp_factor': xp_factor,
            #     'voicetime': voicetime,
            #     'joined_date': json.dumps(member.joined_date, default=json_util.default),
            #     'custom_title': member.custom_title,
            #     'until_date': json.dumps(member.until_date, default=json_util.default),
            #     'is_member': member.is_member,
            #     'can_be_edited': member.can_be_edited,
            #     'date': date,
            # }

            member_parameters = {}
            for attr in [attr for attr in dir(member) if not attr.startswith('_')]:
                try:
                    value = getattr(member, attr)

                    member_parameters[attr] = json.dumps(value, default=json_util.default)
                except Exception as e:
                    # Not serializable
                    pass

            user_parameters = {}
            for attr in [attr for attr in dir(member.user) if not attr.startswith('_')]:
                try:
                    value = getattr(member.user, attr)

                    user_parameters[attr] = json.dumps(value, default=json_util.default)
                except Exception as e:
                    # Not serializable
                    pass

            member_parameters['user_parameters'] = user_parameters

            member_parameters['messages_count'] = messages_count
            # member_parameters['reactions_count'] = reactions_count
            # 'lvl': lvl,
            # 'xp_have': xp_have,
            # 'xp_need': xp_need,
            member_parameters['xp'] = xp
            member_parameters['xp_factor'] = xp_factor
            member_parameters['voicetime'] = voicetime
            member_parameters['date'] = date

            members_parameters[member.user.id] = member_parameters

        stats = []

        for user_id, parameters in members_parameters.items():
            stat = (user_id, parameters.get('xp', 0))
            stats.append(stat)

        # Sort members by xp
        stats.sort(reverse=True, key=lambda x: x[1])

        i = 0
        for stat in stats:
            i += 1
            # Position for member in chat by xp
            user_id = stat[0]
            members_parameters[user_id]['position'] = i

        # chat_parameters = {
        #     'id': chat.id,
        #     # 'type': chat.type,
        #     'is_verified': chat.is_verified,
        #     'is_restricted': chat.is_restricted,
        #     'is_creator': chat.is_creator,
        #     'is_scam': chat.is_scam,
        #     'is_fake': chat.is_fake,
        #     'is_support': chat.is_support,
        #     'title': chat.title,
        #     'username': chat.username,
        #     'first_name': chat.first_name,
        #     'last_name': chat.last_name,
        #     # 'photo': chat.photo,
        #     'bio': chat.bio,
        #     'description': chat.description,
        #     'dc_id': chat.dc_id,
        #     'has_protected_content': chat.has_protected_content,
        #     'invite_link': chat.invite_link,
        #     # 'pinned_message': chat.pinned_message,
        #     'sticker_set_name': chat.sticker_set_name,
        #     'can_set_sticker_set': chat.can_set_sticker_set,
        #     'members_count': chat.members_count,
        #     # 'restrictions': chat.restrictions,
        #     # 'permissions': chat.permissions,
        #     'distance': chat.distance,
        #     'xp_factor': xp_factor,
        #     'message_xp': message_xp,
        #     'voice_xp': voice_xp,
        #     # 'linked_chat': chat.linked_chat,
        #     # 'send_as_chat': chat.send_as_chat,
        #     # 'available_reactions': chat.available_reactions,
        #     'date': date,
        # }

        chat_parameters = {}
        for attr in [attr for attr in dir(chat) if not attr.startswith('_')]:
            try:
                value = getattr(chat, attr)

                chat_parameters[attr] = json.dumps(value, default=json_util.default)
            except Exception as e:
                # Not serializable
                pass

        chat_parameters['date'] = date

        response = {
            'chat_parameters': chat_parameters,
            'members_parameters': members_parameters,
        }

        return json_response(response)

    async def __manage_chat_handler(self, request: 'Request'):
        # if request.headers.get('Origin', '').split("//")[-1].split("/")[0].split('?')[0] not in ALLOWED_HOSTS:
        #     if not os.getenv('DEBUG', False):
        #         return Response(status=403)

        user = request.match_info['user']
        chat = request.match_info['chat']

        try:
            data = await request.json()
        except JSONDecodeError:
            data = {}

        if not data.get('publicKey', '') == os.getenv('RSA_PUBLIC_KEY', ''):
            if not os.getenv('DEBUG', False):
                return Response(status=403)

        action = data.get('action', '')
        parameters = data.get('parameters', '')

        if not action:
            return Response(status=422)

        try:
            chat = int(chat)
            # member = await self.pyrogramBot.user.get_chat_member(chat, user)
            chat = await self.pyrogramBot.bot.get_chat(chat)
            user = await self.pyrogramBot.bot.get_users(user)
        except (errors.ChatInvalid, errors.PeerIdInvalid, errors.UserInvalid, errors.UsernameInvalid, errors.UserNotParticipant, errors.UsernameNotOccupied, ValueError):
            return Response(status=422)

        if action == 'demote_chat_member':
            # Demote chat member
            demote_rights = ChatPrivileges()
            demote_rights.can_manage_chat = False
            await self.pyrogramBot.bot.promote_chat_member(chat_id=chat.id, user_id=user.id, privileges=demote_rights)

        if action == 'promote_chat_member':
            # Promote chat member to admin
            promote_rights = ChatPrivileges()
            if await self.pyrogramBot.bot.promote_chat_member(chat_id=chat.id, user_id=user.id, privileges=promote_rights):
                for i in range(5):
                    try:
                        if parameters:
                            custom_title = parameters.get('custom_title', '')

                            if custom_title:
                                if await self.pyrogramBot.bot.set_administrator_title(chat_id=chat.id, user_id=user.id, title=custom_title):
                                    return Response()
                    except ValueError:
                        await asyncio.sleep(5)

        return Response()

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
