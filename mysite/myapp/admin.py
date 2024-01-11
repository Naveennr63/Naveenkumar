from django.contrib import admin
from .models import Product,OrderDetails
# Register your models here.

admin.site.register(Product)
admin.site.register(OrderDetails)