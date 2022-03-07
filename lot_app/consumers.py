import json

from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist

from lot_app.models import Lot
from lot_app.services.web_socket_service import get_recent_lots_offers


class LotConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Join room group
        self.group_name = 'all'
        if self.scope['user'] == AnonymousUser():
            raise DenyConnection("Login failed")

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_price_changing(self, event):
        """ Receive message from room group """
        await self.send(text_data=json.dumps(event))


class OffersConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Join room group
        self.room_name = self.scope['url_route']['kwargs']['lot_id']
        self.room_group_name = f'Lot_{self.room_name}'
        if self.scope['user'] == AnonymousUser():
            raise DenyConnection("Login failed")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        try:
            lot = await get_lot(self.room_name)
        except ObjectDoesNotExist:
            raise DenyConnection("This lot not exists!")
        await self.accept()
        user_offers = await database_sync_to_async(get_recent_lots_offers)(lot)
        if user_offers is not None:
            data = json.dumps(user_offers, default=float)
            await self.send(text_data=json.dumps({'text_data': data},
                                                 default=float))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_recent_offers(self, event):
        await self.send(text_data=json.dumps(event))


@database_sync_to_async
def get_lot(lot_id):
    return Lot.objects.get(pk=lot_id)
