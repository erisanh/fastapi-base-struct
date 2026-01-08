import json
import re
from collections.abc import Mapping

ACRONYM_RE = re.compile(r"([A-Z\d]+)(?=[A-Z\d]|$)")
PASCAL_RE = re.compile(r"([^\-_]+)")
SPLIT_RE = re.compile(r"([\-_]*[A-Z][^A-Z]*[\-_]*)")
UNDERSCORE_RE = re.compile(r"(?<=[^\-_])[\-_]+[^\-_]")


def to_snake_case(string: str) -> str:
    """
    Converts a string from camelCase or PascalCase into snake_case.

    Note:
        Uppercase letters are treated as word boundaries, which become underscores.

    Args:
        string (str): The input in camelCase or PascalCase format.

    Returns:
        str: The string converted to snake_case.

    Example:
        >>> to_snake_case("CamelCaseExample")
        'camel_case_example'


    """
    return "".join(["_" + i.lower() if i.isupper() else i for i in string]).lstrip("_")


def to_camel_case(snake_str: str) -> str:
    """
    Converts a string from snake_case into camelCase.

    Args:
        snake_str (str): The input in snake_case format.

    Returns:
        str: The string converted to camelCase.

    Example:
        >>> to_camel_case("snake_case_example")
        'snakeCaseExample'


    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def to_camel(string: str) -> str:
    """
    Converts a string from snake_case into CamelCase (a.k.a. PascalCase without a leading lowercase).

    Args:
        string (str): The input in snake_case format.

    Returns:
        str: The string converted to CamelCase.

    Example:
        >>> to_camel("snake_case_example")
        'SnakeCaseExample'


    """
    return "".join(word.capitalize() for word in string.split("_"))


def convert_filter_to_camel_case(filter="{}") -> str:
    """
    Despite the function name, it actually converts all JSON keys to snake_case.

    - Loads the given JSON string.
    - Converts **every key** to snake_case.
    - Returns a JSON string with updated keys.

    Args:
        filter (str): A JSON string. Keys may be in any format.

    Returns:
        str: A JSON string where all keys have been converted to snake_case.

    Example:
        >>> convert_filter_to_camel_case('{"snakeCaseKey": "value"}')
        '{"snake_case_key": "value"}'


    """
    filter_json = json.loads(filter)

    if isinstance(filter_json, dict):
        filter_sk = _dict_to_snake_case(filter_json)
    else:
        filter_sk = [_dict_to_snake_case(fl) for fl in filter_json]
    return json.dumps(filter_sk)


def pascalize(str_or_iter):
    """
    Converts a string (or keys in a dict/list) to PascalCase.

    - If the input is a dict or list, applies the transformation recursively to the keys (and nested keys).
    - Otherwise, transforms a single string.

    Args:
        str_or_iter (str | list | dict): Input data to convert.

    Returns:
        str | list | dict: Data converted to PascalCase.

    Example:
        >>> pascalize("snake_case_example")
        'SnakeCaseExample'


    """
    if isinstance(str_or_iter, (list, Mapping)):
        return _process_keys(str_or_iter, pascalize)

    s = _is_none(str_or_iter)
    if s.isupper() or s.isnumeric():
        return str_or_iter

    def _replace_fn(match):
        return match.group(1)[0].upper() + match.group(1)[1:]

    s = camelize(PASCAL_RE.sub(_replace_fn, s))
    return s[0].upper() + s[1:] if s else s


def camelize(str_or_iter):
    """
    Converts a string (or keys in a dict/list) to camelCase.

    - If the input is a dict or list, applies the transformation recursively to the keys (and nested keys).
    - Otherwise, transforms a single string to camelCase.

    Args:
        str_or_iter (str | list | dict): Input data to convert.

    Returns:
        str | list | dict: Data converted to camelCase.

    Example:
        >>> camelize("snake_case_example")
        'snakeCaseExample'


    """
    if isinstance(str_or_iter, (list, Mapping)):
        return _process_keys(str_or_iter, camelize)

    s = _is_none(str_or_iter)
    if s.isupper() or s.isnumeric():
        return str_or_iter

    if len(s) != 0 and not s[:2].isupper():
        s = s[0].lower() + s[1:]

    return UNDERSCORE_RE.sub(lambda m: m.group(0)[-1].upper(), s)


def kebabize(str_or_iter):
    """
    Converts a string (or keys in a dict/list) to kebab-case.

    - If the input is a dict or list, applies the transformation recursively to the keys (and nested keys).
    - Otherwise, transforms a single string to kebab-case.

    Args:
        str_or_iter (str | list | dict): Input data to convert.

    Returns:
        str | list | dict: Data converted to kebab-case.

    Example:
        >>> kebabize("snake_case_example")
        'snake-case-example'


    """
    if isinstance(str_or_iter, (list, Mapping)):
        return _process_keys(str_or_iter, kebabize)

    s = _is_none(str_or_iter)
    if s.isnumeric():
        return str_or_iter

    if not s.isupper() and (is_camelcase(s) or is_pascalcase(s)):
        return _separate_words(string=_fix_abbreviations(s), separator="-").lower()

    return UNDERSCORE_RE.sub(lambda m: "-" + m.group(0)[-1], s)


def decamelize(str_or_iter):
    """
    Converts a string (or keys in a dict/list) to snake_case, usually from camelCase or PascalCase.

    - If the input is a dict or list, applies the transformation recursively to the keys (and nested keys).
    - Otherwise, transforms a single string.

    Args:
        str_or_iter (str | list | dict): Input data to convert.

    Returns:
        str | list | dict: Data converted to snake_case.

    Example:
        >>> decamelize("camelCaseExample")
        'camel_case_example'


    """
    if isinstance(str_or_iter, (list, Mapping)):
        return _process_keys(str_or_iter, decamelize)

    s = _is_none(str_or_iter)
    if s.isupper() or s.isnumeric():
        return str_or_iter

    return _separate_words(_fix_abbreviations(s)).lower()


def depascalize(str_or_iter):
    """
    Converts a string (or keys in a dict/list) from PascalCase to snake_case.

    Essentially a wrapper around decamelize.

    Args:
        str_or_iter (str | list | dict): Input data in PascalCase.

    Returns:
        str | list | dict: Data converted to snake_case.

    Example:
        >>> depascalize("PascalCaseExample")
        'pascal_case_example'


    """
    return decamelize(str_or_iter)


def dekebabize(str_or_iter):
    """
    Converts a string (or keys in a dict/list) from kebab-case to snake_case.

    - If the input is a dict or list, applies the transformation recursively to the keys (and nested keys).
    - Otherwise, replaces hyphens (“-”) with underscores (“_”).

    Args:
        str_or_iter (str | list | dict): Input data in kebab-case.

    Returns:
        str | list | dict: Data converted to snake_case.

    Example:
        >>> dekebabize("kebab-case-example")
        'kebab_case_example'


    """
    if isinstance(str_or_iter, (list, Mapping)):
        return _process_keys(str_or_iter, dekebabize)

    s = _is_none(str_or_iter)
    if s.isnumeric():
        return str_or_iter

    return s.replace("-", "_")


def is_camelcase(str_or_iter):
    """
    Checks if a string (or every key in a dict/list) is in camelCase format.

    Internally compares the input with the result of camelize().

    Args:
        str_or_iter (str | list | dict): The input to check.

    Returns:
        bool: True if it's strictly in camelCase, False otherwise.

    Example:
        >>> is_camelcase("camelCaseExample")
        True


    """
    return str_or_iter == camelize(str_or_iter)


def is_pascalcase(str_or_iter):
    """
    Checks if a string (or every key in a dict/list) is in PascalCase format.

    Internally compares the input with the result of pascalize().

    Args:
        str_or_iter (str | list | dict]): The input to check.

    Returns:
        bool: True if it's strictly in PascalCase, False otherwise.

    Example:
        >>> is_pascalcase("PascalCaseExample")
        True


    """
    return str_or_iter == pascalize(str_or_iter)


def is_kebabcase(str_or_iter):
    """
    Checks if a string (or every key in a dict/list) is in kebab-case format.

    Internally compares the input with the result of kebabize().

    Args:
        str_or_iter (str | list | dict): The input to check.

    Returns:
        bool: True if it's strictly in kebab-case, False otherwise.

    Example:
        >>> is_kebabcase("kebab-case-example")
        True


    """
    return str_or_iter == kebabize(str_or_iter)


def is_snakecase(str_or_iter):
    """
    Checks if a string (or every key in a dict/list) is in snake_case format.

    Internally compares the input with the result of decamelize().

    Args:
        str_or_iter (str | list | dict): The input to check.

    Returns:
        bool: True if it's strictly in snake_case, False otherwise.

    Example:
        >>> is_snakecase("snake_case_example")
        True


    """
    if is_kebabcase(str_or_iter) and not is_camelcase(str_or_iter):
        return False
    return str_or_iter == decamelize(str_or_iter)


def _is_none(_in):
    """
    Returns an empty string if input is None; otherwise, strips all whitespace.

    Args:
        _in (str): The input string (may be None).

    Returns:
        str: Whitespace-free string, or empty if None.

    Example:
        >>> _is_none("  hello world  ")
        'helloworld'


    """
    return "" if _in is None else re.sub(r"\s+", "", str(_in))


def _process_keys(str_or_iter, fn):
    """
    Recursively applies a conversion function to each key in a dict or each element of a list.

    - If the input is a list, applies `fn` or recursion to each element.
    - If the input is a dict, applies `fn` to each key and recursion to each value.

    Args:
        str_or_iter (str | list | dict): The data to process.
        fn (callable): The function used to convert each key or element.

    Returns:
        str | list | dict: The processed data.

    Example:
        >>> _process_keys({"snake_key": "value"}, to_camel_case)
        {'snakeKey': 'value'}


    """
    if isinstance(str_or_iter, list):
        return [_process_keys(k, fn) for k in str_or_iter]
    if isinstance(str_or_iter, Mapping):
        return {fn(k): _process_keys(v, fn) for k, v in str_or_iter.items()}
    return str_or_iter


def _fix_abbreviations(string: str) -> str:
    """
    Adjusts uppercase acronyms so decamelization can split them more consistently.

    Args:
        string (str): The input string (may contain all-caps acronyms).

    Returns:
        str: A version of the string with acronyms partially cased to allow splitting.

    Example:
        >>> _fix_abbreviations("APIResponse")
        'ApiResponse'


    """
    return ACRONYM_RE.sub(lambda m: m.group(0).title(), string)


def _separate_words(string: str, separator="_") -> str:
    """
    Splits a string by uppercase “word boundaries” and rejoins using a chosen separator.

    Note:
        This function does not convert letters to lowercase;
        uppercase letters remain uppercase in split segments.

        Example:
            "camelCaseExample" => "camel_Case_Example" (NOT "camel_case_example").

    Args:
        string (str): The input string where uppercase letters indicate boundaries.
        separator (str): The separator used to join each chunk.

    Returns:
        str: The joined string with each chunk separated by `separator`.

    Example:
        >>> _separate_words("camelCaseExample")
        'camel_Case_Example'


    """
    return separator.join(s for s in SPLIT_RE.split(string) if s)


def _dict_to_snake_case(dict_: dict) -> dict:
    """
    Converts all keys in a dictionary to snake_case, preserving their values.

    Args:
        dict_ (dict): The input dictionary.

    Returns:
        dict: A new dictionary with all keys converted to snake_case.

    Example:
        >>> _dict_to_snake_case({"CamelCaseKey": "value"})
        {'camel_case_key': 'value'}


    """
    return {to_snake_case(k): dict_[k] for k in dict_}


def singularize(noun):
    """
    Converts a plural noun into a naive singular form by trimming trailing “s” or “es”.

    Warning:
        This function does not handle irregular nouns well:
        e.g., "companies" -> "companie", "wolves" -> "wolve".

    Args:
        noun (str): The plural noun to convert.

    Returns:
        str: The simplified form of the noun, possibly incorrect for many irregulars.

    Example:
        >>> singularize("users")
        'user'
        >>> singularize("companies")
        'companie'
        >>> singularize("wolves")
        'wolve'


    """
    if noun.endswith("s") or noun.endswith("es"):
        singular_form = noun[:-1]

        if singular_form.endswith("i") and not singular_form.endswith("ei"):
            singular_form = singular_form[:-1] + "y"
        elif singular_form.endswith("ves"):
            # "wolves" => "wolve" => removing "s" first leads to "wolve"
            # Then we see 'ves' -> 'f' (but it's truncated incorrectly).
            singular_form = singular_form[:-3] + "f"
        elif singular_form.endswith("es"):
            singular_form = singular_form[:-2]
        elif singular_form.endswith("ss"):
            singular_form = noun  # e.g., "bosses" => "bosses"

        return singular_form

    return noun
