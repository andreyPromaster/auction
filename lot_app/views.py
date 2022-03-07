import django_filters
from rest_framework import generics, filters, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from auction_app.services.auction_tasks_service import send_email_to_user_about_outbidding
from lot_app.models import Lot
from lot_app.serializers import LotSerializer, OfferSerializer
from rest_framework.pagination import PageNumberPagination

from lot_app.services.make_offer_service import save_auction_offer, buy_now_dutch_lot, \
    buy_now_english_lot
from lot_app.services.process_celery_task import revoke_celery_task
from lot_app.validators import validate_status, validate_offered_price, \
    validate_offered_price_with_buy_now_price, validate_auction_english_type


class LotsResultSerPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data,
            'current_page': self.page.number
        })


class AuctionTypeBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        auction_type = request.query_params.get('auction')
        if auction_type == 'english':
            queryset = queryset.filter(auction__englishauction__isnull=False)
        elif auction_type == 'dutch':
            queryset = queryset.filter(auction__dutchauction__isnull=False)
        return queryset


class LotList(generics.ListCreateAPIView):
    queryset = Lot.objects.all()
    serializer_class = LotSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,
                       django_filters.rest_framework.DjangoFilterBackend,
                       AuctionTypeBackend)
    filterset_fields = ('auction__status', )
    pagination_class = LotsResultSerPagination
    search_fields = ['item__title']
    ordering_fields = ['auction__end_date', 'auction__current_price']


class LotDetailAuction(viewsets.ModelViewSet):
    """Get detail about auction: Item and certain auction.
    def create_offer allows make offer for definite lot"""

    queryset = Lot.objects.all()
    serializer_class = LotSerializer

    @action(detail=True)
    def create_offer(self, request, pk=None):
        lot = self.get_object()
        serializer = OfferSerializer(data=request.data)
        if serializer.is_valid():
            validate_auction_english_type(lot)
            validate_status(lot)
            validate_offered_price(lot, serializer.validated_data['offered_price'])
            send_email_to_user_about_outbidding(lot, request.user)
            save_auction_offer(lot, serializer.validated_data['offered_price'],
                               request.user)
            return Response({'status': 'offer was created'},
                            status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True)
    def create_offer_buy_it_now(self, request, pk=None):
        lot = self.get_object()
        validate_status(lot)
        if hasattr(lot.auction, 'englishauction'):
            validate_offered_price_with_buy_now_price(lot)
            buy_now_english_lot(lot, request.user)
        else:
            buy_now_dutch_lot(lot, request.user)
            revoke_celery_task(lot.auction.dutchauction.task_id_update_price) # revoke close auction task and
            # announce_the_winner_task
        revoke_celery_task(lot.auction.task_id_close_auction)
        return Response({'status': 'offer was created'},
                        status=status.HTTP_201_CREATED)
