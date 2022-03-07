from rest_framework import serializers
from auction_app.serializers import AuctionSerializer
from item_app.serializers import ItemSerializer
from lot_app.models import Lot, Offer


class LotSerializer(serializers.ModelSerializer):
    item = ItemSerializer()
    auction = AuctionSerializer()

    class Meta:
        model = Lot
        fields = '__all__'


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = ['offered_price']

