from plugins.Bots.AiogramBot.bot import AiogramBot
from plugins.Twitch.eventsub import EventSub
from aiohttp.web import Request, Response
from pprint import pprint
from plugins.DataBase.mongo import MongoDataBase


class TwitchHandler:
    """
    Twitch Handler
    """

    def __init__(self, webSerber, aiogramBot: AiogramBot, eventSub: EventSub, mongoDataBase: MongoDataBase):
        self.webServer = webSerber
        self.aiogramBot = webSerber.aiogramBot
        self.pyrogramBot = webSerber.pyrogramBot
        self.eventSub = eventSub
        self.twitch = eventSub.twitch
        self.mongoDataBase = mongoDataBase

    async def __test(self):
        self.eventSub.wait_for_subscription_confirm = False
        #self.eventSub.unsubscribe_all()

        TARGET_USERNAME = "Jazer"
        uid = self.twitch.get_users(logins=[TARGET_USERNAME])
        user_id = uid['data'][0]['id']
        sub_type = 'channel.follow'

        self.eventSub.subscribe(sub_type, '1', {'broadcaster_user_id': user_id}, sub_type)

    async def twitch_event_handler(self, callback: str, sub_id, data: dict):
        # TODO EVENT HANDLER
        """
        **Twitch event handler**

        :param callback: Callback name
        :param sub_id: ID of subscription
        :param data: Data received in callback
        """
        print('------------------------------------------')
        print(callback)
        pprint(data['event']['user_name'])
        await self.aiogramBot.client.send_message(chat_id=365867152, text=f"{callback}: {data['event']['user_name']}")

    async def twitch_challenge_handler(self, request: 'Request', data: dict):
        """
        **Twitch challenge handler**

        :param request: Request: aiohttp.web.Request
        :param data: Data: dict
        :return:
        """
        print(f'received challenge for subscription {data.get("subscription").get("id")}')
        if not await self.eventSub.verify_signature(request):
            print(f'message signature is not matching! Discarding message')
            return Response(status=403)
        self.eventSub.activate_callback(data.get('subscription').get('id'))

        print(f'subscribed to {data.get("subscription").get("id")}')
        return Response(text=data.get('challenge'))

    async def twitch_callback_handler(self, request: 'Request'):
        """
        **Twitch callback handler**

        :param request: Request: aiohttp.web.Request
        :return:
        """
        data: dict = await request.json()
        if data.get('challenge') is not None:
            return await self.twitch_challenge_handler(request, data)
        sub_id = data.get('subscription', {}).get('id')
        callback = self.eventSub.callbacks.get(sub_id)
        if callback is None:
            print(f'received event for unknown subscription with ID {sub_id}')
        else:
            if not await self.eventSub.verify_signature(request):
                print(f'message signature is not matching! Discarding message')
                return Response(status=403)
            await self.twitch_event_handler(callback=callback['callback'], sub_id=sub_id, data=data)
            #await callback['callback'](data)
        return Response(status=200)
