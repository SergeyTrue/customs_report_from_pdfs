from pathlib import Path
import typing

import pandas as pd
import pdfplumber
from datetime import datetime
import pycbrf

from ._input_data import InputData
from ._input_ways import input_from_cmd
from p_c.core import ImportGood, ImportGoods, Declaration, Declarations, Position
from p_c.declaration import process_declarations
from p_c.common.config import (WEIGHT_PATH, COUNTRY_PATH, UNIT_OF_MEASUREMENT_CORRECTOR, OLD_NEW_CODE_CORRECTOR)


def get_import_goods() -> ImportGoods:
    input_data = input_from_cmd()
    weight_df = _read_weights(WEIGHT_PATH)
    country_df = _read_countries(COUNTRY_PATH)
    old_new_code_df = _read_old_new_code(OLD_NEW_CODE_CORRECTOR)
    declarations = process_declarations(input_data.declaration_dump, input_data.declaration_files)
    res = _to_import_goods(input_data, weight_df, country_df, old_new_code_df, declarations)
    return res


def _to_import_goods(input_data: InputData, weight_df: pd.DataFrame, country_df: pd.DataFrame,
                     old_new_code_df: pd.DataFrame, all_declarations: typing.List[Declaration]
                     ) -> ImportGoods:

    goods = []
    merged_df = _read_dfs_from_invoices(input_data.import_good_files)
    modify_unit_of_measurement_df = _read_uom_corrector(UNIT_OF_MEASUREMENT_CORRECTOR)

    exchange_rates = _make_exchange_rate_df(merged_df)
    for i, row in merged_df.iterrows():
        good = _to_import_good(row, weight_df, country_df, exchange_rates, all_declarations)
        goods.append(good)
    for good in goods:
        good.modify_units_of_measure(modify_unit_of_measurement_df)
        good.modify_old_new_code(old_new_code_df)
    return goods


def _read_uom_corrector(corrector: Path):
    print(type(corrector))
    print(corrector.is_file())
    corrector_df = pd.read_csv(corrector, sep='\t')
    corrector_df.set_index('type_code', inplace=True)

    return corrector_df


def _read_old_new_code(old_new_code_path: Path):

    old_new_code_df = pd.read_csv(old_new_code_path, sep='\t')
    old_new_code_df.set_index('old', inplace=True)
    return old_new_code_df


def _make_exchange_rate_df(df: pd.DataFrame):

    dates = df['date'].drop_duplicates(keep='first')
    exchange_rates = pd.DataFrame(dates)
    exchange_rates = exchange_rates.rename(columns={0: 'date'})
    currencies = ['USD', 'EUR']
    for currency in currencies:
        exchange_rates[currency] = exchange_rates.date.apply(lambda x: pycbrf.ExchangeRates(x)[currency].value)
    exchange_rates = exchange_rates.set_index('date')
    return exchange_rates


def _read_weights(weight_path: Path) -> pd.DataFrame:

    weight_df = pd.read_csv(weight_path, sep='\t')
    weight_df.set_index('Material', inplace=True)
    return weight_df


def _read_countries(country_path: Path) -> pd.DataFrame:

    country_df = pd.read_csv(country_path, sep='|')
    country_df.set_index('country', inplace=True)
    return country_df


def _read_dfs_from_invoices(import_good_files) -> pd.DataFrame:
    dfs = []
    for invoice in import_good_files:
        invoice_content = pdfplumber.open(invoice)
        page = invoice_content.pages[0]
        invoice_number = page.extract_text()[15:25]
        invoice_date = page.extract_text()[29:39]
        invoice_date = datetime.strptime(invoice_date, '%d.%m.%Y').strftime('%Y-%m-%d')

        pages = invoice_content.pages
        for i, pg in enumerate(pages):
            df = pd.DataFrame(pages[i].extract_table())
            df['invoice'] = invoice_number
            df['date'] = invoice_date
            dfs.append(df)

    df = pd.concat(dfs)

    bad_list = ['1', None, 'Всего к оплате']
    df = df.loc[~df[0].isin(bad_list)]
    df.reset_index(inplace=True, drop=True)
    df.replace(to_replace=r'\s+|\\n', value=' ', regex=True, inplace=True)
    df = df.loc[df.iloc[:, 0].str.match(r'^\d')]
    return df


