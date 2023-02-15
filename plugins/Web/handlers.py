"""
WebServerHandler plugin to work with Handler
"""
import json
import os
from json import dumps

from bson import json_util
from pyrogram.enums import MessagesFilter
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, InlineQueryHandler, ChosenInlineResultHandler, \
    RawUpdateHandler
from pyrogram import filters, errors
from aiohttp.web import Response, Request, json_response

from plugins.Bots.AiogramBot.handlers import AiogramBotHandler
from plugins.Bots.PyrogramBot.handlers import PyrogramBotHandler
from plugins.Twitch.handlers import TwitchHandler


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

    async def __member_parameters_handler(self, request: 'Request'):
        user = request.match_info['user']
        # chat_id = request.match_info['chat_id']
        chat = request.match_info['chat']

        # try:
        #     user = await self.pyrogramBot.user.get_users(user)
        #     chat = await self.pyrogramBot.user.get_chat(chat)
        #     member = await self.pyrogramBot.user.get_chat_member(chat.id, user.id)
        # except (errors.UsernameInvalid, errors.PeerIdInvalid, errors.ChatInvalid):
        #     user = None
        #     chat = None
        #     member = None
        #
        # if not user or not chat or not member:
        #     return Response(status=422)

        try:
            member = await self.pyrogramBot.bot.get_chat_member(chat, user)
        except (errors.ChatInvalid, errors.PeerIdInvalid, errors.UserInvalid, errors.UsernameInvalid):
            member = None

        if not member:
            return Response(status=422)

        query = ""
        query_filter = MessagesFilter.EMPTY

        # Search only for userbots
        messages_count = await self.pyrogramBot.user.search_messages_count(chat_id=chat, from_user=user, query=query,
                                                                           filter=query_filter)

        member_parameters = {
            # 'status': member.status,
            # 'user': member.user,
            # 'chat': member.chat,
            'joined_date': json.dumps(member.joined_date, default=json_util.default),
            'custom_title': member.custom_title,
            'until_date': json.dumps(member.until_date, default=json_util.default), # banned until date
            # 'invited_by': member.invited_by,
            # 'promoted_by': member.promoted_by,
            # 'restricted_by': member.restricted_by,
            'is_member': member.is_member,
            'can_be_edited': member.can_be_edited,
            # 'permissions': member.permissions,
            # 'privileges', member.privileges,
        }

        response = {
            'messages_count': messages_count,
            'member_parameters': member_parameters,
        }
            # 'user': user.username,
            # 'chat.title': chat.title,
            # 'chat.members_count': chat.members_count,
            # 'member.joined_date': json.dumps(member.joined_date, default=json_util.default),
            # 'member.messages_count': messages_count,
            # 'member.custom_title': member.custom_title,

        return json_response(response)

    async def __user_parameters_handler(self, request: 'Request'):
        user = request.match_info['user']

        try:
            user = await self.pyrogramBot.bot.get_users(user)
        except (errors.UsernameInvalid, errors.PeerIdInvalid, errors.UserInvalid):
            user = None

        if not user:
            return Response(status=422)

        user_parameters = {
            'id': user.id,
            'is_self': user.is_self,
            'is_contact': user.is_contact,
            'is_mutual_contact': user.is_mutual_contact,
            'is_deleted': user.is_deleted,
            'is_bot': user.is_bot,
            'is_verified': user.is_verified,
            'is_restricted': user.is_restricted,
            'is_scam': user.is_scam,
            'is_fake': user.is_fake,
            'is_support': user.is_support,
            'is_premium': user.is_premium,
            'first_name': user.first_name,
            'last_name': user.last_name,
            # 'status': user.status,
            'last_online_date': json.dumps(user.last_online_date, default=json_util.default),
            'next_offline_date': json.dumps(user.next_offline_date, default=json_util.default),
            'username': user.username,
            'language_code': user.language_code,
            # 'emoji_status': user.emoji_status,
            'dc_id': user.dc_id,
            'phone_number': user.phone_number,
            # 'photo': user.photo,
            # 'restrictions': user.restrictions,
            'mention': user.mention,
        }

        response = {
            'user_parameters': user_parameters,
        }

        return json_response(response)

    async def __chat_parameters_handler(self, request: 'Request'):
        chat = request.match_info['chat']

        try:
            chat = await self.pyrogramBot.bot.get_chat(chat)
        except (errors.ChatInvalid, errors.PeerIdInvalid):
            chat = None

        if not chat:
            return Response(status=422)

        chat_parameters = {
            'id': chat.id,
            # 'type': chat.type,
            'is_verified': chat.is_verified,
            'is_restricted': chat.is_restricted,
            'is_creator': chat.is_creator,
            'is_scam': chat.is_scam,
            'is_fake': chat.is_fake,
            'is_support': chat.is_support,
            'title': chat.title,
            'username': chat.username,
            'first_name': chat.first_name,
            'last_name': chat.last_name,
            # 'photo': chat.photo,
            'bio': chat.bio,
            'description': chat.description,
            'dc_id': chat.dc_id,
            'has_protected_content': chat.has_protected_content,
            'invite_link': chat.invite_link,
            # 'pinned_message': chat.pinned_message,
            'sticker_set_name': chat.sticker_set_name,
            'can_set_sticker_set': chat.can_set_sticker_set,
            'members_count': chat.members_count,
            # 'restrictions': chat.restrictions,
            # 'permissions': chat.permissions,
            'distance': chat.distance,
            # 'linked_chat': chat.linked_chat,
            # 'send_as_chat': chat.send_as_chat,
            # 'available_reactions': chat.available_reactions,
        }

        response = {
            'chat_parameters': chat_parameters,
        }

        return json_response(response)

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
