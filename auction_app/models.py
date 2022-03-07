from django.core import validators
from django.db import models


class CurrencyField(models.DecimalField):
    """This field will be used as the default to
    define currency."""

    MAX_DIGITS = 10
    DECIMAL_PLACES = 2
    MIN_PRICE = 0

    def __init__(self, max_digits=None, decimal_places=None, *args, **kwargs):
        super(CurrencyField, self).__init__(*args, **kwargs)
        self.validators = [validators.MinValueValidator(CurrencyField.MIN_PRICE)]
        if max_digits is None or decimal_places is None:
            self.max_digits = CurrencyField.MAX_DIGITS
            self.decimal_places = CurrencyField.DECIMAL_PLACES
        else:
            self.max_digits = max_digits
            self.decimal_places = decimal_places


class BaseAuction(models.Model):
    start_date = models.DateTimeField(verbose_name="Start auction")
    end_date = models.DateTimeField(verbose_name="End auction")
    current_price = CurrencyField()

    class LotStatus(models.IntegerChoices):
        PENDING = 0
        IN_PROGRESS = 1
        COMPLETED = 2

    status = models.SmallIntegerField(choices=LotStatus.choices,
                                      default=LotStatus.PENDING)

    def __str__(self):
        return f"{self.start_date.strftime('%Y-%m-%d-%H.%M')} " \
               f" - {self.end_date.strftime('%Y-%m-%d-%H.%M')}"

    @property
    def task_id_close_auction(self):
        return f'close_auction-{self.pk}'


class EnglishAuction(BaseAuction):
    buy_it_now_price = CurrencyField(verbose_name="Buy now price")
    reserved_price = CurrencyField(verbose_name="Reserved price")

    def __str__(self):
        return f"English {super().__str__()}"


class DutchAuction(BaseAuction):
    start_price = CurrencyField()
    end_price = CurrencyField()
    update_price_frequency = models.PositiveSmallIntegerField(verbose_name="Frequency to reduce",
                                                              help_text="Update_price_frequency "
                                                                        "means that how mane time"
                                                                        " price will be updated")

    def __str__(self):
        return f"Dutch {super().__str__()}"

    @property
    def task_id_update_price(self):
        return f"update_price-{self.pk}"

    @property
    def price_step(self):
        return (self.start_price - self.end_price) / self.update_price_frequency

    @property
    def time_step(self):
        return (self.end_date - self.start_date) / (self.update_price_frequency + 1)
