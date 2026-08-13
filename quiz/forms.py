from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML


class QuizForm(forms.Form):
    FRAGRANCE_FAMILIES = [
        ('floral', 'Floral'),
        ('fresh', 'Fresh'),
        ('fruity', 'Fruity'),
        ('oriental', 'Oriental / Amber'),
        ('musk', 'Musk'),
        ('woody', 'Woody'),
        ('citrus', 'Citrus'),
        ('oud', 'Oud'),
        ('aquatic', 'Aquatic'),
        ('spicy', 'Spicy'),
    ]
    GENDER = [
        ('unisex', 'Unisex'),
        ('women', 'Women'),
        ('men', 'Men'),
        ('any', 'No Preference'),
    ]
    OCCASIONS = [
        ('daily', 'Daily Wear'),
        ('office', 'Office'),
        ('date', 'Date Night'),
        ('party', 'Party'),
        ('wedding', 'Wedding'),
        ('special', 'Special Occasions'),
        ('night', 'Evening'),
        ('day', 'Daytime'),
        ('summer', 'Summer'),
        ('winter', 'Winter'),
    ]
    BUDGET = [
        ('low', 'Under AED 100'),
        ('mid', 'AED 100 – AED 125'),
        ('high', 'AED 125 – AED 150'),
        ('premium', 'Above AED 150'),
    ]
    INTENSITY = [
        ('light', 'Light & Subtle'),
        ('moderate', 'Moderate'),
        ('strong', 'Strong & Long-lasting'),
    ]
    TIME = [
        ('day', 'Day Wear'),
        ('night', 'Night Wear'),
        ('both', 'Both'),
    ]

    fragrance_family = forms.ChoiceField(
        choices=FRAGRANCE_FAMILIES,
        label='Preferred Fragrance Family',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    preferred_notes = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. rose, jasmine, amber',
        }),
        label='Preferred Notes (optional)',
    )
    occasion = forms.ChoiceField(
        choices=OCCASIONS,
        label='Occasion',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    gender = forms.ChoiceField(
        choices=GENDER,
        label='Gender Preference',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    budget = forms.ChoiceField(
        choices=BUDGET,
        label='Budget Range',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    intensity = forms.ChoiceField(
        choices=INTENSITY,
        label='Fragrance Intensity',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    time_of_use = forms.ChoiceField(
        choices=TIME,
        label='Day or Night Usage',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('fragrance_family', css_class='col-md-6 mb-3'),
                Column('occasion', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('gender', css_class='col-md-4 mb-3'),
                Column('budget', css_class='col-md-4 mb-3'),
                Column('time_of_use', css_class='col-md-4 mb-3'),
            ),
            Row(
                Column('intensity', css_class='col-md-6 mb-3'),
                Column('preferred_notes', css_class='col-md-6 mb-3'),
            ),
            Submit('submit', 'Find My Perfume', css_class='btn btn-gold w-100 py-3'),
        )
