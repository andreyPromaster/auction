from django.contrib import admin
from django.db import transaction

from auction_app.models import EnglishAuction, DutchAuction
from auction_app.services.auction_tasks_service import run_start_auction_task, \
    run_finish_auction_task, run_update_dutch_auction_price_task, run_announce_the_winner_task
from lot_app.models import Lot


class LotInline(admin.TabularInline):
    model = Lot
    search_fields = ("title",)
    autocomplete_fields = ("item",)


@admin.register(EnglishAuction)
class EnglishAuctionAdmin(admin.ModelAdmin):
    inlines = [LotInline]
    list_display = ("start_date", "end_date", "current_price",
                    "buy_it_now_price", "reserved_price", "status",)
    list_editable = ("current_price", "buy_it_now_price",
                     "reserved_price", "status",)
    search_fields = ("current_price", "start_date", "end_date",)
    list_filter = ("start_date", "end_date", "current_price",
                   "status",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        transaction.on_commit(lambda: run_start_auction_task(obj))
        transaction.on_commit(lambda: run_announce_the_winner_task(obj))
        transaction.on_commit(lambda: run_finish_auction_task(obj))


@admin.register(DutchAuction)
class DutchAuctionAdmin(admin.ModelAdmin):
    inlines = [LotInline]
    list_display = ("start_date", "end_date", "current_price",
                    "start_price", "end_price", "update_price_frequency",
                    "view_price_step", "view_time_step", "status",
                    )
    list_editable = ("current_price", "start_price", "end_price",
                     "update_price_frequency", "status",)
    search_fields = ("current_price", "start_date", "end_date",)
    list_filter = ("start_date", "end_date", "current_price",
                   "status",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        transaction.on_commit(lambda: run_start_auction_task(obj))
        transaction.on_commit(lambda: run_update_dutch_auction_price_task(obj))
        transaction.on_commit(lambda: run_finish_auction_task(obj))

    def view_price_step(self, obj):
        return obj.price_step

    def view_time_step(self, obj):
        return obj.time_step
