from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    ''' Form for the user to enter their details for an order'''
    class Meta:
        model = Order
        fields = (
            'full_name',
            'email',
            'phone_number',
            'country',
            'town_or_city',
            'street_address1',
            'street_address2',
            'county',
            'pickup_time')

    def __init__(self, *args, **kwargs):
        ''' Add placeholders, remove auto-generated
             labels and autofocus on field'''
        super().__init__(*args, **kwargs)
        placeholders = {
            'full_name': 'Full Name',
            'email': 'Email',
            'phone_number': 'Phone Number',
            'town_or_city': 'Town or City',
            'street_address1': 'Street Address 1',
            'street_address2': 'Street Address 2',
            'county': 'County, State or Locality',
            'pickup_time': 'Pickup Time',
        }

        self.fields['full_name'].widget.attrs['autofocus'] = True
        for field in self.fields:
            if field != 'country':
                if self.fields[field].required:
                    placeholder = f'{placeholders[field]} *'
                else:
                    placeholder = placeholders[field]
                self.fields[field].widget.attrs['placeholder'] = placeholder
            self.fields[field].widget.attrs['class'] = 'stripe-style-input'
            self.fields[field].label = False


class CheckoutForm(forms.Form):
    ''' Form for the user to enter their details for an order'''
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    address = forms.CharField(max_length=100)
    city = forms.CharField(max_length=50)
    country = forms.CharField(max_length=50)
    save_info = forms.BooleanField(required=False)
