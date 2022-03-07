from auction_app.models import BaseAuction
from lot_app.models import Offer
from django.db import transaction

from lot_app.services.web_socket_service import send_event_about_updating_price,\
    send_resent_lots_offers


@transaction.atomic
def save_auction_offer(lot, offered_price, user):
    lot.auction.current_price = offered_price
    lot.auction.save()
    Offer.objects.create(user=user,
                         lot=lot,
                         offered_price=offered_price)
    send_event_about_updating_price(lot.id, offered_price)
    send_resent_lots_offers(lot)


@transaction.atomic
def buy_now_english_lot(lot, user):
    offered_price = lot.auction.englishauction.buy_it_now_price
    lot.auction.current_price = offered_price
    lot.auction.status = BaseAuction.LotStatus.COMPLETED
    lot.auction.save()
    Offer.objects.create(user=user,
                         lot=lot,
                         offered_price=offered_price)
    send_event_about_updating_price(lot.id, offered_price)
    send_resent_lots_offers(lot)


@transaction.atomic
def buy_now_dutch_lot(lot, user):
    lot.auction.status = BaseAuction.LotStatus.COMPLETED
    lot.auction.save()
    Offer.objects.create(user=user,
                         lot=lot,
                         offered_price=lot.auction.current_price)
