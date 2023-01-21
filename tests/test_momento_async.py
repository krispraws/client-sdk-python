import os
import time
from datetime import timedelta

import pytest

import momento.errors as errors
from momento import SimpleCacheClientAsync
from momento.auth.credential_provider import CredentialProvider, EnvMomentoTokenProvider
from momento.config.configuration import Configuration
from momento.errors import InvalidArgumentException, MomentoErrorCode
from momento.responses import (
    CacheDelete,
    CacheGet,
    CacheSet,
    CreateCache,
    DeleteCache,
    ListCaches,
)
from tests.utils import str_to_bytes, unique_test_cache_name, uuid_bytes, uuid_str


async def test_create_cache_get_set_values_and_delete_cache(
    client_async: SimpleCacheClientAsync, cache_name: str
) -> None:
    random_cache_name = unique_test_cache_name()
    key = uuid_str()
    value = uuid_str()

    await client_async.create_cache(random_cache_name)

    set_resp = await client_async.set(random_cache_name, key, value)
    assert isinstance(set_resp, CacheSet.Success)

    get_resp = await client_async.get(random_cache_name, key)
    assert isinstance(get_resp, CacheGet.Hit)
    assert get_resp.value_string == value

    get_for_key_in_some_other_cache = await client_async.get(cache_name, key)
    assert isinstance(get_for_key_in_some_other_cache, CacheGet.Miss)

    await client_async.delete_cache(random_cache_name)


# Init
async def test_init_throws_exception_when_client_uses_negative_default_ttl(
    configuration: Configuration, credential_provider: CredentialProvider
) -> None:
    with pytest.raises(InvalidArgumentException, match="TTL timedelta must be a non-negative integer"):
        SimpleCacheClientAsync(configuration, credential_provider, timedelta(seconds=-1))


async def test_init_throws_exception_for_non_jwt_token(
    configuration: Configuration, default_ttl_seconds: timedelta
) -> None:
    with pytest.raises(InvalidArgumentException, match="Invalid Auth token."):
        os.environ["BAD_AUTH_TOKEN"] = "notanauthtoken"
        credential_provider = EnvMomentoTokenProvider("BAD_AUTH_TOKEN")
        SimpleCacheClientAsync(configuration, credential_provider, default_ttl_seconds)


async def test_init_throws_exception_when_client_uses_integer_request_timeout_ms(
    configuration: Configuration, credential_provider: CredentialProvider, default_ttl_seconds: int
) -> None:
    with pytest.raises(
        InvalidArgumentException, match="Request timeout must be a timedelta with a value greater " "than zero."
    ):
        configuration.with_client_timeout(-1)


async def test_init_throws_exception_when_client_uses_negative_request_timeout_ms(
    configuration: Configuration, credential_provider: CredentialProvider, default_ttl_seconds: timedelta
) -> None:
    with pytest.raises(
        InvalidArgumentException, match="Request timeout must be a timedelta with a value greater than zero."
    ):
        configuration = configuration.with_client_timeout(timedelta(seconds=-1))
        SimpleCacheClientAsync(configuration, credential_provider, default_ttl_seconds)


async def test_init_throws_exception_when_client_uses_zero_request_timeout_ms(
    configuration: Configuration, credential_provider: CredentialProvider, default_ttl_seconds: timedelta
) -> None:
    with pytest.raises(
        InvalidArgumentException, match="Request timeout must be a timedelta with a value greater than zero."
    ):
        configuration = configuration.with_client_timeout(timedelta(seconds=0))
        SimpleCacheClientAsync(configuration, credential_provider, default_ttl_seconds)


# Create cache
async def test_create_cache__already_exists_when_creating_existing_cache(
    client_async: SimpleCacheClientAsync, cache_name: str
) -> None:
    response = await client_async.create_cache(cache_name)
    assert isinstance(response, CreateCache.CacheAlreadyExists)


