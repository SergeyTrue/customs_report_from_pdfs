import attr
import typing
import json
from pathlib import Path
import re

import pdfplumber


from p_c.core import Declaration, Declarations, Position


all_declarations_json_path = Path(
    r'C:\Users\belose\PycharmProjects\pdf_customs\p_c\resources\all_declarations_json.txt')


def make_declarations_from_dump(file_with_declarations: Path) -> Declarations:
    with open(file_with_declarations, 'r') as f:
        all_declarations = json.loads(f.read())

    declarations = []
    for declaration_number, declaration_content in all_declarations.items():
        declaration = Declaration(number=declaration_number)
        positions = []
        if declaration_content:
            for position_number, position_content in declaration_content.items():
                if position_content:
                    try:
                        position = Position(position_number, position_content)
                        positions.append(position)
                    except ValueError:
                        print('ошибки позиций', declaration.number)

            declaration.positions = positions
            declarations.append(declaration)
    return declarations


def _find_declarations_missing_in_dump(declarations_from_dump: typing.List[Declaration],
                                       files_to_check: typing.Tuple[Path]) -> typing.List[Path]:
    known_declaration_numbers = []
    for entry in declarations_from_dump:
        known_declaration_numbers.append(entry.number)

    missing_declaration_paths = []

    for pdf_file in files_to_check:
        if not int(pdf_file.stem[-7:]) in known_declaration_numbers:

            missing_declaration_paths.append(pdf_file)
        else:
            continue
    return missing_declaration_paths


def make_declarations_from_files(files: typing.List[Path]) -> Declarations:
    declarations_from_new_files = []
    for pdf_file in files:
        print('а вот новый', pdf_file.stem[-7:])
        print(pdf_file)
        with pdfplumber.open(pdf_file) as pdf:
            pdf_content = ''
            for page in pdf.pages:
                single_page_text = page.extract_text()
                pdf_content = "".join((pdf_content, single_page_text))

        goods_starts = [word.start() for word in re.finditer(r'Товар №', pdf_content)]
        if goods_starts:
            number_starts = [x + 8 for x in goods_starts]
            number_ends = [x + 2 for x in number_starts]
            goods_indices = [pdf_content[x:x + 2].strip() for x in number_starts]
            goods_starts.pop(0)

            goods_starts.append(len(pdf_content))

            descriptions = list(zip(goods_indices, number_ends, goods_starts))
            positions = []
            for (indices, start, end) in descriptions:
                position = Position(number=indices, content=pdf_content[start:end])
                positions.append(position)
        else:
            positions = None

        declaration = Declaration(number=int(pdf_file.stem[-7:]), positions=positions)
        declarations_from_new_files.append(declaration)

    return declarations_from_new_files


def make_json(all_declarations:  typing.List[Declaration]) -> str:

    declaration_dict = {}
    for declaration in all_declarations:
        position_dict = {}
        if declaration.positions:
            for position in declaration.positions:
                position_dict[position.number] = position.content
            declaration_dict[declaration.number] = position_dict
        else:
            declaration_dict[declaration.number] = None
    return json.dumps(declaration_dict)


def process_declarations(path_to_dump: Path, path_do_declarations: Path):
    declarations = make_declarations_from_dump(path_to_dump)
    files_to_read = _find_declarations_missing_in_dump(declarations, path_do_declarations)
    if files_to_read:
        new_declarations = make_declarations_from_files(files_to_read)
        declarations = declarations + new_declarations
        json_declarations = make_json(declarations)
        with open(path_to_dump, 'w') as f:
            f.write(json_declarations)
    return declarations





