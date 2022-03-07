from django.contrib import admin

from lot_app.models import Lot, Offer


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    autocomplete_fields = ("item",)
    list_display = ("item", "auction",)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("user", "lot", "offered_price",
                    "creation_datetime")
