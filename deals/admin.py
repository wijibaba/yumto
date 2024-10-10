from django.contrib import admin
from .models import Deal


class DealAdmin(admin.ModelAdmin):
    list_display = ('id', 'deal_type', 'deal_name', 'price_range', 'image')  # Display these fields in the admin list view
    search_fields = ('deal_name', 'deal_type')  # Add search functionality by deal name and type
    list_filter = ('deal_type',)  # Filter deals by deal type

# Register the Deal model with the admin site using the custom DealAdmin class
admin.site.register(Deal, DealAdmin)
