from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class ContactForm(forms.Form):
    ENQUIRY_TYPES = [
        ('general', 'General'),
        ('customer', 'Customer Message'),
        ('wholesale', 'Wholesale Enquiry'),
    ]

    name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    subject = forms.CharField(max_length=200)
    enquiry_type = forms.ChoiceField(choices=ENQUIRY_TYPES, initial='general')
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Send Message', css_class='btn btn-gold'))


class NewsletterForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Enter your email',
        'class': 'form-control',
    }))
