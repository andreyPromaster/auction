from django.contrib import admin

from item_app.models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "photo")
    list_filter = ("title", )
    search_fields = ("title", "description")

