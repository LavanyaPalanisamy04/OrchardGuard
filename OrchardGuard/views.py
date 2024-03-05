import csv
import json
import requests

import boto3
from django.shortcuts import render
from .forms import SearchForm

from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse

from OrchardGuard.dynamodb import insert_item_into_dynamodb, insert_data_into_dynamodb, query, query_by_partition_key, \
    scan_table

from elasticsearch import Elasticsearch
from django.shortcuts import render
from .forms import SearchForm  # Import your SearchForm

# Define Elasticsearch client
es = Elasticsearch(hosts=['https://search-orchard-guard-ow7eqo2vkmw47bwlnbasc6a2ce.us-east-2.es.amazonaws.com'],
                   http_auth=('Lavanya', 'Orchardguard@04'),
                   headers={"Content-Type": "application/json"}
                   )



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
            items = response.json()['hits']['hits']

            print("items ",items)

            # Render the search results in the template
            return render(request, 'OrchardGuard/search_results.html', {'items': items})
    else:
        form = SearchForm()
    return render(request, 'OrchardGuard/search.html', {'form': form})



