"""
Web plugin to work with Web
"""
import gettext

from aiohttp import web
from plugins.Bots.AiogramBot.bot import AiogramBot
from plugins.Bots.PyrogramBot.bot import PyrogramBot
from plugins.Web.handlers import WebServerHandler
from aiogram.dispatcher.webhook import get_new_configured_app
from plugins.Twitch.twitch import Twitch
from plugins.Twitch.eventsub import EventSub
from plugins.DataBase.mongo import MongoDataBase
from plugins.Google.google import Google
from pyrogram.errors import exceptions


class WebServer:
    """
    Class to work with Handler
    """

    def __init__(self, mongoDataBase: MongoDataBase = None, aiogramBot: AiogramBot = None,
                 pyrogramBot: PyrogramBot = None, twitch: Twitch = None, eventSub: EventSub = None,
                 google: Google = None, language: str = 'ru'):
        self.mongoDataBase = mongoDataBase

        try:
            self.languages = {'_': gettext.gettext,
                              'en': gettext.translation(domain='en', localedir='locale', languages=['en']),
                              'ru': gettext.translation(domain='ru', localedir='locale', languages=['ru']), }

            query = {'_id': 0, 'language_code': 1}

            document = self.mongoDataBase.get_document(database_name='tbot', collection_name='init', query=query)

            if document:
                language_code = document.get('language_code', 'ru')
            else:
                language_code = 'ru'

            self.languages.get(language_code).install()
        except OSError:
            # TODO change print
            print('Error set up languages')

        if aiogramBot:
            self.client = get_new_configured_app(dispatcher=aiogramBot.dispatcher, path=aiogramBot.webhook_path)
            #self.client['websockets'] = weakref.WeakSet()
            #self.client = web.Application()
            self.aiogramBot = aiogramBot
        else:
            self.aiogramBot = None
            self.client = web.Application()

            #self.runner = aiohttp.web.AppRunner(self.client)

        self.pyrogramBot = pyrogramBot
        self.twitch = twitch
        self.eventSub = eventSub
        self.google = google

        self.handler = WebServerHandler(webServer=self)
        self.client.on_startup.append(self.__on_startup)
        self.client.on_shutdown.append(self.__on_shutdown)
        #self.PyrogramBot.add_handler(MessageHandler(callback=type, filters=filters.command("type", prefixes=".")))

        #self.client['websockets'] = weakref.WeakSet()

    async def __on_startup(self, web):
        if self.aiogramBot:
            #await self.aiogramBot.dispatcher.skip_updates()
            await self.aiogramBot.set_webhook_url(webhook_url=self.aiogramBot.webhook_url,
                                                  certificate=self.aiogramBot.certificate)
            await self.aiogramBot.set_default_commands()

        if self.pyrogramBot:
            try:
                await self.pyrogramBot.user.start()
            except ConnectionError:
                # TODO connection error
                pass

            try:
                await self.pyrogramBot.bot.start()
            except ConnectionError:
                # TODO connection error
                pass

            await self.pyrogramBot.set_default_commands()
            await self.pyrogramBot.set_default_commands_ru()

            # session = await self.pyrogramBot.bot.export_session_string()
            # print(session)

        if self.twitch:
            self.twitch.authenticate_app([])

        await self.pyrogramBot.bot.send_message(chat_id=365867152, text="Online")

    async def __on_shutdown(self, web):
        if self.aiogramBot:
            await self.aiogramBot.client.delete_webhook()

        if self.eventSub:
            self.eventSub.unsubscribe_all_known()

        await self.pyrogramBot.bot.send_message(chat_id=365867152, text="Offline")

        if self.pyrogramBot:
            try:
                await self.pyrogramBot.user.stop()
            except ConnectionError:
                # TODO connection error
                pass

            try:
                await self.pyrogramBot.bot.stop()
            except ConnectionError:
                # TODO connection error
                pass
        #await pyrogram.idle()

        #await self.AiogramBot.dispatcher.storage.close()
        #await self.AiogramBot.dispatcher.wait_closed()

        #await self.AiogramBot.client.close_bot()

        #for ws in set(web['websockets']):
        #    await ws.close(code=WSCloseCode.GOING_AWAY, message='Server shutdown')

        #session = aiohttp.ClientSession()
        # use the session here
        #await session.close()
        #for task in asyncio.Task.all_tasks():
        #    task.cancel()

        #loop = asyncio.get_event_loop()
        #session.stop()


"""
    async def websocket_handler(self, request):
        ws = aiohttp.web.WebSocketResponse()
        await ws.prepare(request)

        client = self.client

        request.client['websockets'].add(ws)
        try:
            async for msg in ws:
                pass
        finally:
            request.client['websockets'].discard(ws)

        return ws
"""
