from django.core.mail import send_mail

from auction import settings


def send_email_about_winner(user_email, lot):
    send_mail(
        'Auction winner',
        f'You are a winner in auction: {lot.item.title}',
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False,
    )


def send_email_about_outbid(user_email, lot):
    send_mail(
        'Outbid the prices',
        f'Someone has outbid your bid price in auction: {lot.item.title}',
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False,
    )


def send_email_about_rejected_auction(user_email, lot):
    send_mail(
        'Result auction',
        f'You may have been a winner if your offer had been bigger '
        f'than reserved price:( Lot - {lot.item.title}',
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False,
    )
