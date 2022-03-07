from auction.celery import app
from auction_app.models import BaseAuction, DutchAuction, EnglishAuction
from auction_app.services.email_service import send_email_about_winner, \
    send_email_about_outbid, send_email_about_rejected_auction
from auction_app.services.offers_service import get_last_offer, change_price_in_dutch_auction
from lot_app.models import Lot


@app.task
def start_auction_task(auction_id):
    auction = BaseAuction.objects.get(pk=auction_id)
    auction.status = BaseAuction.LotStatus.IN_PROGRESS
    auction.save()


@app.task
def finish_auction_task(auction_id):
    auction = BaseAuction.objects.get(pk=auction_id)
    auction.status = BaseAuction.LotStatus.COMPLETED
    auction.save()


@app.task
def update_dutch_auction_price_task(auction_id, tick=0):
    auction = DutchAuction.objects.get(pk=auction_id)
    if tick == 0:
        update_dutch_auction_price_task.s(auction_id, tick+1)\
            .apply_async(countdown=auction.time_step.total_seconds(),
                         task_id=auction.task_id_update_price)
    elif auction.update_price_frequency == tick:
        change_price_in_dutch_auction(auction)
    else:
        change_price_in_dutch_auction(auction)
        update_dutch_auction_price_task.s(auction_id, tick+1)\
            .apply_async(countdown=auction.time_step.total_seconds(),
                         task_id=auction.task_id_update_price)


@app.task
def send_email_winner_task(user_email, lot_id):
    lot = Lot.objects.select_related('item').get(pk=lot_id)
    send_email_about_winner(user_email, lot)


@app.task
def send_email_outbid_prices_task(user_email, lot_id):
    lot = Lot.objects.select_related('item').get(pk=lot_id)
    send_email_about_outbid(user_email, lot)


@app.task
def send_email_winner_rejected_task(user_email, lot_id):
    lot = Lot.objects.select_related('item').get(pk=lot_id)
    send_email_about_rejected_auction(user_email, lot)


@app.task
def announce_the_winner_task(auction_id):
    auction = EnglishAuction.objects.get(pk=auction_id)
    offer = get_last_offer(auction.lot)
    if offer is not None and offer.user.email != '':
        if offer.offered_price >= auction.reserved_price:
            send_email_winner_task.s(offer.user.email, offer.lot.pk).apply_async()
        else:
            send_email_winner_rejected_task.s(offer.user.email, offer.lot.pk).apply_async()
