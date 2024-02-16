# forms.py
from django import forms

class SearchForm(forms.Form):

    SEARCH_CHOICES = [
        ('acno', 'Acno'),
        ('accession', 'Accession'),
        ('cultivar_name', 'Cultivar Name'),
        ('origin_country', 'Origin Country'),
        ('origin_city', 'Origin City'),
        ('origin_province', 'Origin Province'),
        ('pedigree', 'Pedigree'),
        ('genus', 'Genus'),
        ('species', 'Species'),
    ]

    search_attribute = forms.ChoiceField(choices=SEARCH_CHOICES)
    search_term = forms.CharField(max_length=100)


