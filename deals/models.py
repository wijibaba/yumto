
from django.db import models
from django.contrib.auth.models import User


class Deal(models.Model):
    id = models.CharField(max_length=50, primary_key=True)  # Assuming 'id' is the primary key in your existing table
    image = models.URLField(max_length=255)
    deal_type = models.CharField(max_length=50)
    deal_name = models.CharField(max_length=255)
    price_range = models.CharField(max_length=255)

    class Meta:
        db_table = 'deals'


class Comment(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(default="No comment")  # This is the 'comment' field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.comment[:50]


class Address(models.Model):
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    street_address = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state}, {self.country}, {self.zip_code}"

