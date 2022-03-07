from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/update_price', consumers.LotConsumer.as_asgi()),
    path('ws/<int:lot_id>/resent_offer', consumers.OffersConsumer.as_asgi()), 
]
