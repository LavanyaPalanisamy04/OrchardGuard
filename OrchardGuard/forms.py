# forms.py
from django import forms

class SearchForm(forms.Form):
    acno = forms.CharField(label='Acno', max_length=100, required=False)
    accession = forms.CharField(label='Accession', max_length=100,required=False)
    cultivar_name = forms.CharField(label='Cultivar Name', max_length=100,required=False)
    origin_country = forms.CharField(label='Origin Country', max_length=100,required=False)
    origin_city = forms.CharField(label='Origin City', max_length=100,required=False)
    origin_province = forms.CharField(label='Origin Province', max_length=100,required=False)
    e_pedigree = forms.CharField(label='Pedigree', max_length=100,required=False)
    e_genus = forms.CharField(label='Genus', max_length=100,required=False)
    e_species = forms.CharField(label='Species', max_length=100,required=False)

class ListSearchForm(forms.Form):
    acnos = forms.CharField(label='Comma separated Acnos', max_length=100, required=True)





class AnySearchForm(forms.Form):
    input = forms.CharField(label='Anything to search for', max_length=100, required=True)


class ImageUploadForm(forms.Form):
    image = forms.ImageField()


class LoginForm(forms.Form):
    username_or_email = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


