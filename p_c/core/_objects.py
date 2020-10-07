import attr
import typing

import pandas as pd
import numpy as np


@attr.s(auto_attribs=True)
class Declaration:
    number: int = attr.ib(converter=attr.converters.optional(int))

    positions: typing.List['Position'] = attr.validators.optional(attr.ib(factory=list))

    def find_position(self, article):
        if self.positions:

            for entry in self.positions:
                if entry.content:
                    if not str(article) in entry.content:
                        continue
                    else:
                        if entry.number:
                            return entry.number
                        else:
                            break

            if len(str(article)) > 8:
                article = int(str(article)[:7])
                for entry in self.positions:
                    if entry.content:
                        if not str(article) in entry.content:
                            continue
                        else:
                            return entry.number

@attr.s(auto_attribs=True)
class Position:
    number: int = attr.ib(converter=attr.converters.optional(int))
    content: str = attr.ib(converter=attr.converters.optional(str))


Declarations = typing.List[Declaration]


def _more_then_zero(instance, attrib, value: float):
    if value <= 0:
        raise ValueError


@attr.s
class ImportGood:
    article_number = attr.ib(type=int, validator=attr.validators.instance_of(int))
    article_description = attr.ib(type=str, validator=attr.validators.instance_of(str))
    type_code = attr.ib(type=int, validator=attr.validators.instance_of(int))
    unit_of_measure_in_words = attr.ib(type=str, validator=attr.validators.instance_of(str))
    quantity = attr.ib(type=float, converter=float, validator=_more_then_zero)
    quantity_code = attr.ib(type=int, validator=attr.validators.instance_of(int))
    price_per_each = attr.ib(type=float, converter=float, validator=_more_then_zero)
    country = attr.ib(type=str, validator=attr.validators.instance_of(str))
    country_2_letter_code = attr.ib(type=str, validator=attr.validators.instance_of(str))
    full_declaration_number = attr.ib(type=str, validator=attr.validators.instance_of(str))
    short_declaration_number = attr.ib(type=str, validator=attr.validators.instance_of(str))
    invoice = attr.ib(type=int, validator=attr.validators.instance_of(int))
    date = attr.ib(type=str, validator=attr.validators.instance_of(str))
    net_weight = attr.ib(type=float, converter=float, validator=_more_then_zero)
    gross_weight = attr.ib(type=float, converter=float, validator=_more_then_zero)
    statistical_rub_amount = attr.ib(type=float, converter=float, validator=_more_then_zero)
    statistical_usd_amount = attr.ib(type=float, converter=float, validator=_more_then_zero)
    declaration = attr.ib(type=Declaration, validator=attr.validators.optional(attr.validators.instance_of(Declaration)))
    position = attr.ib(type=str, validator=attr.validators.instance_of(str))
    manufacturer = attr.ib(type=str, validator=attr.validators.optional(attr.validators.instance_of(str)))
    ogrn =attr.ib(type=str, validator=attr.validators.optional(attr.validators.instance_of(str)))
    inn = attr.ib(type=str, validator=attr.validators.optional(attr.validators.instance_of(str)))
    kpp = attr.ib(type=str, validator=attr.validators.optional(attr.validators.instance_of(str)))
    okato = attr.ib(type=str, validator=attr.validators.optional(attr.validators.instance_of(str)))
    traceable_quantity = attr.ib(type=float, validator=attr.validators.optional(attr.validators.instance_of(float)))
    traceable_quantity_sign = attr.ib(type=str, validator=attr.validators.optional(attr.validators.instance_of(str)))
    traceable_quantity_code = attr.ib(type=str, validator=attr.validators.optional(attr.validators.instance_of(str)))
    additional_data_code = attr.ib(type=str, validator=attr.validators.optional(attr.validators.instance_of(str)))

    def modify_units_of_measure(self, units_of_measure_corrector: pd.DataFrame):

        if self.type_code in units_of_measure_corrector.index:
            self.unit_of_measure_in_words = units_of_measure_corrector.loc[self.type_code, 'unit_of_measure_in_words']
            self.quantity_code = units_of_measure_corrector.loc[self.type_code, 'quantity_code']
            if (type(units_of_measure_corrector.loc[self.type_code, 'quantity']) == np.float64 and
                    pd.isna(units_of_measure_corrector.loc[self.type_code, 'quantity'])):
                self.quantity = None

    def modify_old_new_code(self, old_new_code_df: pd.DataFrame):
        if self.type_code in old_new_code_df.index:
            self.type_code = old_new_code_df.loc[self.type_code, 'new']



ImportGoods = typing.List[ImportGood]


class ImportGoodDetail:
    import_good: ImportGood  # all data
    country_code: str




