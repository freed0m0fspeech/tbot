"""
WebServerHandler plugin to work with Handler
"""
import os

from pyrogram.handlers import MessageHandler, CallbackQueryHandler, InlineQueryHandler, ChosenInlineResultHandler, \
    RawUpdateHandler
from pyrogram import filters
from aiohttp.web import Response, Request

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
                InlineQueryHandler(callback=callback, filters=filters.regex(rf'/{command}.*')) #filters.command(f'{command}'))
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

    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
