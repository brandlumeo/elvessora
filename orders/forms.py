from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class CheckoutForm(forms.Form):
    ONLINE_CHOICE = ('nomod', 'Pay Online — Card, Apple Pay, Google Pay, Tabby or Tamara')
    COD_CHOICE = ('cod', 'Cash on Delivery (UAE)')
    PAYMENT_CHOICES = [ONLINE_CHOICE, COD_CHOICE]

    shipping_name = forms.CharField(max_length=150, label='Full Name')
    shipping_phone = forms.CharField(max_length=20, label='Phone')
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Address')
    shipping_city = forms.CharField(max_length=100, initial='Dubai')
    shipping_state = forms.CharField(max_length=100, label='Emirate', initial='Dubai')
    shipping_pincode = forms.CharField(max_length=10, label='P.O. Box / Area Code')
    shipping_country = forms.CharField(max_length=100, initial='United Arab Emirates')
    coupon_code = forms.CharField(max_length=50, required=False, label='Coupon Code')
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES, widget=forms.RadioSelect)
    guest_email = forms.EmailField(required=False, label='Email (for guest checkout)')
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False, label='Order Notes')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        online_available = kwargs.pop('online_available', True)
        super().__init__(*args, **kwargs)
        if not online_available:
            # No payment gateway configured: only offer Cash on Delivery.
            self.fields['payment_method'].choices = [self.COD_CHOICE]
            self.fields['payment_method'].initial = 'cod'
        if self.user and self.user.is_authenticated:
            self.fields['guest_email'].widget = forms.HiddenInput()
        self.helper = FormHelper()
        self.helper.form_class = 'checkout-form-lux'
        self.helper.add_input(Submit('submit', 'Place Order', css_class='btn btn-gold btn-lg w-100 mt-3'))
