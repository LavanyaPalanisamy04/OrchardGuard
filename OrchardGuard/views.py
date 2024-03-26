import csv
import json
from .forms import FeedbackForm, SearchForm, ListSearchForm, AnySearchForm, ImageUploadForm, LoginForm, RegistrationForm
from django.contrib.auth import logout
from OrchardGuard.dynamodb import insert_item_into_dynamodb, insert_data_into_dynamodb, query, query_by_partition_key, \
    scan_table
from elasticsearch import Elasticsearch
import firebase_admin
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from firebase_admin import auth, credentials,db
import re
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse

# Define Elasticsearch client
es = Elasticsearch(hosts=['https://search-orchard-guard-ow7eqo2vkmw47bwlnbasc6a2ce.us-east-2.es.amazonaws.com'],
                   http_auth=('Lavanya', 'Orchardguard@04'),
                   headers={"Content-Type": "application/json"}
                   )

cred = credentials.Certificate('D:\\pycharmproject\\djangoProject\\OrchardGuard\\security_key.json')
default_app = firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://apple-disease-detection-ab165-default-rtdb.firebaseio.com/'
})


def insert_item_view(request):
    """
    View to insert an item into DynamoDB.
    """
    # Replace 'your-table-name' with the name of your DynamoDB table
    # table_name = 'your-table-name'

    # Replace with the item you want to insert
    item_to_insert = {
        'acno': {'S': '123'},
        'name': {'S': 'John'}
    }

    # Insert the item into DynamoDB
    success = insert_item_into_dynamodb(item_to_insert)

    if success:
        return JsonResponse({'status': 'Item inserted successfully'})
    else:
        return JsonResponse({'status': 'Failed to insert item'})

def convert_value(value, datatype):
    """Converts a value to the specified datatype."""
    if datatype == 'N':
        # DynamoDB expects numbers to be in string format
        return str(int(value)) if value.isdigit() else str(float(value))
    # For simplicity, return all other datatypes as strings
    return value

