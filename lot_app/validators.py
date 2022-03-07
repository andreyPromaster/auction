from rest_framework import serializers

from auction_app.models import BaseAuction


def validate_status(lot):
    if lot.auction.status != BaseAuction.LotStatus.IN_PROGRESS:
        raise serializers.ValidationError('Status not in progress')


def validate_offered_price(lot, offered_price):
    if lot.auction.current_price >= offered_price:
        raise serializers.ValidationError('Offered_price must be more than current price')


def validate_offered_price_with_buy_now_price(lot):
    if lot.auction.current_price > lot.auction.englishauction.buy_it_now_price:
        raise serializers.ValidationError('Buy now price less than current price')


def validate_auction_english_type(lot):
    if not hasattr(lot.auction, 'englishauction'):
        raise serializers.ValidationError('Invalid type of auction')
