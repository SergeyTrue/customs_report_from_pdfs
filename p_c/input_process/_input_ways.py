import argparse
import pathlib
from ._input_data import InputData


def input_from_cmd() -> InputData:
    parser = argparse.ArgumentParser()
    parser.add_argument('--invoice_dir', type=str, required=True)
    parser.add_argument('--import_dir', type=str, required=True)
    parser.add_argument('--declaration_dump', type=str, required=True)
    args = vars(parser.parse_args())

    invoice_dir, import_dir, declaration_dump = (pathlib.Path(args['invoice_dir']), pathlib.Path(args['import_dir']),
                                                pathlib.Path(args['declaration_dump']))
    invoice_files = tuple(invoice_dir.rglob('*.pdf'))
    import_files = tuple(import_dir.rglob('*.pdf'))

    input_ = InputData(declaration_files=import_files, import_good_files=invoice_files,
                       declaration_dump=declaration_dump)
    return input_


