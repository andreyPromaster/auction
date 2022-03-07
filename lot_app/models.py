from django.db import models

from auction_app.models import BaseAuction, CurrencyField
from item_app.models import Item
from django.contrib.auth import get_user_model
User = get_user_model()


class Lot(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="lot")
    auction = models.OneToOneField(BaseAuction, on_delete=models.CASCADE, related_name="lot")


class Offer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE)
    offered_price = CurrencyField()
    creation_datetime = models.DateTimeField(auto_now_add=True)
