import asyncio
import os

from aiohttp.web import AppRunner, TCPSite
from dotenv import load_dotenv
from pyrogram import idle
from jobs.updater import start
from plugins.Bots.PyrogramBot.bot import PyrogramBot
from plugins.Web.server import WebServer
from utils import dataBases
from plugins.Google.google import Google

mongoDataBase = dataBases.mongodb_client


async def main():
    """
    Main function
    Set up and start application
    """

    # ------------------------------------------------------------------------------------------------------------------

    # https://telegram-bot-freed0m0fspeech.fly.dev/

    TOKEN = os.getenv('TOKEN')
    # HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

    # MONGODATABASE_USER = os.getenv('MONGODATABASE_USER')
    # MONGODATABASE_PASSWORD = os.getenv('MONGODATABASE_PASSWORD')
    # MONGODATABASE_HOST = os.getenv('MONGODATABASE_HOST')

    USER_SESSION = os.getenv('USER_SESSION')
    # BOT_SESSION = os.getenv('BOT_SESSION')

    PYROGRAM_API_ID = os.getenv('PYROGRAM_API_ID')
    PYROGRAM_API_HASH = os.getenv('PYROGRAM_API_HASH')

    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GOOGLE_ENGINE_ID = os.getenv('GOOGLE_ENGINE_ID')

    # TWITCH_APP_ID = os.getenv('TWITCH_APP_ID')
    # TWITCH_APP_SECRET = os.getenv('TWITCH_APP_SECRET')

    # no host specified in headers or uri fix http://
    WEBAPP_HOST = '0.0.0.0'
    WEBAPP_PORT = int(os.getenv('PORT', '80'))

    # ------------------------------------------------------------------------------------------------------------------

    # HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
    # WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
    # WEBHOOK_PATH_TWITCH = f'/webhook/{TOKEN}/twitch'
    # WEBHOOK_URL_TWITCH = f'{WEBHOOK_HOST}{WEBHOOK_PATH_TWITCH}'

    # mongoDataBase = MongoDataBase(host=MONGODATABASE_HOST, user=MONGODATABASE_USER, passwd=MONGODATABASE_PASSWORD)


    # aiogramBot = AiogramBot(token=TOKEN, webhook_path=WEBHOOK_PATH_AIOGRAM, webhook_url=WEBHOOK_URL_AIOGRAM)

    pyrogramBot = PyrogramBot(api_id=PYROGRAM_API_ID, api_hash=PYROGRAM_API_HASH, bot_token=TOKEN,
                              user_session=USER_SESSION)

    # twitch = Twitch(TWITCH_APP_ID, TWITCH_APP_SECRET)
    # event_sub = EventSub(callback_url=WEBHOOK_URL_TWITCH, api_client_id=twitch.app_id, twitch=twitch)
    twitch = None
    event_sub = None

    google = Google(api_key=GOOGLE_API_KEY, engine_id=GOOGLE_ENGINE_ID)

    # await pyrogramBot.client.start()
    # '[This is an example](https://example.com)'
    # '<a href="https://example.com">This is an example</a>'

    # await pyrogramBot.client.send_message(chat_id=-1001571685575, text='text')
    # pub_sub = PubSub(twitch=twitch)
    # webhook = TwitchWebHook(callback_url=WEBHOOK_URL_TWITCH, api_client_id=twitch.app_id, port=WEBAPP_PORT)

    webServer = WebServer(mongoDataBase=mongoDataBase, pyrogramBot=pyrogramBot, twitch=twitch, eventSub=event_sub,
                          google=google)

    # await web.runner.setup()
    # site = aiohttp.web.TCPSite(web.runner, WEBAPP_HOST, WEBAPP_PORT)
    # await site.start()

    # while True:
    #    await asyncio.sleep(3600)

    # runner = aiohttp.web.AppRunner(web.client)
    # await runner.setup()

    # site = aiohttp.web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    # await site.start()
    # await idle()

    # Client.run()
    # Client.start()

    runner = AppRunner(webServer.client)
    await runner.setup()

    # conn = aiohttp.TCPConnector(ttl_dns_cache=300)
    # conn = aiohttp.TCPConnector(use_dns_cache=False)
    # session = aiohttp.ClientSession(connector=conn)

    site = TCPSite(runner=runner, host=WEBAPP_HOST, port=WEBAPP_PORT, shutdown_timeout=60)
    await site.start()

    # if not os.getenv('DEBUG', '0').lower() in ['true', 't', '1']:
    #     start()

    await idle()
    await runner.cleanup()

    # await site.stop()
    # await runner.cleanup()
    # print(runner.sites)

    # await web.client.cleanup()

    # await session.close()
    # await conn.close()

    # aiohttp.web.run_app(app=web.client, host=WEBAPP_HOST, port=WEBAPP_PORT)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
