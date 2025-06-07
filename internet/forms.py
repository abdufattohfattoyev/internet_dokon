from django import forms
from .models import Order, OrderItem

class SimpleOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'admin_notes']  # Added admin_notes field
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Izoh qoldiring (ixtiyoriy)'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make admin_notes optional
        self.fields['admin_notes'].required = False

class OrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].choices = [('samarqand', 'Samarqand')]
        self.fields['region'].initial = 'samarqand'
        # Admin notes are not required in the checkout form
        self.fields['admin_notes'].required = False
        self.fields['admin_notes'].widget = forms.HiddenInput()  # Hide in frontend

    class Meta:
        model = Order
        fields = ['first_name', 'phone', 'region', 'city', 'address', 'notes', 'admin_notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }