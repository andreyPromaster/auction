from django.db import transaction
from django.db.models import F

from lot_app.models import Offer
from lot_app.services.web_socket_service import send_event_about_updating_price


def get_last_offer(lot):
    offer = Offer.objects.filter(lot=lot.pk)
    if offer.exists():
        return offer.latest('creation_datetime')
    return None


def get_user_by_last_offer(lot):
    offer = get_last_offer(lot)
    if offer is not None:
        return offer.user
    return None


@transaction.atomic
def change_price_in_dutch_auction(auction):
    auction.current_price = F('current_price') - auction.price_step
    auction.save()
    auction.refresh_from_db()
    send_event_about_updating_price(auction.lot.id, auction.current_price)