def _to_import_good(row: pd.Series, weight_df: pd.DataFrame, country_df: pd.DataFrame,
                    exchange_rates: pd.DataFrame, all_declarations: typing.List[Declaration]) -> ImportGood:
    _ = row[0]
    article_number, article_description = _.split(' - ')
    article_number = int(article_number.strip())
    article_description = article_description.strip()
    type_code = int(row[1])
    unit_of_measure_in_words = row[3]
    quantity = float(row[4].replace(' ', '').replace('.', '').replace(',', '.'))
    quantity_code = int(row[2])
    price_per_line = float(row[10].replace(' ', '').replace('.', '').replace(',', '.'))
    country = country_df.loc[row[12], 'country_caps']
    country_2_letter_code = country_df.loc[row[12], '2_letter_code']
    full_declaration_number = row[13].replace(' ', '')
    short_declaration_number = full_declaration_number[-7:]

    invoice = int(row['invoice'])
    date = row['date']
    net_weight = weight_df.loc[int(article_number), 'Net Weight'] * quantity
    gross_weight = weight_df.loc[int(article_number), 'Gross Weight'] * quantity
    statistical_rub_amount = float(exchange_rates.loc[date, 'EUR'])*price_per_line
    statistical_usd_amount = statistical_rub_amount/float(exchange_rates.loc[date, 'USD'])
    declaration = next((declaration for declaration in all_declarations if
                        declaration.number == int(short_declaration_number)), None)
    if declaration:
        position = str(declaration.find_position(article_number))
    else:
        position = 'в папке нет декларации'
    manufacturer = None
    ogrn = None
    inn = None
    kpp = None
    okato = None
    traceable_quantity = None
    traceable_quantity_sign = None
    traceable_quantity_code = None
    additional_data_code = None

    good = ImportGood(
        article_number, article_description, type_code, unit_of_measure_in_words, quantity, quantity_code,
        price_per_line, country, country_2_letter_code, full_declaration_number, short_declaration_number,
        invoice, date, net_weight, gross_weight, statistical_rub_amount, statistical_usd_amount, declaration,
        position, manufacturer,
        ogrn, inn, kpp, okato, traceable_quantity, traceable_quantity_sign, traceable_quantity_code,
        additional_data_code)

    return good


#
# incoices_paths = list(Path(r'C:\Users\belose\PycharmProjects\pdf_customs\p_c\resources\invoices').rglob('*.pdf'))
# gtd_paths = list(Path(r'C:\Users\belose\PycharmProjects\pdf_customs\p_c\resources\declaration').rglob('*.pdf'))
# country_path = Path(r'C:\Users\belose\PycharmProjects\pdf_customs\p_c\resources\country.txt')
#
# def read_invoices(inv_path: list) -> pd.DataFrame: #TODO typing  норм?
#     inv_dict={}
#     frames = []
#     for invoice in incoices_paths:
#         invoice_content = pdfplumber.open(invoice)
#         page = invoice_content.pages[0]
#         invoice_numbner = page.extract_text()[15:25]
#         invoice_date = page.extract_text()[29:39]
#         invoice_date = datetime.strptime(invoice_date, '%d.%m.%Y').strftime('%Y-%m-%d')
#         pages = invoice_content.pages
#         for i, pg in enumerate(pages):
#             df = pd.DataFrame(pages[i].extract_table())
#             df['invoice'] = invoice_numbner
#             df['date'] = invoice_date
#             frames.append(df)
#
#         print(invoice.stem)
#     result = pd.concat(frames)
#     return result
#
#
# def clean_invoice_content(df_to_clean: pd.DataFrame) -> pd.DataFrame:
#
#     df_to_clean.replace(to_replace=r'\s+|\\n', value=' ', regex=True, inplace=True)
#     df_to_clean[13] = df_to_clean[13].str.replace(' ', '')
#     bad_list = ['1', None, 'Всего к оплате']
#     df_to_clean = df_to_clean.loc[~df_to_clean[0].isin(bad_list)]
#     df_to_clean.reset_index(inplace=True, drop=True)
#     ar_desc_df = df_to_clean[0].str.split(pat=' - ', expand=True)
#     df_to_clean = df_to_clean.join(ar_desc_df, rsuffix='r')
#     df_to_clean.drop(df_to_clean.columns[0], axis=1, inplace=True)
#     cols_to_move = ['0r', '1r']
#     df_to_clean = df_to_clean[cols_to_move + [col for col in df_to_clean.columns if col not in cols_to_move]]
#     df_to_clean.columns = df_to_clean.iloc[0]
#     df_to_clean = df_to_clean.loc[df_to_clean.iloc[:, 0].str.match(r'^\d')]
#     declaration = df_to_clean['Регистрационныйномертаможеннойдекларации'].str[:7]
#     df_to_clean = df_to_clean.join(declaration, rsuffix='r')
#     df_to_clean.columns = range(df_to_clean.shape[1])
#
#     return df_to_clean
#
#
# def read_country(countries_file: Path) -> pd.DataFrame:
#
#     full_country = pd.read_csv(Path(countries_file), sep='\t')
#     country = full_country[['name', 'alpha2']]
#     country_df = country.rename(columns={'name': 13, 'alpha2': 18})
#
#
#     return country_df
#
#
#
# if __name__ == "__main__":
#
#     df = read_invoices(incoices_paths)
#     df = clean_invoice_content(df)
#     country = read_country(country_path)
#     print(list(df))
#     print(list(country))

  #  df = df.merge(country, on=13)
  #  df = df.rename(columns={1: 'Гр. 12. Наименование товара',
  #                          2: 'Гр. 11. Код ТН ВЭД ЕАЭС',
  #                          3: 'Гр. 18. Количество товара (цифровой  код ед. изм.)',
  #                          4: 'Гр. 18. Количество товара (буквенный код ед. изм.)',
   #                         5: 'Гр. 18. Количество товара (Кол-во)',
   #                         6: 'Гр. 13. Стоимость товара',
  #                          13: 'Гр. 15. Страна происхождения (наименование)',
 #                           16: 'Гр. 15. Страна происхождения (код)',
 #                           14: '№ ДТ: XXXXXXXX/ДДММГГ/XXXXXXX',
 #                           18: 'Гр. 15. Страна происхождения(код)',
#
 #                           })
#
 #   print(df)