async def test_create_cache_throws_exception_for_empty_cache_name(
    client_async: SimpleCacheClientAsync,
) -> None:
    response = await client_async.create_cache("")
    assert isinstance(response, CreateCache.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR


async def test_create_cache_throws_validation_exception_for_null_cache_name(
    client_async: SimpleCacheClientAsync,
) -> None:
    response = await client_async.create_cache(None)
    assert isinstance(response, CreateCache.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert response.inner_exception.message == "Cache name must be a non-empty string"


async def test_create_cache_with_bad_cache_name_throws_exception(
    client_async: SimpleCacheClientAsync,
) -> None:
    response = await client_async.create_cache(1)
    assert isinstance(response, CreateCache.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert response.inner_exception.message == "Cache name must be a non-empty string"


async def test_create_cache_throws_authentication_exception_for_bad_token(
    bad_token_credential_provider: EnvMomentoTokenProvider, configuration: Configuration, default_ttl_seconds: timedelta
) -> None:
    async with SimpleCacheClientAsync(
        configuration, bad_token_credential_provider, default_ttl_seconds
    ) as client_async:
        response = await client_async.create_cache(unique_test_cache_name())
        assert isinstance(response, CreateCache.Error)
        assert response.error_code == errors.MomentoErrorCode.AUTHENTICATION_ERROR


# Delete cache
async def test_delete_cache_succeeds(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    cache_name = uuid_str()

    response = await client_async.create_cache(cache_name)
    assert isinstance(response, CreateCache.Success)

    response = await client_async.delete_cache(cache_name)
    assert isinstance(response, DeleteCache.Success)

    response = await client_async.delete_cache(cache_name)
    assert isinstance(response, DeleteCache.Error)
    assert response.error_code == MomentoErrorCode.NOT_FOUND_ERROR


async def test_delete_cache_throws_not_found_when_deleting_unknown_cache(
    client_async: SimpleCacheClientAsync,
) -> None:
    cache_name = uuid_str()
    response = await client_async.delete_cache(cache_name)
    assert isinstance(response, DeleteCache.Error)
    assert response.error_code == MomentoErrorCode.NOT_FOUND_ERROR


async def test_delete_cache_throws_invalid_input_for_null_cache_name(
    client_async: SimpleCacheClientAsync,
) -> None:
    response = await client_async.delete_cache(None)
    assert isinstance(response, DeleteCache.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR


async def test_delete_cache_throws_exception_for_empty_cache_name(
    client_async: SimpleCacheClientAsync,
) -> None:
    response = await client_async.delete_cache("")
    assert isinstance(response, DeleteCache.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR


async def test_delete_with_bad_cache_name_throws_exception(
    client_async: SimpleCacheClientAsync, cache_name: str
) -> None:
    response = await client_async.delete_cache(1)
    assert isinstance(response, DeleteCache.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert response.inner_exception.message == "Cache name must be a non-empty string"


async def test_delete_cache_throws_authentication_exception_for_bad_token(
    bad_token_credential_provider: EnvMomentoTokenProvider, configuration: Configuration, default_ttl_seconds: timedelta
) -> None:
    async with SimpleCacheClientAsync(
        configuration, bad_token_credential_provider, default_ttl_seconds
    ) as client_async:
        response = await client_async.delete_cache(uuid_str())
        assert isinstance(response, DeleteCache.Error)
        assert response.error_code == MomentoErrorCode.AUTHENTICATION_ERROR


# List caches
async def test_list_caches_succeeds(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    cache_name = uuid_str()

    initial_response = await client_async.list_caches()
    assert isinstance(initial_response, ListCaches.Success)

    cache_names = [cache.name for cache in initial_response.caches]
    assert cache_name not in cache_names

    try:
        response = await client_async.create_cache(cache_name)
        assert isinstance(response, CreateCache.Success)

        list_cache_resp = await client_async.list_caches()
        assert isinstance(list_cache_resp, ListCaches.Success)

        cache_names = [cache.name for cache in list_cache_resp.caches]
        assert cache_name in cache_names
        assert list_cache_resp.next_token is None
    finally:
        delete_response = await client_async.delete_cache(cache_name)
        assert isinstance(delete_response, DeleteCache.Success)


async def test_list_caches_throws_authentication_exception_for_bad_token(
    bad_token_credential_provider: EnvMomentoTokenProvider, configuration: Configuration, default_ttl_seconds: timedelta
) -> None:
    async with SimpleCacheClientAsync(
        configuration, bad_token_credential_provider, default_ttl_seconds
    ) as client_async:
        response = await client_async.list_caches()
        assert isinstance(response, ListCaches.Error)
        assert response.error_code == MomentoErrorCode.AUTHENTICATION_ERROR


async def test_list_caches_with_next_token_works(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    """skip until pagination is actually implemented, see
    https://github.com/momentohq/control-plane-service/issues/83"""
    pass


# Signing keys
async def test_create_list_revoke_signing_keys(client_async: SimpleCacheClientAsync) -> None:
    create_resp = await client_async.create_signing_key(timedelta(minutes=30))
    list_resp = await client_async.list_signing_keys()
    assert create_resp.key_id() in [signing_key.key_id() for signing_key in list_resp.signing_keys()]

    await client_async.revoke_signing_key(create_resp.key_id())
    list_resp = await client_async.list_signing_keys()
    assert create_resp.key_id() not in [signing_key.key_id() for signing_key in list_resp.signing_keys()]


# Setting and Getting
async def test_set_and_get_with_hit(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    key = uuid_str()
    value = uuid_str()

    set_resp = await client_async.set(cache_name, key, value)
    assert isinstance(set_resp, CacheSet.Success)

    get_resp = await client_async.get(cache_name, key)
    isinstance(get_resp, CacheGet.Hit)
    assert get_resp.value_string == value
    assert get_resp.value_bytes == str_to_bytes(value)


async def test_set_and_get_with_byte_key_values(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    key = uuid_bytes()
    value = uuid_bytes()

    set_resp = await client_async.set(cache_name, key, value)
    assert isinstance(set_resp, CacheSet.Success)

    get_resp = await client_async.get(cache_name, key)
    assert isinstance(get_resp, CacheGet.Hit)
    assert get_resp.value_bytes == value


async def test_get_returns_miss(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    key = uuid_str()

    get_resp = await client_async.get(cache_name, key)
    assert isinstance(get_resp, CacheGet.Miss)


async def test_expires_items_after_ttl(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    key = uuid_str()
    val = uuid_str()

    await client_async.set(cache_name, key, val, timedelta(seconds=2))
    get_response = await client_async.get(cache_name, key)
    assert isinstance(get_response, CacheGet.Hit)

    time.sleep(4)
    get_response = await client_async.get(cache_name, key)
    assert isinstance(get_response, CacheGet.Miss)


async def test_set_with_different_ttl(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    key1 = uuid_str()
    key2 = uuid_str()

    await client_async.set(cache_name, key1, "1", timedelta(seconds=2))
    await client_async.set(cache_name, key2, "2")

    # Before
    get_response = await client_async.get(cache_name, key1)
    assert isinstance(get_response, CacheGet.Hit)
    get_response = await client_async.get(cache_name, key2)
    assert isinstance(get_response, CacheGet.Hit)

    time.sleep(4)

    # After
    get_response = await client_async.get(cache_name, key1)
    assert isinstance(get_response, CacheGet.Miss)
    get_response = await client_async.get(cache_name, key2)
    assert isinstance(get_response, CacheGet.Hit)


# Set
async def test_set_with_non_existent_cache_name_throws_not_found(
    client_async: SimpleCacheClientAsync,
) -> None:
    cache_name = uuid_str()
    set_response = await client_async.set(cache_name, "foo", "bar")
    assert isinstance(set_response, CacheSet.Error)
    assert set_response.error_code == MomentoErrorCode.NOT_FOUND_ERROR


async def test_set_with_null_cache_name_throws_exception(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    set_response = await client_async.set(None, "foo", "bar")
    assert isinstance(set_response, CacheSet.Error)
    assert set_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert set_response.inner_exception.message == "Cache name must be a non-empty string"


async def test_set_with_empty_cache_name_throws_exception(
    client_async: SimpleCacheClientAsync,
) -> None:
    set_response = await client_async.set("", "foo", "bar")
    assert isinstance(set_response, CacheSet.Error)
    assert set_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert set_response.inner_exception.message == "Cache header is empty"


async def test_set_with_null_key_throws_exception(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    set_response = await client_async.set(cache_name, None, "bar")
    assert isinstance(set_response, CacheSet.Error)
    assert set_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR


async def test_set_with_null_value_throws_exception(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    set_response = await client_async.set(cache_name, "foo", None)
    assert isinstance(set_response, CacheSet.Error)
    assert set_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR


async def test_set_negative_ttl_throws_exception(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    set_response = await client_async.set(cache_name, "foo", "bar", timedelta(seconds=-1))
    assert isinstance(set_response, CacheSet.Error)
    assert set_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert set_response.inner_exception.message == "TTL timedelta must be a non-negative integer"


async def test_set_with_bad_cache_name_throws_exception(
    client_async: SimpleCacheClientAsync,
) -> None:
    set_response = await client_async.set(1, "foo", "bar")
    assert isinstance(set_response, CacheSet.Error)
    assert set_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert set_response.inner_exception.message == "Cache name must be a non-empty string"


async def test_set_with_bad_key_throws_exception(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    set_response = await client_async.set(cache_name, 1, "bar")
    assert isinstance(set_response, CacheSet.Error)
    assert set_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert set_response.inner_exception.message == "Unsupported type for key: <class 'int'>"


async def test_set_with_bad_value_throws_exception(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    set_response = await client_async.set(cache_name, "foo", 1)
    assert isinstance(set_response, CacheSet.Error)
    assert set_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert set_response.inner_exception.message == "Unsupported type for value: <class 'int'>"


async def test_set_throws_authentication_exception_for_bad_token(
    bad_token_credential_provider: EnvMomentoTokenProvider,
    configuration: Configuration,
    cache_name: str,
    default_ttl_seconds: timedelta,
) -> None:
    async with SimpleCacheClientAsync(
        configuration, bad_token_credential_provider, default_ttl_seconds
    ) as client_async:
        set_response = await client_async.set(cache_name, "foo", "bar")
        assert isinstance(set_response, CacheSet.Error)
        assert set_response.error_code == MomentoErrorCode.AUTHENTICATION_ERROR


async def test_set_throws_timeout_error_for_short_request_timeout(
    configuration: Configuration,
    credential_provider: EnvMomentoTokenProvider,
    cache_name: str,
    default_ttl_seconds: timedelta,
) -> None:
    configuration = configuration.with_client_timeout(timedelta(milliseconds=1))
    async with SimpleCacheClientAsync(configuration, credential_provider, default_ttl_seconds) as client_async:
        set_response = await client_async.set(cache_name, "foo", "bar")
        assert isinstance(set_response, CacheSet.Error)
        assert set_response.error_code == MomentoErrorCode.TIMEOUT_ERROR


# Get
async def test_get_with_non_existent_cache_name_throws_not_found(
    client_async: SimpleCacheClientAsync,
) -> None:
    cache_name = uuid_str()
    get_response = await client_async.get(cache_name, "foo")
    assert isinstance(get_response, CacheGet.Error)
    assert get_response.error_code == MomentoErrorCode.NOT_FOUND_ERROR


async def test_get_with_null_cache_name_throws_exception(
    client_async: SimpleCacheClientAsync,
) -> None:
    get_response = await client_async.get(None, "foo")
    assert isinstance(get_response, CacheGet.Error)
    assert get_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert get_response.inner_exception.message == "Cache name must be a non-empty string"


async def test_get_with_empty_cache_name_throws_exception(
    client_async: SimpleCacheClientAsync,
) -> None:
    get_response = await client_async.get("", "foo")
    assert isinstance(get_response, CacheGet.Error)
    assert get_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert get_response.inner_exception.message == "Cache header is empty"


async def test_get_with_null_key_throws_exception(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    get_response = await client_async.get(cache_name, None)
    assert isinstance(get_response, CacheGet.Error)
    assert get_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR


async def test_get_with_bad_cache_name_throws_exception(
    client_async: SimpleCacheClientAsync,
) -> None:
    get_response = await client_async.get(1, "foo")
    assert isinstance(get_response, CacheGet.Error)
    assert get_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert get_response.inner_exception.message == "Cache name must be a non-empty string"


async def test_get_with_bad_key_throws_exception(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    get_response = await client_async.get(cache_name, 1)
    assert isinstance(get_response, CacheGet.Error)
    assert get_response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert get_response.inner_exception.message == "Unsupported type for key: <class 'int'>"


async def test_get_throws_authentication_exception_for_bad_token(
    bad_token_credential_provider: EnvMomentoTokenProvider,
    configuration: Configuration,
    cache_name: str,
    default_ttl_seconds: timedelta,
) -> None:
    async with SimpleCacheClientAsync(
        configuration, bad_token_credential_provider, default_ttl_seconds
    ) as client_async:
        get_response = await client_async.get(cache_name, "foo")
        assert isinstance(get_response, CacheGet.Error)
        assert get_response.error_code == MomentoErrorCode.AUTHENTICATION_ERROR


async def test_get_throws_timeout_error_for_short_request_timeout(
    configuration: Configuration,
    credential_provider: EnvMomentoTokenProvider,
    cache_name: str,
    default_ttl_seconds: timedelta,
) -> None:
    configuration = configuration.with_client_timeout(timedelta(milliseconds=1))
    async with SimpleCacheClientAsync(configuration, credential_provider, default_ttl_seconds) as client_async:
        get_response = await client_async.get(cache_name, "foo")
        assert isinstance(get_response, CacheGet.Error)
        assert get_response.error_code == MomentoErrorCode.TIMEOUT_ERROR


# Test delete for key that doesn't exist
async def test_delete_key_doesnt_exist(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    key = uuid_str()
    get_response = await client_async.get(cache_name, key)
    assert isinstance(get_response, CacheGet.Miss)

    delete_response = await client_async.delete(cache_name, key)
    assert isinstance(delete_response, CacheDelete.Success)
    get_response = await client_async.get(cache_name, key)
    assert isinstance(get_response, CacheGet.Miss)


# Test delete
async def test_delete(client_async: SimpleCacheClientAsync, cache_name: str) -> None:
    # Set an item to then delete...
    key, value = uuid_str(), uuid_str()
    get_response = await client_async.get(cache_name, key)
    assert isinstance(get_response, CacheGet.Miss)
    set_response = await client_async.set(cache_name, key, value)
    assert isinstance(set_response, CacheSet.Success)

    get_response = await client_async.get(cache_name, key)
    assert isinstance(get_response, CacheGet.Hit)

    # Delete
    delete_response = await client_async.delete(cache_name, key)
    assert isinstance(delete_response, CacheDelete.Success)

    # Verify deleted
    get_response = await client_async.get(cache_name, key)
    assert isinstance(get_response, CacheGet.Miss)


async def test_configuration_client_timeout_copy_constructor(configuration: Configuration) -> None:
    def snag_deadline(config: Configuration) -> timedelta:
        return config.get_transport_strategy().get_grpc_configuration().get_deadline()  # type: ignore

    original_deadline: timedelta = snag_deadline(configuration)
    assert original_deadline.total_seconds() == 15
    configuration = configuration.with_client_timeout(timedelta(seconds=600))
    assert snag_deadline(configuration).total_seconds() == 600
