from django import forms
from .models import Address
import requests


def verify_zip_code_with_api(zip_code, country):
    # Verifying the zip code using Zippopotam API
    if country == 'USA':
        url = f"http://api.zippopotam.us/us/{zip_code}"
    elif country == 'Canada':
        url = f"http://api.zippopotam.us/ca/{zip_code}"
    elif country == 'Pakistan':
        url = f"http://api.zippopotam.us/pk/{zip_code}"
    else:
        return False

    response = requests.get(url)

    if response.status_code == 200:
        # Extract data from the response and return for further validation
        data = response.json()
        return {
            'postal_code': data.get('post code'),
            'country': data.get('country'),
            'state': data['places'][0].get('state'),
            'place_name': data['places'][0].get('place name'),
        }
    return False


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['country', 'state', 'city', 'zip_code', 'street_address']

    def clean_zip_code(self):
        zip_code = self.cleaned_data.get('zip_code')
        country = self.cleaned_data.get('country')
        state = self.cleaned_data.get('state')
        city = self.cleaned_data.get('city')

        # Call the external API to verify the ZIP code
        result = verify_zip_code_with_api(zip_code, country)
        if result:
            # Print the returned result for debugging
            print("API Result:", result)
        if result:
            if result['postal_code'] != zip_code or result['state'] != state or result['place_name'] != city:
                raise forms.ValidationError("The entered ZIP code does not match the provided location.")
        else:
            raise forms.ValidationError("Enter a correct ZIP code for the selected country.")
        return zip_code
