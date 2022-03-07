from auction_app.services.offers_service import get_user_by_last_offer
from auction_app.tasks import start_auction_task, finish_auction_task, \
    update_dutch_auction_price_task, send_email_winner_task, \
    send_email_outbid_prices_task, announce_the_winner_task


def run_start_auction_task(auction):
    start_auction_task.s(auction.pk).apply_async(eta=auction.start_date)


def run_finish_auction_task(auction):
    finish_auction_task.s(auction.pk).apply_async(eta=auction.end_date,
                                                  task_id=auction.task_id_close_auction)


def run_update_dutch_auction_price_task(auction):
    update_dutch_auction_price_task.s(auction.pk).apply_async(task_id=auction.task_id_update_price)


def run_send_email_winner_task(user_email, lot):
    send_email_winner_task.s(user_email, lot.pk).apply_async()


def run_send_email_outbid_prices_task(user_email, lot):
    send_email_outbid_prices_task.s(user_email, lot.pk).apply_async()


def run_announce_the_winner_task(auction):
    announce_the_winner_task.s(auction.pk).apply_async(task_id=auction.task_id_close_auction,
                                                       eta=auction.end_date)


def send_email_to_user_about_outbidding(lot, current_user):
    user = get_user_by_last_offer(lot)
    if user is not None and user.email != '':
        if user != current_user:
            run_send_email_outbid_prices_task(user.email, lot)

