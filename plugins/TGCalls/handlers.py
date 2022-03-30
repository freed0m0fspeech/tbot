from pytgcalls.implementation.group_call import GroupCall


class TGCallsHandler:
    """
    Class to work with Handler
    """

    def __init__(self, groupCall):
        self.groupCall = groupCall

        # self.__register_handlers()

    def __register_handlers(self):
        #self.groupCall.client.add_handler(self.__on_audio_playout_ended, GroupCallAction.AUDIO_PLAYOUT_ENDED)
        #assert isinstance(self.groupCall.client, GroupCall)
        # self.groupCall.client.on_media_playout_ended(self.__on_media_playout_ended)
        # self.groupCall.client.on_network_status_changed(self.__on_network_status_changed)
        self.groupCall.client.on_participant_list_updated(self.__on_participant_list_updated)
        #self.groupCall.client.on_audio_playout_ended(self.__on_audio_playout_ended)
        #self.groupCall.client.on_video_playout_ended(self.__on_video_playout_ended)

    async def __on_media_playout_ended(self, *args):
        # TODO medio playout ended handler
        """
        media_playout_ended handler
        """
        #await groupCall.leave_current_group_call()
        #print(mediaTypeArgs)
        print('media playout ended', args)
        # print(args)

    async def __on_audio_playout_ended(self, *args):
        # TODO audio playout ended handler
        print('audio playout ended', args)
        # print(args)

    async def __on_video_playout_ended(self, *args):
        # TODO video playout ended handler
        print('video playout ended', args)
        # print(args)

    async def __on_network_status_changed(self, *args):
        # TODO network status changed handler
        print('network status changed', args)
        # print(args)

    async def __on_participant_list_updated(self, *args):
        # TODO paricipant list updated handler
        print('participant list updated', args)

        # groupCall = args[0]
        # groupCall.client: GroupCall
        # print(groupCall.client.group_call)
        # print(args)
