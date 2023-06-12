from typing import List
from InstructorEmbedding import INSTRUCTOR
import pinecone
import json
import requests
from bs4 import BeautifulSoup
import uuid


pinecone.init(api_key='3172ab22-d119-46f2-acb2-9ab0122441a5',
              environment='us-east4-gcp')
index = pinecone.Index('law-docs')

model = INSTRUCTOR('/Users/home/gh/instructor-embed-api/instructor-large')

# UTILS
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'
INSTRUCTION = 'Represent the legal document for retrieval.'

# FUNCTIONS


def embed(payload: List[List[str]]):
    embeddings = model.encode(payload)
    return embeddings


def upsert(vectors: List[float], metadata: dict):
    index.upsert(
        [{'id': str(uuid.uuid4()), 'values': vectors, 'metadata': metadata}],
        namespace='act-legislation')


def download_html(url: str):
    response = requests.get(url)
    response.encoding = 'utf-8'  # explicitly set encoding to utf-8
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    return soup.text


def read_json(file_path: str):
    with open(file_path, 'r') as f:
        return json.load(f)


def split_text(input_string, overlap=200):
    result = []
    if len(input_string) > 2000:
        mid_point = len(input_string) // 2
        # Ensure overlap while splitting
        first_part = input_string[:mid_point + overlap]
        second_part = input_string[mid_point:]
        result += split_text(first_part)
        result += split_text(second_part)
    else:
        result.append(input_string)
    return result


def construct_embed_payload(text: str, instruction: str = INSTRUCTION):
    retv = []
    if len(text) > 2000:
        split_texts = split_text(text)
        for text in split_texts:
            retv.append([instruction, text])
    else:
        retv.append([instruction, text])
    return retv


def main():
    json = read_json('ACT-LEGISLATION_HTML copy/legislations.json')
    total_legislations = len(json)
    i = 1
    for legislation in json:
        legislation_id = legislation['id']
        legislation_index_url = legislation['index_url']
        legislation_combined_url = legislation['combined_url']
        legislation_name = legislation['name']
        legislation_year = legislation['year']
        jurisdiction = legislation['jurisdiction']
        print("processing legislation: ", legislation_name)

        j = 0
        for section in legislation['sections']:
            total_sections = len(legislation['sections'])
            section_id = section['id']
            section_name = section['name']
            section_url = section['url']
            print("processing section: ", section_name)

            print("downloading section text from: ", section_url)
            section_text = download_html(section_url)
            payload = construct_embed_payload(section_text)

            embeddings = []
            try:
                print("embedding section")
                embeddings = embed(payload)
            except Exception as e:
                print(RED, "failed to embed section: ",  e, RESET)
                continue

            try:
                print("upserting section")
                for embedding in embeddings:
                    upsert(embedding, {
                        'legislation_id': legislation_id,
                        'legislation_index_url': legislation_index_url,
                        'legislation_combined_url': legislation_combined_url,
                        'legislation_name': legislation_name,
                        'legislation_year': legislation_year,
                        'jurisdiction': jurisdiction,
                        'section_id': section_id,
                        'section_name': section_name,
                        'section_url': section_url,
                        'text': section_text
                    })
            except Exception as e:
                print(RED, f"failed to upsert section{RESET}\n",  e)
                continue
            j += 1
            print(
                GREEN, f"Processing {i}/{total_legislations} legislations{RESET}")
            print(
                GREEN, f"Processed {j}/{total_sections} sections{RESET}")

        i += 1
        print(
            GREEN, f"Processed {i}/{total_legislations} legislations{RESET}")


# def test():
#     json = read_json('ACT-LEGISLATION_HTML/legislations.json')
#     legislation = json[0]
#     legislation_id = legislation['id']
#     legislation_index_url = legislation['index_url']
#     legislation_combined_url = legislation['combined_url']
#     legislation_name = legislation['name']
#     legislation_year = legislation['year']
#     jurisdiction = legislation['jurisdiction']
#     section = legislation['sections'][0]
#     section_id = section['id']
#     section_name = section['name']
#     section_url = section['url']

#     section_text = download_html(section_url)
#     print("section_text: ", section_text)

#     embeddings = embed(section_text)
#     print("len embeddings: ", len(embeddings))
#     print("len embeddings[0]: ", len(embeddings[0]))

#     upsert(section_id, embeddings[0], {
#         'legislation_id': legislation_id,
#         'legislation_index_url': legislation_index_url,
#         'legislation_combined_url': legislation_combined_url,
#         'legislation_name': legislation_name,
#         'legislation_year': legislation_year,
#         'jurisdiction': jurisdiction,
#         'section_id': section_id,
#         'section_name': section_name,
#         'section_url': section_url
#     })


if __name__ == "__main__":
    main()
    # test()
