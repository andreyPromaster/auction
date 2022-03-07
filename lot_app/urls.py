from django.urls import path

from lot_app.views import LotList, LotDetailAuction

urlpatterns = [
    path('lots/', LotList.as_view(), name="lots-list"),
    path('lots/<int:pk>', LotDetailAuction.as_view({'get': 'retrieve'}), name="lot-detail"),
    path('lots/<int:pk>/make_offer',
         LotDetailAuction.as_view({'post': 'create_offer'}), name="lot-make-offer"),
    path('lots/<int:pk>/buy_it_now',
         LotDetailAuction.as_view({'post': 'create_offer_buy_it_now'}), name="lot-buy-now"),
]
