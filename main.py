# TODO class: page_title, page_id, children
import argparse
import logging
import os
from pathlib import Path
from typing import Dict, Optional

import requests
from jinja2 import Environment, FileSystemLoader


def get_page(
        page_id: int
) -> Dict:
    confluence_base_url = os.environ["CONFLUENCE_BASE_URL"]
    url = f"{confluence_base_url}/rest/api/content/{page_id}?expand=children.page"
    logging.info(f'Fetching {url}...')
    response = requests.get(
        url,
        headers={
            'Authorization': f'Bearer {os.environ["CONFLUENCE_PERSONAL_ACCESS_TOKEN"]}'
        }
    )
    assert response.status_code == 200, (response.status_code, response.text)
    data = response.json()
    assert len(data['children']['page']['results']) < data['children']['page']['limit']
    # pprint(data)
    return data


def create_page_and_children_struct(
        page_id: id,
        max_depth: Optional[int],
        depth: int = 0,
) -> Dict:
    confluence_page_data = get_page(page_id)
    children_data = confluence_page_data['children']['page']['results']

    children = []
    if max_depth is None or depth < max_depth:
        for child in children_data:
            if not child['title'].startswith('[DRAFT] '):  # TODO hacky
                children.append(create_page_and_children_struct(child['id'], max_depth, depth + 1))

    return {
        'title': confluence_page_data['title'],
        'id': confluence_page_data['id'],
        'children': children
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # TODO argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--main-page-id', type=int)
    parser.add_argument('--output-name')
    args = parser.parse_args()

    max_depth = None  # Mainly here for debug purpose

    environment = Environment(loader=FileSystemLoader("."))
    template = environment.get_template("template.html.j2")

    content = template.render(
        page=create_page_and_children_struct(args.main_page_id, max_depth),
        confluence_base_url='https://agile.richemont.com/confluence'
    ).replace("\n\n", "\n").replace("\n\n", "\n")  # TODO hacky
    with Path(args.output_name).open(mode="w") as file:
        file.write(content)
