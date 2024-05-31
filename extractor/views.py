import openai
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
import os
import time

# OpenAI API token and assistant name
open_ai_token = settings.OPENAI_API_KEY
open_ai_assistant_name = 'Payment term extractor'
last_message_timestamp = 0

def get_assistant_id_by_name(client, assistant_name):
    list_assistants = client.beta.assistants.list()
    for assistant in list_assistants:
        if assistant.name == assistant_name:
            return assistant.id
    raise Exception(f"No Assistant with name '{assistant_name}' found on OpenAI!")

def start_new_conversation(client):
    new_thread = client.beta.threads.create()
    return new_thread

def process_file(file_path):
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        return df
    except Exception as e:
        print(f"An error occurred while processing the file: {e}")
        return None

def send_message(client, conversation, assistant, content):
    print(f"Sending message to assistant:\n{content}")
    client.beta.threads.messages.create(
        thread_id=conversation.id,
        role="user",
        content=content
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=conversation.id,
        assistant_id=assistant.id,
    )

def has_message_completed(message):
    if 'content' not in message.dict():
        return False
    if len(message.dict()['content']) < 1:
        return False
    if 'text' not in message.dict()['content'][0]:
        return False
    if 'value' not in message.dict()['content'][0]['text']:
        return False
    return True

def get_assistant_response(client, conversation, last_message_timestamp):
    try:
        messages = client.beta.threads.messages.list(thread_id=conversation.id, limit=20)
        if messages is None:
            return None

        for message in messages:
            if message.role == 'assistant' and has_message_completed(message):
                if message.created_at > last_message_timestamp:
                    last_message_timestamp = message.created_at
                    return message
        return None
    except Exception as e:
        print(f"Unable to retrieve assistant response: {e}")
        return None

def save_payment_terms_to_excel(terms, original_file_path):
    if not terms:
        print("No terms to save.")
        return

    base_name = os.path.basename(original_file_path)
    output_file_name = f"pt_output_{os.path.splitext(base_name)[0]}.xlsx"
    output_file_path = os.path.join(os.path.dirname(original_file_path), output_file_name)

    df = pd.DataFrame(terms, columns=['Payment Term Description', 'Payment Term', 'Cliff'])
    df['Payment Term'] = pd.to_numeric(df['Payment Term'], errors='coerce')
    df['Cliff'] = pd.to_numeric(df['Cliff'], errors='coerce')
    df.to_excel(output_file_path, index=False)
    print(f"Payment terms saved to {output_file_path}")

def print_unique_term_descriptions_count(terms):
    unique_descriptions = set(description for description, term, cliff in terms)
    print(f"Count of unique payment term descriptions: {len(unique_descriptions)}")

def guess_payment_term_column(df):
    for column in df.columns:
        sample_values = df[column].dropna().astype(str).tolist()
        if any("net" in value.lower() or "within" in value.lower() for value in sample_values):
            return column
    return None


def upload_file(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['file']
        file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)

        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        client = openai.OpenAI(api_key=open_ai_token)
        assistant_id = get_assistant_id_by_name(client, open_ai_assistant_name)
        assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
        conversation = start_new_conversation(client)

        df = process_file(file_path)
        if df is not None:
            column_name = "Payment Term Description"
            if column_name not in df.columns:
                guessed_column = guess_payment_term_column(df)
                if guessed_column:
                    column_name = guessed_column
                    print(f"Guessed the column containing payment terms: {column_name}")
                else:
                    print("Available columns in the file:")
                    for i, col in enumerate(df.columns):
                        print(f"{i + 1}. {col}")
                    col_index = int(
                        input("Enter the number corresponding to the 'Payment Term Description' column: ")) - 1
                    column_name = df.columns[col_index]

            # Remove header row from DataFrame after guessing the column
            unique_terms = df[[column_name]].drop_duplicates().iloc[1:]
            unique_terms[column_name] = unique_terms[column_name].fillna("Unknown")
            print(f"Unique terms collected:\n{unique_terms}")

            batch_size = 20
            all_terms = []
            for start_row in range(0, len(unique_terms), batch_size):
                chunk = unique_terms.iloc[start_row:start_row + batch_size]
                file_content = chunk.to_string(index=False)
                input_message = f"Please extract the payment terms and values from the following content, providing only original term description and the values. nothing else:\n{file_content}"
                print(f"Sending message to assistant:\n{input_message}")
                send_message(client, conversation, assistant, input_message)

                response = None
                while not response:
                    response = get_assistant_response(client, conversation, last_message_timestamp)
                    time.sleep(1)

                response_text = response.dict()['content'][0]['text']['value']
                print(f"Assistant response text:\n{response_text}")

                terms = []
                for line in response_text.split('\n'):
                    parts = line.split('|')
                    if len(parts) == 3:
                        description, term, cliff = parts
                        terms.append((description.strip(), float(term.strip()), float(cliff.strip())))

                if len(terms) != len(chunk):
                    print(
                        f"Mismatch in the number of terms for rows {start_row} to {start_row + batch_size}. Stopping the process.")
                    break
                else:
                    all_terms.extend(terms)

            if all_terms:
                save_payment_terms_to_excel(all_terms, file_path)
                print_unique_term_descriptions_count(all_terms)

                # Construct the output file path for the response
                base_name = os.path.basename(file_path)
                output_file_name = f"pt_output_{os.path.splitext(base_name)[0]}.xlsx"
                output_file_path = os.path.join(os.path.dirname(file_path), output_file_name)

                return render(request, 'upload.html',
                              {'message': f"Payment terms saved successfully to {output_file_path}"})
            else:
                return render(request, 'upload.html', {'message': "No payment terms found in the responses."})
        else:
            return render(request, 'upload.html',
                          {'message': "Failed to process the file. Please try uploading again."})
    return render(request, 'upload.html')





