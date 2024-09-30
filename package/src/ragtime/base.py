from pydantic import BaseModel
from typing import Optional, Generic, Any, TypeVar
import inspect
from typing import Callable, Dict, Optional
import requests
from requests import Response


class RagtimeBase(BaseModel):
    meta: dict[str, Any] = {}


class RagtimeText(RagtimeBase):
    text: str = ""


T = TypeVar("T")


class RagtimeList(RagtimeBase, Generic[T]):
    items: list[T] = []

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, item):
        return self.items[item]

    def __getitem__(self, row: int) -> T:
        return self.items[row]

    def __setitem__(self, row: int, t: T):
        self.items[row] = t

    def append(self, t: T):
        self.items.append(t)

    def __len__(self) -> int:
        return len(self.items)

    def empty(self):
        self.items = []

class RagtimeException(Exception):
    pass


def format_exc(msg: str) -> str:
    """Format the message for Exceptions - adds the call stack among other"""
    inspect_stack = inspect.stack()
    class_name: str = inspect_stack[1][0].f_locals["self"].__class__.__name__
    return f"[{class_name}.{inspect.stack()[1][3]}()] {msg}"


def div0(num: float, denom: float) -> float:
    return float(num / denom) if denom else 0.0


# Requests types
REQ_GET = "get"
REQ_POST = "post"
REQ_PUT = "put"
REQ_DELETE = "delete"

_req_type_func: Dict[str, Callable] = {
    REQ_GET: requests.get,
    REQ_POST: requests.post,
    REQ_PUT: requests.put,
    REQ_DELETE: requests.delete,
}


################
# call
# @retry(Exception, tries=5, delay=3, jitter=(0,3))
def call_api(a_req_type: str, a_url: str, **kwargs) -> Response:
    """
    Calls API and manages errors
    Args:
        a_req_type: type of request (GET, POST, PUT, DELETE)
        a_url
        *args: variable number of extra argument
        **kwargs: variable number of keyword arguments
    Returns:
        Response
    """
    response: Optional[Response] = None
    err_msg: str = f"Type: {a_req_type} - Route: {a_url} - Args: {kwargs}"

    try:
        if kwargs == {}:
            response = _req_type_func[a_req_type](url=a_url)
        else:
            response = _req_type_func[a_req_type](a_url, **kwargs)
        if response is not None:
            err_msg += (
                "\n"
                + f"Response status: {response.status_code} - Response reason:{response.reason} - Response content: {str(response.content)}"
            )
    except:
        s: str = "before" if response is None else "after"
        raise Exception(f"Exception raised {s} calling - {err_msg}")
    if response is not None and response.status_code < 300:
        return response
    else:
        raise Exception(f"API called but returned error - {err_msg}")
