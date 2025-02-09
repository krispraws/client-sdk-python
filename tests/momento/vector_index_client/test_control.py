import pytest
from momento import CredentialProvider, PreviewVectorIndexClient
from momento.config import VectorIndexConfiguration
from momento.errors import MomentoErrorCode
from momento.requests.vector_index import SimilarityMetric
from momento.responses.vector_index import (
    CreateIndex,
    DeleteIndex,
    IndexInfo,
    ListIndexes,
)

from tests.conftest import TUniqueVectorIndexName
from tests.utils import unique_test_vector_index_name


def test_create_index_list_indexes_and_delete_index(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
    vector_index_dimensions: int,
) -> None:
    new_index_name = unique_vector_index_name(vector_index_client)

    create_index_response = vector_index_client.create_index(new_index_name, num_dimensions=vector_index_dimensions)
    assert isinstance(create_index_response, CreateIndex.Success)

    list_indexes_response = vector_index_client.list_indexes()
    assert isinstance(list_indexes_response, ListIndexes.Success)
    assert any(
        IndexInfo(new_index_name, vector_index_dimensions, SimilarityMetric.COSINE_SIMILARITY) == index
        for index in list_indexes_response.indexes
    )

    delete_index_response = vector_index_client.delete_index(new_index_name)
    assert isinstance(delete_index_response, DeleteIndex.Success)


def test_create_index_already_exists_when_creating_existing_index(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
    vector_index_dimensions: int,
) -> None:
    new_index_name = unique_vector_index_name(vector_index_client)

    response = vector_index_client.create_index(new_index_name, num_dimensions=vector_index_dimensions)
    assert isinstance(response, CreateIndex.Success)

    response = vector_index_client.create_index(new_index_name, num_dimensions=vector_index_dimensions)
    assert isinstance(response, CreateIndex.IndexAlreadyExists)

    del_response = vector_index_client.delete_index(new_index_name)
    assert isinstance(del_response, DeleteIndex.Success)


def test_create_index_returns_error_for_bad_name(
    vector_index_client: PreviewVectorIndexClient,
) -> None:
    for bad_name, reason in [("", "not be empty"), (None, "be a string"), (1, "be a string")]:
        response = vector_index_client.create_index(bad_name, num_dimensions=1)  # type: ignore[arg-type]
        assert isinstance(response, CreateIndex.Error)
        assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
        assert response.inner_exception.message == f"Vector index name must {reason}"
        assert response.message == f"Invalid argument passed to Momento client: {response.inner_exception.message}"


def test_create_index_returns_error_for_bad_num_dimensions(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    for bad_num_dimensions in [0, 1.1]:
        response = vector_index_client.create_index(
            unique_vector_index_name(vector_index_client),
            num_dimensions=bad_num_dimensions,  # type: ignore[arg-type]
        )
        assert isinstance(response, CreateIndex.Error)
        assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
        assert response.inner_exception.message == "Number of dimensions must be a positive integer."
        assert response.message == f"Invalid argument passed to Momento client: {response.inner_exception.message}"


def test_create_index_returns_error_for_bad_similarity_metric(
    vector_index_client: PreviewVectorIndexClient,
) -> None:
    response = vector_index_client.create_index(
        index_name="vector-index",
        num_dimensions=2,
        similarity_metric="ASDF",  # type: ignore[arg-type]
    )
    assert isinstance(response, CreateIndex.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert response.inner_exception.message == "Invalid similarity metric `ASDF`"
    assert response.message == f"Invalid argument passed to Momento client: {response.inner_exception.message}"


# Delete index
def test_delete_index_succeeds(vector_index_client: PreviewVectorIndexClient, vector_index_dimensions: int) -> None:
    index_name = unique_test_vector_index_name()

    response = vector_index_client.create_index(index_name, vector_index_dimensions)
    assert isinstance(response, CreateIndex.Success)

    delete_response = vector_index_client.delete_index(index_name)
    assert isinstance(delete_response, DeleteIndex.Success)

    delete_response = vector_index_client.delete_index(index_name)
    assert isinstance(delete_response, DeleteIndex.Error)
    assert delete_response.error_code == MomentoErrorCode.NOT_FOUND_ERROR


def test_delete_index_returns_not_found_error_when_deleting_unknown_index(
    vector_index_client: PreviewVectorIndexClient,
) -> None:
    index_name = unique_test_vector_index_name()
    response = vector_index_client.delete_index(index_name)
    assert isinstance(response, DeleteIndex.Error)
    assert response.error_code == MomentoErrorCode.NOT_FOUND_ERROR
    assert response.inner_exception.message == f'Index with name "{index_name}" does not exist'
    print(response.message)
    expected_resp_message = (
        f"A index with the specified name does not exist. To resolve this error, make sure you "
        f"have created the index before attempting to use it: {response.inner_exception.message}"
    )
    assert response.message == expected_resp_message


def test_delete_index_returns_error_for_bad_name(
    vector_index_client: PreviewVectorIndexClient,
) -> None:
    for bad_name, reason in [("", "not be empty"), (None, "be a string"), (1, "be a string")]:
        response = vector_index_client.delete_index(bad_name)  # type: ignore[arg-type]
        assert isinstance(response, DeleteIndex.Error)
        assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
        assert response.inner_exception.message == f"Vector index name must {reason}"
        assert response.message == f"Invalid argument passed to Momento client: {response.inner_exception.message}"


def test_create_index_throws_authentication_exception_for_bad_token(
    bad_token_credential_provider: CredentialProvider,
    vector_index_configuration: VectorIndexConfiguration,
    vector_index_dimensions: int,
) -> None:
    index_name = unique_test_vector_index_name()

    with PreviewVectorIndexClient(vector_index_configuration, bad_token_credential_provider) as vector_index_client:
        response = vector_index_client.create_index(index_name, num_dimensions=2)
        assert isinstance(response, CreateIndex.Error)
        assert response.error_code == MomentoErrorCode.AUTHENTICATION_ERROR
        assert response.inner_exception.message == "Invalid signature"
        assert response.message == "Invalid authentication credentials to connect to index service: Invalid signature"


# List indexes
@pytest.mark.parametrize(
    "num_dimensions, similarity_metric",
    [
        (1, SimilarityMetric.COSINE_SIMILARITY),
        (2, SimilarityMetric.EUCLIDEAN_SIMILARITY),
        (3, SimilarityMetric.INNER_PRODUCT),
    ],
)
def test_list_indexes_succeeds(
    vector_index_client: PreviewVectorIndexClient, num_dimensions: int, similarity_metric: SimilarityMetric
) -> None:
    index_name = unique_test_vector_index_name()

    initial_response = vector_index_client.list_indexes()
    assert isinstance(initial_response, ListIndexes.Success)

    index_names = [index.name for index in initial_response.indexes]
    assert index_name not in index_names

    try:
        response = vector_index_client.create_index(index_name, num_dimensions, similarity_metric)
        assert isinstance(response, CreateIndex.Success)

        list_cache_resp = vector_index_client.list_indexes()
        assert isinstance(list_cache_resp, ListIndexes.Success)

        assert IndexInfo(index_name, num_dimensions, similarity_metric) in list_cache_resp.indexes
    finally:
        delete_response = vector_index_client.delete_index(index_name)
        assert isinstance(delete_response, DeleteIndex.Success)
