from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column
from .models import Address, UserProfile


def _style_auth_fields(form):
    for name, field in form.fields.items():
        if isinstance(field.widget, (forms.HiddenInput, forms.CheckboxInput)):
            continue
        css = field.widget.attrs.get('class', '')
        field.widget.attrs['class'] = f'{css} form-control'.strip()
        if name in ('username', 'email'):
            field.widget.attrs.setdefault('placeholder', field.label or name.title())


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    phone = forms.CharField(max_length=20, required=False, label='Phone (optional)')
    email_notifications = forms.BooleanField(
        required=False, initial=True, label='Email me about my orders and account'
    )
    whatsapp_notifications = forms.BooleanField(
        required=False, initial=False, label='Send order updates to my WhatsApp'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_auth_fields(self)
        self.fields['password1'].help_text = 'Use at least 8 characters with letters and numbers.'
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.layout = Layout(
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            'username', 'email', 'phone',
            'password1', 'password2',
            'email_notifications', 'whatsapp_notifications',
            Submit('submit', 'Create Account', css_class='btn btn-gold'),
        )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('whatsapp_notifications') and not cleaned_data.get('phone'):
            self.add_error('phone', 'Add a phone number to receive WhatsApp updates.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            user.profile.phone = self.cleaned_data.get('phone', '')
            user.profile.email_notifications = self.cleaned_data.get('email_notifications', True)
            user.profile.whatsapp_notifications = self.cleaned_data.get('whatsapp_notifications', False)
            user.profile.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        next_url = kwargs.pop('next_url', '')
        super().__init__(*args, **kwargs)
        _style_auth_fields(self)
        if next_url:
            self.fields['next'] = forms.CharField(
                widget=forms.HiddenInput(), initial=next_url, required=False
            )
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Sign In', css_class='btn btn-gold'))


class ElvessoraPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Enter your account email',
            'class': 'form-control',
        })
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Send Reset Link', css_class='btn btn-gold'))


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()

    class Meta:
        model = UserProfile
        fields = [
            'phone', 'date_of_birth', 'newsletter_subscribed',
            'email_notifications', 'whatsapp_notifications',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['first_name'].initial = self.user.first_name
        self.fields['last_name'].initial = self.user.last_name
        self.fields['email'].initial = self.user.email
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Update Profile', css_class='btn btn-gold'))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('whatsapp_notifications') and not cleaned_data.get('phone'):
            self.add_error('phone', 'Add a phone number to receive WhatsApp updates.')
        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        self.user.save()
        if commit:
            profile.save()
        return profile


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'address_type', 'full_name', 'phone', 'address_line1', 'address_line2',
            'city', 'state', 'pincode', 'country', 'is_default',
        ]
        widgets = {
            'address_line1': forms.TextInput(attrs={'placeholder': 'House No., Street'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Landmark (optional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Save Address', css_class='btn btn-gold'))