def load_excel(request):
    """
    View to insert an item into DynamoDB.
    """
    # Replace 'your-table-name' with the name of your DynamoDB table
    # table_name = 'your-table-name'

    # Replace with the item you want to insert
    with open('OrchardGuard/TDInventory.csv', 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        data = []
        for row in reader:
            row['acno'] = int(row['acno'])
            data.append(row)

    response = insert_data_into_dynamodb(data)


    if response:
        return JsonResponse({'status': 'data loaded successfully'})
    else:
        return JsonResponse({'status': 'Failed to load data'})


def index_documents_opensearch(request):
    with open('OrchardGuard/AppleAccessions.json', 'r') as file:
        json_data = json.load(file)

    # Prepare bulk indexing request
    bulk_request = ''
    index_name = 'accessions'

    for document in json_data:
        # Add metadata line
        bulk_request += json.dumps({"index": {"_index": index_name}}) + '\n'
        # Add JSON document
        bulk_request += json.dumps(document) + '\n'

    # Send bulk indexing request
    url = 'https://search-orchard-guard-ow7eqo2vkmw47bwlnbasc6a2ce.us-east-2.es.amazonaws.com/_bulk'
    headers = {'Content-Type': 'application/json'}
    auth = ("Lavanya", "Orchardguard@04")
    response = requests.post(url, auth=auth, headers=headers, data=bulk_request)

    # Check response status
    if response.status_code == 200:
        print("Documents indexed successfully!")
    else:
        print("Failed to index documents:", response.text)


def search(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():

            # Map form field names to DynamoDB attribute names
            attribute_mapping = {
                'pedigree': 'e_pedigree',
                'genus': 'e_genus',
                'species': 'e_species'
            }

            # Construct filter expression, attribute names, and values
            filter_expression_parts = []
            expression_attribute_names = {}
            expression_attribute_values = {}
            for field, value in form.cleaned_data.items():
                if value:
                    db_field = attribute_mapping.get(field, field)
                    if field == 'acno':
                        filter_expression_parts.append("#acno = :acno")
                        expression_attribute_names['#acno'] = 'acno'
                        expression_attribute_values[':acno'] = int(value)
                    else:
                        filter_expression_parts.append(f"#{db_field} = :{field}")
                        expression_attribute_names[f"#{db_field}"] = db_field
                        expression_attribute_values[f":{field}"] = value

            # Join filter expression parts
            filter_expression = ' AND '.join(filter_expression_parts)

            # Query the DynamoDB table
            response = scan_table(filter_expression,expression_attribute_names,expression_attribute_values)

            # Process search results
            items = response['Items']

            # Render the search results in the template
            return render(request, 'OrchardGuard/search_results.html', {'results': items})
    else:
        form = SearchForm()
    return render(request, 'OrchardGuard/search.html', {'form': form})

def list_search(request):
    if request.method == 'POST':
        form = ListSearchForm(request.POST)
        if form.is_valid():

            acnos = form.cleaned_data['acnos']

            # Now you can process the acnos data as needed
            query = {
                "query": {
                    "terms": {
                        "acno": [int(acno.strip()) for acno in acnos.split(',')]
                    }
                }
            }
            # acno_list = [int(acno.strip()) for acno in acnos.split(',')]
            # query["query"]["terms"]["acno"].append(acno_list)
            response = requests.post(
                'https://search-orchard-guard-ow7eqo2vkmw47bwlnbasc6a2ce.us-east-2.es.amazonaws.com/_search',
                auth=('Lavanya', 'Orchardguard@04'),
                json=query)

            print(query)

            # Extract search results
            items = []
            for record in response.json()['hits']['hits']:
                items.append(record['_source'])

            print("items ", items)
            return render(request, 'OrchardGuard/search_results.html', {'items': items})
    else:
        form = ListSearchForm()
    return render(request, 'OrchardGuard/search.html', {'form': form})


def any_search(request):
    if request.method == 'POST':
        form = AnySearchForm(request.POST)
        if form.is_valid():

            input = form.cleaned_data['input']

            # Now you can process the acnos data as needed
            query = {
                "query": {
                    "query_string": {
                        "query": input
                    }
                }
            }
            response = requests.post(
                'https://search-orchard-guard-ow7eqo2vkmw47bwlnbasc6a2ce.us-east-2.es.amazonaws.com/_search',
                auth=('Lavanya', 'Orchardguard@04'),
                json=query)

            print(query)

            # Extract search results
            items = []
            for record in response.json()['hits']['hits']:
                items.append(record['_source'])

            print("items ", items)
            return render(request, 'OrchardGuard/search_results.html', {'items': items})
    else:
        form = AnySearchForm()
    return render(request, 'OrchardGuard/search.html', {'form': form})




def elastic_search(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            # Construct Elasticsearch query based on form data
            query = {
                "query": {
                    "bool": {
                        "must": []
                    }
                }
            }

            # Add search terms from the form fields
            for field, value in form.cleaned_data.items():
                if value:
                    query["query"]["bool"]["must"].append({"match": {field: value}})

                    # Make a POST request to Elasticsearch
            response = requests.post(
                'https://search-orchard-guard-ow7eqo2vkmw47bwlnbasc6a2ce.us-east-2.es.amazonaws.com/_search',
                auth=('Lavanya', 'Orchardguard@04'),
                json=query)

            # Extract search results
            items = []
            for record in response.json()['hits']['hits']:
                items.append(record['_source'])

            print("items ",items)

            # Render the search results in the template
            return render(request, 'OrchardGuard/search_results.html', {'items': items})
    else:
        form = SearchForm()
    return render(request, 'OrchardGuard/search.html', {'form': form})



def upload_and_predict(request):
    if request.method == 'POST':
        if 'image_file' not in request.FILES:
            return JsonResponse({'error': 'No image file provided.'}, status=400)

        image_file = request.FILES['image_file']
        temp_image = default_storage.save("temp_image", ContentFile(image_file.read()))
        temp_image_path = default_storage.path(temp_image)

        try:
            with open(temp_image_path, 'rb') as file:
                fastapi_url = 'http://localhost:8081/prediction'
                response = requests.post(fastapi_url, files={'file': file})

            # Ensure you delete the temp file after closing it
            default_storage.delete(temp_image)

            if response.status_code == 200:
                prediction = response.json()
                return JsonResponse({
                    'class': prediction.get('class', 'N/A'),
                    'confidence': prediction.get('confidence', 0)
                })
            else:
                return JsonResponse({'error': 'Failed to get prediction from FastAPI.'}, status=response.status_code)
        except Exception as e:
            # If an error occurs, delete the temp file
            default_storage.delete(temp_image)
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return render(request, 'OrchardGuard/image_recognition.html')




def homepage(request):
    return render(request, 'OrchardGuard/homepage.html')

def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('feedback_success')  # Redirect to a success page after submitting feedback
    else:
        form = FeedbackForm()
    return render(request, 'OrchardGuard/feedback.html', {'form': form})


def information_page(request):
    any_search_form = AnySearchForm()
    search_form = SearchForm()
    list_search_form = ListSearchForm()

    return render(request, 'OrchardGuard/infohub.html', {
        'any_search_form': any_search_form,
        'search_form': search_form,
        'list_search_form': list_search_form
    })
def login(request):
    return render(request, 'OrchardGuard/vinsha_login.html')

def signup(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dob = request.POST.get('dob')

        # Basic password validation (enforce this client-side, or use Django's validators)
        if len(password) < 8 or not re.search("[a-z]", password) or not re.search("[A-Z]", password) or not re.search(
                "[0-9]", password) or not re.search("[\W_]", password):
            messages.error(request, "Password does not meet the security requirements.")
            return render(request, 'OrchardGuard/signup.html')

        try:
            user = auth.create_user(email=email, password=password)
            # After the user is created, save the additional information in Realtime Database
            user_ref = db.reference(f'users/{user.uid}')
            user_ref.set({
                'first_name': first_name,
                'last_name': last_name,
                'dob': dob
            })
            messages.success(request, "Account created successfully")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Failed to create account: {str(e)}")
            return render(request, 'OrchardGuard/signup.html')
    else:
        return render(request,'OrchardGuard/signup.html')

# def login_or_register(request):
#     login_form = LoginForm()
#     register_form = RegistrationForm()
#     if request.method == 'POST':
#         if 'login_submit' in request.POST:
#             login_form = LoginForm(request.POST)
#             if login_form.is_valid():
#                 # Perform login logic here
#                 return redirect('homepage')  # Redirect to homepage after successful login
#         elif 'register_submit' in request.POST:
#             register_form = RegistrationForm(request.POST)
#             if register_form.is_valid():
#                 # Perform registration logic here
#                 # For example:
#                 # first_name = register_form.cleaned_data['first_name']
#                 # last_name = register_form.cleaned_data['last_name']
#                 # email = register_form.cleaned_data['email']
#                 # password = register_form.cleaned_data['password']
#                 return redirect('login_or_register')  # Redirect to login page after successful registration
#     return render(request, 'OrchardGuard/vinsha_login.html', {'login_form': login_form, 'register_form': register_form})


def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return redirect('homepage')