import grpc
import time
import uuid
import momento_wire_types.cacheclient_pb2_grpc as cache_client
import momento_wire_types.cacheclient_pb2 as cache_client_types

from . import _cache_service_errors_converter
from . import _authorization_interceptor
from . import _cache_name_interceptor
from . import errors
from . import cache_operation_responses as cache_sdk_resp
from . import _momento_logger


class Cache:
    def __init__(self, auth_token, cache_name, endpoint, default_ttlSeconds):
        self._validate_ttl(default_ttlSeconds)
        self._default_ttlSeconds = default_ttlSeconds
        self._secure_channel = grpc.secure_channel(
            endpoint, grpc.ssl_channel_credentials())
        auth_interceptor = _authorization_interceptor.get_authorization_interceptor(
            auth_token)
        cache_interceptor = _cache_name_interceptor.get_cache_name_interceptor(
            cache_name)
        intercept_channel = grpc.intercept_channel(self._secure_channel,
                                                   auth_interceptor,
                                                   cache_interceptor)
        self._client = cache_client.ScsStub(intercept_channel)

    # While the constructor opens the grpc channel. Connect allows the channel
    # to test the connection with provided cache name and auth token.
    # Separating the _connect from the constructor, allows better latency and
    # resource management for calls that need get or create functionality.
    def _connect(self) :
        try:
            _momento_logger.debug('Initializing connection with Cache Service')
            self.get(uuid.uuid1().bytes)
            _momento_logger.debug('Success: Connection Initialized with Cache Service')
            return self
        except Exception as e:
            _momento_logger.debug(f'Cache Service Connect Failed with: {e}')
            raise _cache_service_errors_converter.convert(e) from None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._secure_channel.close()

    def set(self, key, value, ttl_seconds=None):
        try:
            _momento_logger.debug(f'Issuing a set request with key {key}')
            item_ttl_seconds = self._default_ttlSeconds if ttl_seconds is None else ttl_seconds
            self._validate_ttl(item_ttl_seconds)
            set_request = cache_client_types.SetRequest()
            set_request.cache_key = self._asBytes(
                key, 'Unsupported type for key: ')
            set_request.cache_body = self._asBytes(
                value, 'Unsupported type for value: ')
            set_request.ttl_milliseconds = item_ttl_seconds * 1000
            response = self._client.Set(set_request)
            _momento_logger.debug(f'Set succeeded for key: {key}')
            return cache_sdk_resp.CacheSetResponse(response,
                                                   set_request.cache_body)
        except Exception as e:
            _momento_logger.debug(f'Set failed for {key} with response: {e}')
            raise _cache_service_errors_converter.convert(e)

    def get(self, key):
        try:
            _momento_logger.debug(f'Issuing a get request with key {key}')
            get_request = cache_client_types.GetRequest()
            get_request.cache_key = self._asBytes(
                key, 'Unsupported type for key: ')
            response = self._client.Get(get_request)
            _momento_logger.debug(f'Received a get response for {key}')
            return cache_sdk_resp.CacheGetResponse(response)
        except Exception as e:
            _momento_logger.debug(f'Get failed for {key} with response: {e}')
            raise _cache_service_errors_converter.convert(e)

    def _asBytes(self, data, errorMessage):
        if (isinstance(data, str)):
            return data.encode('utf-8')
        if (isinstance(data, bytes)):
            return data
        raise errors.InvalidInputError(errorMessage + str(type(data)))

    def _validate_ttl(self, ttl_seconds):
        if (not isinstance(ttl_seconds, int) or ttl_seconds <= 0):
            raise errors.InvalidInputError(
                'TTL Seconds must be a non-zero positive integer.')
