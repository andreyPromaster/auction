import tempfile
from collections import OrderedDict
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from auction_app.models import EnglishAuction, BaseAuction, DutchAuction
from auction_app.services.auction_tasks_service import send_email_to_user_about_outbidding
from auction_app.services.offers_service import change_price_in_dutch_auction
from item_app.models import Item
from lot_app.models import Lot, Offer
from lot_app.services.make_offer_service import buy_now_dutch_lot, save_auction_offer, buy_now_english_lot
from lot_app.services.web_socket_service import get_recent_lots_offers

User = get_user_model()


def create_lot_in_english_auction(auction_status=BaseAuction.LotStatus.IN_PROGRESS):
    item = Item.objects.create(title="test", description="test-description", photo="test.png")
    import datetime
    time_and_date = datetime.datetime(day=1, month=1, year=2022, hour=1)
    auction = EnglishAuction.objects.create(start_date=time_and_date, end_date=time_and_date + datetime.timedelta(days=1),
                                  current_price="10.00", buy_it_now_price="30.00", status=auction_status,
                                  reserved_price="20.00")
    lot = Lot.objects.create(auction=auction, item=item)
    return lot


def create_lot_in_dutch_auction(auction_status=BaseAuction.LotStatus.IN_PROGRESS):
    item = Item.objects.create(title="test_dutch", description="test_dutch_description", photo="test.png")
    import datetime
    time_and_date = datetime.datetime(day=1, month=1, year=2022, hour=1)
    auction = DutchAuction.objects.create(start_date=time_and_date, end_date=time_and_date + datetime.timedelta(days=1),
                                  current_price="20.00", status=auction_status,
                                  start_price="20.00", end_price="5.00",
                                update_price_frequency=2)
    lot = Lot.objects.create(auction=auction, item=item)
    return lot


class AuctionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@mail.com', 'testingpassword')

        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()

    def test_token_obtain_successful(self):
        url = reverse('api_token_auth')
        data = {'username': self.user.username, "password": "testingpassword"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Token.objects.count(), 1)
        self.assertEqual(Token.objects.get(user__username=self.user.username).key, response.data["token"])

    def test_token_obtain_failed(self):
        url = reverse('api_token_auth')
        data = {'username': self.user.username, "password": "failed_password"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_lot_list(self):
        url = reverse('lots-list')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(f"{url}?page=1&page_size=10", format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'next': None, 'previous': None, 'count': 0, 'results': [], 'current_page': 1})

    def test_lot_list(self):
        lot = create_lot_in_english_auction()
        url = reverse('lots-list')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(f"{url}?page=1&page_size=10", format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["item"]["title"], lot.item.title)
        self.assertEqual(response.data["results"][0]["item"]["description"], lot.item.description)
        self.assertEqual(response.data["results"][0]["auction"]["start_date"], '2022-01-01T01:00:00+03:00')
        self.assertEqual(response.data["results"][0]["auction"]["current_price"], '10.00')

        self.assertEqual(response.data["count"], 1)
        self.assertIsNone(response.data["previous"])
        self.assertIsNone(response.data["next"])

    def test_lot_failed_auth(self):
        url = reverse('lots-list')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + "failed-token")
        response = self.client.get(f"{url}?page=1&page_size=10", format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lot_detail(self):
        lot = create_lot_in_english_auction()
        url = reverse("lot-detail", args=[lot.id])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], lot.id)
        self.assertEqual(response.data["item"]["title"], lot.item.title)
        self.assertEqual(response.data["item"]["description"], lot.item.description)
        self.assertEqual(response.data["auction"]["current_price"], lot.auction.current_price)
        self.assertEqual(response.data["auction"]["auction_data"]["buy_it_now_price"], str(lot.auction.englishauction.buy_it_now_price))
        self.assertEqual(response.data["auction"]["auction_data"]["reserved_price"], str(lot.auction.englishauction.reserved_price))

    def test_make_offer(self):
        lot = create_lot_in_english_auction()
        url = reverse("lot-make-offer", args=[lot.id])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {"offered_price": "15.00"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'status': 'offer was created'})

    def test_make_offer_offered_price_failed(self):
        lot = create_lot_in_english_auction()
        url = reverse("lot-make-offer", args=[lot.id])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {"offered_price": "9.00"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0], "Offered_price must be more than current price")

    def test_make_offer_status_failed(self):
        lot = create_lot_in_english_auction(auction_status=BaseAuction.LotStatus.PENDING)
        url = reverse("lot-make-offer", args=[lot.id])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {"offered_price": "12.00"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0], "Status not in progress")

    def test_buy_it_now_lot_failed_status(self):
        lot = create_lot_in_english_auction(auction_status=BaseAuction.LotStatus.PENDING)
        url = reverse("lot-buy-now", args=[lot.id])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0], "Status not in progress")

    def test_buy_it_now_lot(self):
        lot = create_lot_in_english_auction()
        url = reverse("lot-buy-now", args=[lot.id])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'status': 'offer was created'})

    def test_buy_it_now_lot_for_dutch_auction(self):
        lot = create_lot_in_dutch_auction()
        url = reverse("lot-buy-now", args=[lot.id])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'status': 'offer was created'})

    def test_buy_it_now_lot_failed_price(self):
        lot = create_lot_in_english_auction()
        lot.auction.current_price = "40.00"
        lot.auction.save()
        url = reverse("lot-buy-now", args=[lot.id])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0], 'Buy now price less than current price')

    def test_make_offer_lot_for_dutch_auction(self):
        lot = create_lot_in_dutch_auction()
        url = reverse("lot-make-offer", args=[lot.id])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, {"offered_price": "50.00"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0], "Invalid type of auction")

    def test_get_recent_lots_offers(self):
        lot = create_lot_in_english_auction()
        for price in range(11, 18):
            Offer.objects.create(lot=lot, user=self.user, offered_price=price)
        offers = get_recent_lots_offers(lot)
        self.assertEqual(offers, [{"test":Decimal("17.00")}, {"test":Decimal("16.00")}, {"test":Decimal("15.00")}, {"test":Decimal("14.00")}, {"test":Decimal("13.00")}])

    def test_get_recent_lots_offers_with_different_users(self):
        lot = create_lot_in_english_auction()
        for price in range(11, 18):
            Offer.objects.create(lot=lot, user=self.user, offered_price=price)
        new_user = User.objects.create_user('test1', 'test@mail.com', 'testingpassword')
        Offer.objects.create(lot=lot, user=new_user, offered_price="18.00")
        offers = get_recent_lots_offers(lot)
        self.assertEqual(offers, [{"test1":Decimal("18.00")}, {"test":Decimal("17.00")}, {"test":Decimal("16.00")}, {"test":Decimal("15.00")}, {"test":Decimal("14.00")},])

    def test_get_recent_lots_less_than_5_users(self):
        lot = create_lot_in_english_auction()
        for price in range(15, 19):
            Offer.objects.create(lot=lot, user=self.user, offered_price=price)
        offers = get_recent_lots_offers(lot)
        self.assertEqual(offers, [{"test":Decimal("18.00")}, {"test":Decimal("17.00")}, {"test":Decimal("16.00")}, {"test":Decimal("15.00")},])

    def test_lot_list_filter_by_english_auction(self):
        english_lot = create_lot_in_english_auction()
        dutch_lot = create_lot_in_dutch_auction()
        url = reverse('lots-list')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(f"{url}?page=1&page_size=10&auction=english", format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["item"]["title"], english_lot.item.title)
        self.assertEqual(response.data["results"][0]["item"]["description"], english_lot.item.description)
        self.assertEqual(response.data["results"][0]["auction"]["start_date"], '2022-01-01T01:00:00+03:00')
        self.assertEqual(response.data["results"][0]["auction"]["current_price"], '10.00')

        self.assertEqual(response.data["count"], 1)
        self.assertIsNone(response.data["previous"])
        self.assertIsNone(response.data["next"])

    def test_lot_list_filter_by_dutch_auction(self):
        english_lot = create_lot_in_english_auction()
        dutch_lot = create_lot_in_dutch_auction()
        url = reverse('lots-list')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(f"{url}?page=1&page_size=10&auction=dutch", format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["results"][0]["item"]["title"], dutch_lot.item.title)
        self.assertEqual(response.data["results"][0]["item"]["description"], dutch_lot.item.description)
        self.assertEqual(response.data["results"][0]["auction"]["start_date"], '2022-01-01T01:00:00+03:00')
        self.assertEqual(response.data["results"][0]["auction"]["current_price"], '20.00')

        self.assertEqual(response.data["count"], 1)
        self.assertIsNone(response.data["previous"])
        self.assertIsNone(response.data["next"])

    def test_lot_list_filter_by_unknown_auction(self):
        english_lot = create_lot_in_english_auction()
        dutch_lot = create_lot_in_dutch_auction()
        url = reverse('lots-list')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(f"{url}?page=1&page_size=10&auction=unknown", format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["count"], 2)
        self.assertIsNone(response.data["previous"])
        self.assertIsNone(response.data["next"])

    @patch("auction_app.services.auction_tasks_service.run_send_email_outbid_prices_task")
    def test_send_email_user_about_outbidding(self, mock_send_email):
        mock_send_email.return_value = MagicMock()

        lot = create_lot_in_english_auction()
        new_user = User.objects.create_user('test1', 'test1@mail.com', 'testingpassword')
        Offer.objects.create(lot=lot, user=new_user, offered_price="18.00")

        url = reverse("lot-make-offer", args=[lot.id])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {"offered_price": "20.00"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'status': 'offer was created'})
        mock_send_email.assert_called_once_with(new_user.email, lot)

    @patch("auction_app.services.auction_tasks_service.run_send_email_outbid_prices_task")
    def test_send_email_to_user_about_outbidding(self, mock_send_email):
        mock_send_email.return_value = MagicMock()

        lot = create_lot_in_english_auction()
        new_user = User.objects.create_user('test1', 'test1@mail.com', 'testingpassword')
        Offer.objects.create(lot=lot, user=new_user, offered_price="18.00")
        send_email_to_user_about_outbidding(lot, self.user)
        mock_send_email.assert_called_once_with(new_user.email, lot)

    @patch("auction_app.services.auction_tasks_service.run_send_email_outbid_prices_task")
    def test_send_email_to_user_about_outbidding_without_email(self, mock_send_email):
        mock_send_email.return_value = MagicMock()

        lot = create_lot_in_english_auction()
        new_user = User.objects.create_user('test1', '', 'testingpassword')
        Offer.objects.create(lot=lot, user=new_user, offered_price="18.00")
        send_email_to_user_about_outbidding(lot, self.user)
        mock_send_email.assert_not_called()

    @patch("auction_app.services.auction_tasks_service.run_send_email_outbid_prices_task")
    def test_send_email_to_user_about_outbidding_the_same_user(self, mock_send_email):
        mock_send_email.return_value = MagicMock()

        lot = create_lot_in_english_auction()
        Offer.objects.create(lot=lot, user=self.user, offered_price="18.00")
        send_email_to_user_about_outbidding(lot, self.user)
        mock_send_email.assert_not_called()

    @patch("auction_app.services.offers_service.send_event_about_updating_price")
    def test_change_price_in_dutch_auction(self, mock_service):
        mock_service.return_value = MagicMock()

        lot = create_lot_in_dutch_auction()
        change_price_in_dutch_auction(lot.auction.dutchauction)
        self.assertEqual(lot.auction.dutchauction.current_price, Decimal("12.50"))
        self.assertEqual(lot.auction.dutchauction.price_step, Decimal("7.50"))
        mock_service.assert_called_once()

    def test_buy_now_dutch_lot(self):
        lot = create_lot_in_dutch_auction()
        buy_now_dutch_lot(lot, self.user)
        self.assertEqual(lot.auction.status, BaseAuction.LotStatus.COMPLETED)
        offer = Offer.objects.get(user=self.user, lot=lot)
        self.assertEqual(offer.offered_price, Decimal(lot.auction.current_price))

    def test_save_auction_offer(self):
        lot = create_lot_in_english_auction()
        save_auction_offer(lot, "20.00", self.user)
        offer = Offer.objects.get(user=self.user, lot=lot)
        self.assertEqual(lot.auction.current_price, "20.00")
        self.assertEqual(offer.offered_price, Decimal("20.00"))

    @patch("lot_app.services.make_offer_service.send_event_about_updating_price")
    @patch("lot_app.services.make_offer_service.send_resent_lots_offers")
    def test_buy_now_english_lot(self, mock_event_service, mock_recent_offers):
        mock_event_service.return_value = MagicMock()
        mock_recent_offers.return_value = MagicMock()

        lot = create_lot_in_english_auction()
        buy_now_english_lot(lot, self.user)
        offer = Offer.objects.get(user=self.user, lot=lot)
        self.assertEqual(lot.auction.current_price, lot.auction.englishauction.buy_it_now_price)
        self.assertEqual(offer.offered_price, lot.auction.englishauction.buy_it_now_price)
        self.assertEqual(lot.auction.status, BaseAuction.LotStatus.COMPLETED)

        mock_event_service.assert_called_once()
        mock_recent_offers.assert_called_once()