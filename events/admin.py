from django.contrib import admin
from . models import Event,EventAggregate
# Register your models here.

admin.site.register(Event)
admin.site.register(EventAggregate)
