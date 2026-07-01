from pathlib import Path
import markdown_to_json as mj
import json
from docx import Document

def _mdToJson(file_path: str, output_file_path: str):
    with open(file_path, 'r', encoding='utf-8') as file:
        md_content = file.read()

    data = mj.dictify(md_content)

    with open(output_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

def _docxToJson(file_path: str, output_file_path: str):
    doc = Document(file_path)
    data = {"paragraphs": []}

    for para in doc.paragraphs:
        if para.text.strip():
            data["paragraphs"].append(para.text)

    with open(output_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

def _txtToJson(file_path: str, output_file_path: str):
    with open(file_path, 'r', encoding='utf-8') as input_file:
        input_data = input_file.read()
    input_data_paragraphs = input_data.split("\n\n")
    data = {"paragraphs": []}
    for para in input_data_paragraphs:
        data["paragraphs"].append(para)
    
    with open(output_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


def plan_to_json(plan_file_path: str, json_file_path: str):
    file_path = Path(plan_file_path)
    suffix = file_path.suffix
    if suffix == '.md':
        _mdToJson(file_path, json_file_path)
    elif suffix == '.docx':
        _docxToJson(file_path, json_file_path)
    elif suffix == '.txt':
        _txtToJson(file_path, json_file_path)
    else:
        print("I do not know this file!")
