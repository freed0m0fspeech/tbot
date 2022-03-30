import pyrogram.types

from aiogram.types.message import Message
from plugins.Bots.AiogramBot.bot import AiogramBot
from plugins.DataBase.mongo import MongoDataBase
from aiogram.utils import exceptions


class AiogramBotHandler:
    """
    Aiogram Handler
    """

    def __init__(self, webSerber, aiogramBot: AiogramBot, mongoDataBase: MongoDataBase):
        self.webServer = webSerber
        self.aiogramBot = aiogramBot
        self.mongoDataBase = mongoDataBase

    async def start_command(self, message: Message):
        """
        **Start command handler**

        :param message: Message: aiogram.types.message
        """
        try:
            await message.reply('Start message')
        except exceptions.BadRequest:
            print('BadRequest')

    async def help_command(self, message: Message):
        try:
            await message.reply('Help message')
        except exceptions.BadRequest:
            print('BadRequest')

    async def echo_command(self, message: Message):
        # await AiogramBot.send_message(chat_id=message.from_user.id, text=message.text)
        try:
            await message.reply(text=message.get_args())
        except exceptions.BadRequest:
            print('BadRequest')

    #async def type_command_aiogram_handler(self, message: Message):
    #    print('type command')
        #await message.reply('Type command')
