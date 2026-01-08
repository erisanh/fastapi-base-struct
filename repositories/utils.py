from pydantic import BaseModel


class Paging(BaseModel):
    offset: int
    limit: int
    sort_by: str
    sort_order: str
