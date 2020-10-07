import attr
import typing
import pathlib


def _to_paths(items):
    return tuple(pathlib.Path(item) for item in items)

def _to_path(item):
    return pathlib.Path(item)

def _is_existing_file(instance, attrib, value: pathlib.Path):
    return value.is_file()


@attr.s
class InputData:
    declaration_files = attr.ib(type=typing.Tuple[pathlib.Path],
                                converter=_to_paths,
                                validator=attr.validators.deep_iterable(member_validator=_is_existing_file))

    import_good_files = attr.ib(type=typing.Tuple[pathlib.Path],
                                converter=_to_paths,
                                validator=attr.validators.deep_iterable(member_validator=_is_existing_file))

    declaration_dump = attr.ib(type=pathlib.Path,
                               converter=_to_path,
                               )
