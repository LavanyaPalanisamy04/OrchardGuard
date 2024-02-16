import csv
import boto3
from django.shortcuts import render
from .forms import SearchForm

from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse

from OrchardGuard.dynamodb import insert_item_into_dynamodb, insert_data_into_dynamodb, query, query_by_partition_key


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


def search(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            # Get form data
            # Get form data
            search_attribute = form.cleaned_data.get('search_attribute')
            search_term = form.cleaned_data.get('search_term')

            queries = []

            # Add query for partition key
            if search_attribute == 'acno':
                items = query_by_partition_key(int(search_term))
                return render(request, 'OrchardGuard/search_results.html', {'items': items})

            # Add queries for each indexed attribute
            elif search_attribute ==  'accession':
                queries.append({
                    'IndexName': 'accession-index',  # Replace with the name of the GSI for accession
                    'KeyConditionExpression': 'accession = :accession',
                    'ExpressionAttributeValues': {':accession': search_term}
                })

            elif search_attribute ==  'cultivar_name':
                queries.append({
                    'IndexName': 'cultivar_name-index',  # Replace with the name of the GSI for accession
                    'KeyConditionExpression': 'cultivar_name = :cultivar_name',
                    'ExpressionAttributeValues': {':cultivar_name': search_term}
                })

            elif search_attribute == 'origin_country':
                queries.append({
                    'IndexName': 'origin_country-index',  # Replace with the name of the GSI for origin_country
                    'KeyConditionExpression': 'origin_country = :origin_country',
                    'ExpressionAttributeValues': {':origin_country': search_term}
                })

            elif search_attribute == 'origin_city':
                queries.append({
                    'IndexName': 'origin_city-index',  # Replace with the name of the GSI for origin_country
                    'KeyConditionExpression': 'origin_city = :origin_city',
                    'ExpressionAttributeValues': {':origin_city': search_term}
                })

            elif search_attribute == 'origin_province':
                queries.append({
                    'IndexName': 'origin_province-index',  # Replace with the name of the GSI for origin_country
                    'KeyConditionExpression': 'origin_province = :origin_province',
                    'ExpressionAttributeValues': {':origin_province': search_term}
                })

            elif search_attribute == 'pedigree':
                queries.append({
                    'IndexName': 'e_pedigree-index',  # Replace with the name of the GSI for origin_country
                    'KeyConditionExpression': 'e_pedigree = :pedigree',
                    'ExpressionAttributeValues': {':pedigree': search_term}
                })

            elif search_attribute == 'genus':
                queries.append({
                    'IndexName': 'e_genus-index',  # Replace with the name of the GSI for origin_country
                    'KeyConditionExpression': 'e_genus = :genus',
                    'ExpressionAttributeValues': {':genus': search_term}
                })

            elif search_attribute == 'species':
                queries.append({
                    'IndexName': 'e_species-index',  # Replace with the name of the GSI for origin_country
                    'KeyConditionExpression': 'e_species = :species',
                    'ExpressionAttributeValues': {':species': search_term}
                })

            # Execute queries and combine results
            items = query(queries)
            return render(request, 'OrchardGuard/search_results.html', {'items': items})

    else:
        form = SearchForm()

    return render(request, 'OrchardGuard/search.html', {'form': form})


