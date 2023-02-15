"""
PyrogramBot plugin to work with pyrogram
"""
import gettext

from pyrogram.client import Client
from pyrogram.raw.base import BotCommandScope
# from pyrogram.raw.types import BotCommand, BotCommandScopeDefault, BotCommandScopeUsers, BotCommandScopePeerUser, \
#     BotCommandScopePeer, BotCommandScopeChats, BotCommandScopePeerAdmins, BotCommandScopeChatAdmins
from pyrogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeChat,
    BotCommandScopeChatAdministrators,
    BotCommandScopeChatMember,
)
from pyrogram.storage import Storage
from typing import Union, Optional
from plugins.TGCalls.groupcall import GroupCall
from pyrogram.raw.functions.bots import SetBotCommands


class PyrogramBot:
    """
    Class to work with pyrogram
    """

    def __init__(self, api_hash: str, api_id: str, bot_token=Optional[str], user_session=':memory:',
                 bot_session=':memory:'):
        # user_session: Union[str, Storage], bot_session: Union[str, Storage]
        # self.user = Client(session_name=user_session, api_id=api_id, api_hash=api_hash)
        # self.bot = Client('bot', bot_token='-', api_id=api_id, api_hash=api_hash)
        # self.bot = Client(session_name=bot_session, api_id=api_id, api_hash=api_hash)

        self.user = Client(name="userbot", session_string=user_session, api_id=api_id, api_hash=api_hash,
                           in_memory=True)
        self.bot = Client(name="bot", bot_token=bot_token, api_id=api_id, api_hash=api_hash, in_memory=True)

        # TODO user session authorization to :memory:

        self.groupCall = GroupCall(self)

        #self.MessageHandlerCommands = {*[command.command for command in self.bot_commands_default.commands],
        #                               *[command.command for command in self.bot_commands_chats.commands],
        #                               *[command.command for command in self.bot_commands_users.commands]}

        self.MessageHandlerCommands = {'leave': 'group', 'start': 'private', 'skip': 'group', 'queue': 'group',
                                       'speech_to_text': 'all', 'clear': 'group', 'play': 'group', 'join': 'group',
                                       'now': 'group', 'pause': 'group', 'lyrics': 'all', 'help': 'all',
                                       'stats': 'group', 'language': 'all'}
        self.CallbackQueryHandlerCommands = {'queue': 'group'}
        self.InlineQueryHandlerCommands = {'play': 'group'}

    async def __get_bot_session(self, bot_token=Optional[str], api_id=Union[int, str, None], api_hash=Optional[str],
                                              session_name=':memory:'):
        with Client(session_name, bot_token=bot_token, api_id=api_id, api_hash=api_hash) as app:
            return app.export_session_string()

    async def __get_user_session(self, api_id=Union[int, str, None], api_hash=Optional[str], session_name=':memory:'):
        with Client(session_name, api_id=api_id, api_hash=api_hash) as app:
            return app.export_session_string()

    async def set_default_commands(self, bot_commands_default: SetBotCommands = None,
                                   bot_commands_users: SetBotCommands = None,
                                   bot_commands_chats: SetBotCommands = None):
        """
        botCommandScopeDefault	The commands will be valid in all chats
        botCommandScopeUsers	The specified bot commands will only be valid in all private chats with users.
        botCommandScopeChats	The specified bot commands will be valid in all groups and supergroups
        botCommandScopeChatAdmins	The specified bot commands will be valid only for chat administrators, in all groups and supergroups.
        botCommandScopePeer	The specified bot commands will be valid only in a specific dialog
        botCommandScopePeerAdmins	The specified bot commands will be valid for all admins of the specified group or supergroup.
        botCommandScopePeerUser	The specified bot commands will be valid only for a specific user in the specified chat
        """

        if not bot_commands_default:
            bot_commands_default = [
                BotCommand(command='start', description="Start command"),
                BotCommand(command='help', description="Help command"),
            ]
        if not bot_commands_users:
            bot_commands_users = [
                BotCommand(command='start', description="Start command"),
                BotCommand(command='help', description="Help command"),
                #BotCommand(command='echo', description="Echo any message (/echo [message])"),
                BotCommand(command='lyrics', description='Lyrics for current playing audio or song title'),
                BotCommand(command='speech_to_text', description="Speech to text (reply to voice with /speech_to_text)"),
            ]
        if not bot_commands_chats:
            bot_commands_chats = [
                BotCommand(command='help', description="Help command"),
                BotCommand(command='play', description="Play media by url or text (/play [url/text]) "
                                                       "(@sc@, @yt@, @video@, @sync@)"),
                BotCommand(command='skip', description="Skip playing media"),
                BotCommand(command='clear', description="Clear queue (/clear [count/-count/0])"),
                BotCommand(command='pause', description="Pause/Resume media"),
                BotCommand(command='now', description="Now playing media info"),
                BotCommand(command='queue', description="Group queue media info (/queue [page])"),
                BotCommand(command='leave', description="Stop playing media"),
                BotCommand(command='join', description="Join group call"),
                BotCommand(command='lyrics', description='Lyrics for current playing audio or song title'),
                BotCommand(command='speech_to_text', description="Speech to text (reply to voice with /speech_to_text)"),
                BotCommand(command='stats', description="Stats about you or some person in group (/stats [user])"),
                #BotCommand(command='language', description="Change language of bot (/language [lang_code])"),
            ]

        await self.bot.set_bot_commands(bot_commands_default, scope=BotCommandScopeDefault(), language_code='en')
        await self.bot.set_bot_commands(bot_commands_users, scope=BotCommandScopeAllPrivateChats(), language_code='en')
        await self.bot.set_bot_commands(bot_commands_chats, scope=BotCommandScopeAllGroupChats(), language_code='en')

    async def set_default_commands_ru(self):
        bot_commands_default = [
            BotCommand(command='start', description="Start команда"),
            BotCommand(command='help', description="Help команда"),
        ]

        bot_commands_users = [
            BotCommand(command='start', description="Start команда"),
            BotCommand(command='help', description="Help команда"),
            # BotCommand(command='echo', description="Echo any message (/echo [message])"),
            BotCommand(command='lyrics', description='Слова песни для текущей песни или названия (/lyrics [название])'),
            BotCommand(command='speech_to_text',
                       description="Распознаниие речи в голосовом сообщении (переслать голосовое с /speech_to_text)"),
        ]
        bot_commands_chats = [
            BotCommand(command='help', description="Help команда"),
            BotCommand(command='play', description="Добавить в очередь мультимедиа (/play [url/название]) "
                                                   "(@sc@, @yt@, @video@, @sync@)"),
            BotCommand(command='skip', description="Пропуск мультимедиа"),
            BotCommand(command='clear', description="Очисить очередь (/clear [количество/-количество/0])"),
            BotCommand(command='pause', description="Приостановить/Возобновить мультимедиа"),
            BotCommand(command='now', description="Информация о текущем мультимедиа"),
            BotCommand(command='queue', description="Очередь мультимедиа (/queue [станица])"),
            BotCommand(command='leave', description="Покинуть голосовой канал"),
            BotCommand(command='join', description="Присойденится к голосовому каналу"),
            BotCommand(command='lyrics', description='Слова песни для текущей песни или названия (/lyrics [название])'),
            BotCommand(command='speech_to_text',
                       description="Распознаниие речи в голосовом сообщении (переслать голосовое с /speech_to_text)"),
            BotCommand(command='stats', description="Информация о участнике или топ группы (/stats [участник])"),
            # BotCommand(command='language', description="Change language of bot (/language [lang_code])"),
        ]

        await self.bot.set_bot_commands(bot_commands_default, scope=BotCommandScopeDefault(), language_code='ru')
        await self.bot.set_bot_commands(bot_commands_users, scope=BotCommandScopeAllPrivateChats(), language_code='ru')
        await self.bot.set_bot_commands(bot_commands_chats, scope=BotCommandScopeAllGroupChats(), language_code='ru')
