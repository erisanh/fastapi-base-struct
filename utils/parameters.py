from fastapi import Query

from utils.string_case import convert_filter_to_camel_case, to_snake_case


async def common_filter_parameters(
    page: int = 1,
    limit: int = 100,
    filter: str = "{}",
    include: str = None,
    join: str = "{}",
    orderBy: str = None,
):
    if join:
        join_ = convert_filter_to_camel_case(join)
    else:
        join_ = "{}"

    if filter:
        filter_ = convert_filter_to_camel_case(filter)
    else:
        filter_ = "{}"

    if include:
        include = to_snake_case(include)
    else:
        include = None
    skip = round((page - 1) * limit)
    if skip < 1:
        skip = 0
    if orderBy and orderBy != "":
        orderBy = to_snake_case(orderBy)
    else:
        orderBy = None
    return {
        "skip": skip,
        "limit": limit,
        "filter": filter_,
        "include": include,
        "order_by": orderBy,
        "join": join_,
    }
