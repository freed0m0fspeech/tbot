"""
AiogramBot plugin to work with aiogram
"""
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.bot import Bot
from aiogram.types import BotCommand
from typing import Optional


class AiogramBot:
    """
    Class to work with aiogram
    """

    def __init__(self, token, webhook_path, webhook_url: Optional[str] = None, certificate: Optional[str] = None):
        self.client = Bot(token=token)
        self.dispatcher = Dispatcher(bot=self.client)
        self.webhook_path = webhook_path
        self.webhook_url = webhook_url
        self.certificate = certificate

    async def set_default_commands(self):
        await self.client.set_my_commands([
            BotCommand('start', "Start command"),
            BotCommand('help', "Help command"),
            BotCommand('echo', "Echo any message (/echo [message])"),
            BotCommand('type', "Print any message with animation (/type [message])"),
            BotCommand('play', "Play media by url or text (/play [url/text]) "
                               "(@sc@, @yt@, @audio@, @sync@)"),
            BotCommand('skip', "Skip playing media (/skip)"),
            BotCommand('pause', "Pause/Resume media (/pause)")
        ])

    async def set_webhook_url(self, webhook_url=None, certificate=None):
        webhook = await self.client.get_webhook_info()

        if webhook_url:
            if webhook.url != webhook_url:
                if not webhook.url:
                    await self.client.delete_webhook()

            if certificate:
                with open(certificate, 'rb') as certificate_file:
                    await self.client.set_webhook(url=webhook_url, certificate=certificate_file)
            else:
                await self.client.set_webhook(url=webhook_url)
        elif webhook.url:
            await self.client.delete_webhook()
