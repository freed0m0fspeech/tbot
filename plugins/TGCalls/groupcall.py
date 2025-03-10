from pytgcalls import GroupCallFactory
from plugins.TGCalls.handlers import TGCallsHandler
from pyrogram.raw.functions import phone


class GroupCall:
    """
    GroupCall to work with tgcalls
    """

    def __init__(self, pyrogramBot):
        self.pyrogramBot = pyrogramBot
        self.factory = GroupCallFactory(pyrogramBot.user)
        self.client = self.factory.get_group_call()
        # self.mute = False

        self.audio_formats = {'3gp', 'aac', 'mp3', 'wav', 'm4a', 'webm', 'ogg', 'opus'}
        self.video_formats = {'flv', 'mp4'}

        self.handler = TGCallsHandler(groupCall=self)

        # self.client.on_media_playout_ended()
