import json

import channels.layers
from asgiref.sync import async_to_sync
from lot_app.models import Offer


def send_event_about_updating_price(lot_id, offered_price):
    updating_price_data = json.dumps({'lot_id': lot_id,
                                      'price': offered_price},
                                     default=float)
    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)('all',
                                            {'type': 'send_price_changing',
                                             'text_data': updating_price_data})


def send_resent_lots_offers(lot):
    user_offers = get_recent_lots_offers(lot)
    if user_offers is not None:
        channel_layer = channels.layers.get_channel_layer()
        data = json.dumps(user_offers, default=float)
        async_to_sync(channel_layer.group_send)(f'Lot_{lot.id}',
                                                {'type': 'send_recent_offers',
                                                 'text_data': data})


def get_recent_lots_offers(lot):
    NUMBER_OF_RECENT_OFFERS = 5
    query = Offer.objects.select_related('user').filter(lot=lot)\
                 .order_by('-creation_datetime')[:NUMBER_OF_RECENT_OFFERS]
    if query.exists():
        return [{offer.user.username: offer.offered_price} for offer in query]
    else:
        return None
