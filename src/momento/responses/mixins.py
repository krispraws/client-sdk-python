import typing

# https://stackoverflow.com/questions/71889556/mypy-checking-typing-protocol-with-python-3-7-support
if typing.TYPE_CHECKING:
    from typing_extensions import Protocol
else:
    Protocol = object

from typing import Type, TypeVar

from momento.errors import MomentoErrorCode, SdkException


class HasValueBytesProtocol(Protocol):
    @property
    def value_bytes(self) -> bytes:
        ...


class ValueStringMixin:
    """Renders `value_bytes` as a utf-8 string.

    Returns:
        str: the utf-8 encoding of the data
    """

    @property
    def value_string(self: HasValueBytesProtocol) -> str:
        """Convert the bytes `value` to a UTF-8 string

        Returns:
            str: UTF-8 representation of the `value`
        """
        return self.value_bytes.decode("utf-8")


class HasErrorProtocol(Protocol):
    @property
    def _error(self) -> SdkException:
        ...


TError = TypeVar("TError", bound="ErrorResponseMixin")


class ErrorResponseMixin:
    def __init__(self, _error: SdkException):
        ...

    @property
    def inner_exception(self: HasErrorProtocol) -> SdkException:
        """The SdkException object used to construct the response."""
        return self._error

    @property
    def error_code(self: HasErrorProtocol) -> MomentoErrorCode:
        """The `MomentoErrorCode` value for the particular error object."""
        return self._error.error_code

    @property
    def message(self: HasErrorProtocol) -> str:
        """An explanation of conditions that caused and potential ways to resolve the error."""
        return f"{self._error.message_wrapper}: {self._error.message}"

    @classmethod
    def from_sdkexception(cls: Type[TError], _error: SdkException) -> TError:
        return cls(_error)
