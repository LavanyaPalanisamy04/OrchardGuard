import ast
import csv
import json

import requests
from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

from .forms import ListSearchForm, AnySearchForm
from .forms import SearchForm

AWS_ELASTICSEARCH_URL = settings.AWS_ELASTICSEARCH_URL
AWS_ELASTICSEARCH_USERNAME = settings.AWS_ELASTICSEARCH_USERNAME
AWS_ELASTICSEARCH_PASSWORD = settings.AWS_ELASTICSEARCH_PASSWORD
auth = (AWS_ELASTICSEARCH_USERNAME, AWS_ELASTICSEARCH_PASSWORD)

COLUMNS_TO_EXPORT = ['acno', 'accession', 'cultivar_name', 'origin_country', 'origin_province', 'origin_city',
                     'e_pedigree', 'e_genus', 'e_species', 'breeder']
COLUMN_HEADER = ['Acno', 'Accession', 'Cultivar Name', 'Country', 'Province', 'City', 'Pedigree', 'Genus', 'Species',
                 'breeder']

REPORT_HEADING = 'Apple Accessions Report'
EXPORT_FILENAME = "Accessions Search Report"


# add documents to opensearch domain
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
    headers = {'Content-Type': 'application/json'}
    response = requests.post(AWS_ELASTICSEARCH_URL, auth=auth, headers=headers, data=bulk_request)

    # Check response status
    if response.status_code == 200:
        print("Documents indexed successfully!")
    else:
        print("Failed to index documents:", response.text)


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
            response = requests.post(
                AWS_ELASTICSEARCH_URL,
                auth=(AWS_ELASTICSEARCH_USERNAME, AWS_ELASTICSEARCH_PASSWORD),
                json=query)

            # Extract search results
            items = []
            for record in response.json()['hits']['hits']:
                items.append(record['_source'])

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
                AWS_ELASTICSEARCH_URL,
                auth=(AWS_ELASTICSEARCH_USERNAME, AWS_ELASTICSEARCH_PASSWORD),
                json=query)

            # Extract search results
            items = []
            for record in response.json()['hits']['hits']:
                items.append(record['_source'])

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
                        "should": []
                    }
                }
            }

            # Add search terms from the form fields
            for field, value in form.cleaned_data.items():
                if value:
                    query["query"]["bool"]["should"].append({"match": {field: value}})

                    # Make a POST request to Elasticsearch
            response = requests.post(
                AWS_ELASTICSEARCH_URL,
                auth=(AWS_ELASTICSEARCH_USERNAME, AWS_ELASTICSEARCH_PASSWORD),
                json=query)

            # Extract search results
            items = []
            for record in response.json()['hits']['hits']:
                items.append(record['_source'])
            # Render the search results in the template
            return render(request, 'OrchardGuard/search_results.html', {'items': items})
    else:
        form = SearchForm()
    return render(request, 'OrchardGuard/search.html', {'form': form})


def wrap_text(text, char_limit):
    words = text.split()
    wrapped_text = ''
    line = ''
    for word in words:
        if len(line) + len(word) <= char_limit:
            line += word + ' '
        else:
            wrapped_text += line + '\n'
            line = word + ' '
    wrapped_text += line
    return wrapped_text.strip()


def export_pdf(items_list):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{EXPORT_FILENAME}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []  # List to hold elements to add to the document
    # Define the styles for the document
    styles = getSampleStyleSheet()
    heading_style = styles['Heading1']  # Use a predefined heading style
    heading_style.alignment = 1
    # Create the heading Paragraph and add it to the elements list
    heading_text = REPORT_HEADING
    heading = Paragraph(heading_text, heading_style)
    elements.append(heading)

    # Define a style for wrapped text
    style = ParagraphStyle(name='WrapStyle', fontSize=8)

    # Create the header row with the column names
    header_row = [Paragraph('<b>' + column + '</b>', style) for column in COLUMN_HEADER]

    # Filter the items_list to only include the columns you want
    data = [header_row] + [
        [Paragraph(str(item.get(column, '')), style) for column in COLUMNS_TO_EXPORT] for item in items_list
    ]

    # Define column widths - you'll need to adjust these values to fit your content
    column_widths = [
        0.56 * inch, 0.75 * inch, 1 * inch, 0.75 * inch, 0.75 * inch,
        1 * inch, 0.75 * inch, 0.75 * inch, 0.75 * inch, 0.75 * inch
    ]

    # Make sure the number of widths matches the number of columns
    assert len(column_widths) == len(COLUMNS_TO_EXPORT), "Column widths do not match number of columns"

    # Create the table with the data and column widths
    table = Table(data, colWidths=column_widths)

    # Add style to table, including borders
    table_style = TableStyle([
        # ... your existing style definitions ...
        ('BOX', (0, 0), (-1, -1), 1, colors.black),  # Outer border
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Inner grid
    ])
    table.setStyle(table_style)
    elements.append(table)

    # List of elements to build the document with
    elements = [heading, Spacer(1, 0.25 * inch), table]  # Spacer adds space after the heading
    # Add table to the PDF
    doc.build(elements)
    return response


def export_word(items_list):
    # Create a Word document
    doc = Document()

    # Add a heading
    heading = doc.add_heading(REPORT_HEADING, level=1)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # Add a table to the Word document
    table = doc.add_table(rows=1, cols=len(COLUMNS_TO_EXPORT))

    # Populate the header row
    for idx, column in enumerate(COLUMNS_TO_EXPORT):
        cell = table.cell(0, idx)
        cell.text = str(column)

    # Apply style to the table (optional, you can define your own style)
    table.style = 'Table Grid'

    # Populate table rows with items
    for item in items_list:
        row_cells = table.add_row().cells
        for idx, column in enumerate(COLUMNS_TO_EXPORT):
            row_cells[idx].text = str(item.get(column, ''))

    # Prepare the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="{EXPORT_FILENAME}.docx"'

    # Save the document to the HttpResponse
    doc.save(response)

    return response


def export_csv(request):
    if request.method == 'POST':
        items_json = request.POST.get('items')
        export_option = request.POST.get('exportOption')

        try:
            # Parse the JSON data
            items_list = ast.literal_eval(items_json)

            # Filter the items_list to only include the columns you want
            filtered_items_list = [{column: item.get(column, '') for column in COLUMNS_TO_EXPORT} for item in
                                   items_list]

            if export_option == 'csv':
                # Export as CSV with selected columns
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{EXPORT_FILENAME}.csv"'

                csv_writer = csv.DictWriter(response, fieldnames=COLUMNS_TO_EXPORT)
                csv_writer.writeheader()
                for item in filtered_items_list:
                    csv_writer.writerow(item)

                return response
            elif export_option == 'pdf':
                # Export as PDF with selected columns
                return export_pdf(filtered_items_list)
            elif export_option == 'word':
                # Export as PDF with selected columns
                return export_word(filtered_items_list)
            else:
                return HttpResponseBadRequest("Invalid export option.")
        except (ValueError, SyntaxError) as e:
            return HttpResponseBadRequest("Invalid JSON data.")
    else:
        return HttpResponseBadRequest("Invalid request method.")
