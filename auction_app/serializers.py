from rest_framework import serializers

from auction_app.models import EnglishAuction, DutchAuction, BaseAuction


class AuctionSerializer(serializers.ModelSerializer):
    auction_data = serializers.SerializerMethodField()

    def get_auction_data(self, obj):
        if hasattr(obj, 'englishauction'):
            return EnglishAuctionSerializer(obj.englishauction).data
        else:
            return DutchAuctionSerializer(obj.dutchauction).data

    class Meta:
        model = BaseAuction
        fields = ['id', 'start_date', 'end_date',
                  'current_price', 'auction_data',
                  'status']


class EnglishAuctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnglishAuction
        fields = ['buy_it_now_price', 'reserved_price']


class DutchAuctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutchAuction
        fields = ['start_price', 'end_price', 'update_price_frequency']
