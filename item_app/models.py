from django.db import models


class Item(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    photo = models.ImageField(verbose_name="Photo of item")

    def __str__(self):
        return self.title
