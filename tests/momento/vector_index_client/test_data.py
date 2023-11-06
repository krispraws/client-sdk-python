from __future__ import annotations

from typing import Optional

import pytest

from momento import PreviewVectorIndexClient
from momento.errors import MomentoErrorCode
from momento.requests.vector_index import ALL_METADATA, Item, SimilarityMetric
from momento.responses.vector_index import (
    CreateIndex,
    DeleteItemBatch,
    Search,
    SearchHit,
    UpsertItemBatch,
)
from tests.conftest import TUniqueVectorIndexName
from tests.utils import sleep


def test_create_index_with_inner_product_upsert_item_search_happy_path(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=2, similarity_metric=SimilarityMetric.INNER_PRODUCT
    )
    assert isinstance(create_response, CreateIndex.Success)

    upsert_response = vector_index_client.upsert_item_batch(index_name, items=[Item(id="test_item", vector=[1.0, 2.0])])
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    search_response = vector_index_client.search(index_name, query_vector=[1.0, 2.0], top_k=1)
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 1
    assert search_response.hits[0].id == "test_item"
    assert search_response.hits[0].distance == 5.0


@pytest.mark.parametrize("similarity_metric", [SimilarityMetric.COSINE_SIMILARITY, None])
def test_create_index_with_cosine_similarity_upsert_item_search_happy_path(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
    similarity_metric: Optional[SimilarityMetric],
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    num_dimensions = 2
    if similarity_metric is not None:
        create_response = vector_index_client.create_index(
            index_name, num_dimensions=num_dimensions, similarity_metric=similarity_metric
        )
    else:
        create_response = vector_index_client.create_index(index_name, num_dimensions=num_dimensions)
    assert isinstance(create_response, CreateIndex.Success)

    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[1.0, 1.0]),
            Item(id="test_item_2", vector=[-1.0, 1.0]),
            Item(id="test_item_3", vector=[-1.0, -1.0]),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    search_response = vector_index_client.search(index_name, query_vector=[2.0, 2.0], top_k=3)
    assert isinstance(search_response, Search.Success)
    assert search_response.hits == [
        SearchHit(id="test_item_1", distance=1.0),
        SearchHit(id="test_item_2", distance=0.0),
        SearchHit(id="test_item_3", distance=-1.0),
    ]


def test_create_index_with_euclidean_similarity_upsert_item_search_happy_path(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=2, similarity_metric=SimilarityMetric.EUCLIDEAN_SIMILARITY
    )
    assert isinstance(create_response, CreateIndex.Success)

    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[1.0, 1.0]),
            Item(id="test_item_2", vector=[-1.0, 1.0]),
            Item(id="test_item_3", vector=[-1.0, -1.0]),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    search_response = vector_index_client.search(index_name, query_vector=[1.0, 1.0], top_k=3)
    assert isinstance(search_response, Search.Success)
    assert search_response.hits == [
        SearchHit(id="test_item_1", distance=0.0),
        SearchHit(id="test_item_2", distance=4.0),
        SearchHit(id="test_item_3", distance=8.0),
    ]


def test_create_index_upsert_multiple_items_search_happy_path(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=2, similarity_metric=SimilarityMetric.INNER_PRODUCT
    )
    assert isinstance(create_response, CreateIndex.Success)

    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[1.0, 2.0]),
            Item(id="test_item_2", vector=[3.0, 4.0]),
            Item(id="test_item_3", vector=[5.0, 6.0]),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    search_response = vector_index_client.search(index_name, query_vector=[1.0, 2.0], top_k=3)
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 3

    assert search_response.hits == [
        SearchHit(id="test_item_3", distance=17.0),
        SearchHit(id="test_item_2", distance=11.0),
        SearchHit(id="test_item_1", distance=5.0),
    ]


def test_create_index_upsert_multiple_items_search_with_top_k_happy_path(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=2, similarity_metric=SimilarityMetric.INNER_PRODUCT
    )
    assert isinstance(create_response, CreateIndex.Success)

    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[1.0, 2.0]),
            Item(id="test_item_2", vector=[3.0, 4.0]),
            Item(id="test_item_3", vector=[5.0, 6.0]),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    search_response = vector_index_client.search(index_name, query_vector=[1.0, 2.0], top_k=2)
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 2

    assert search_response.hits == [
        SearchHit(id="test_item_3", distance=17.0),
        SearchHit(id="test_item_2", distance=11.0),
    ]


def test_upsert_and_search_with_metadata_happy_path(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=2, similarity_metric=SimilarityMetric.INNER_PRODUCT
    )
    assert isinstance(create_response, CreateIndex.Success)

    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[1.0, 2.0], metadata={"key1": "value1"}),
            Item(id="test_item_2", vector=[3.0, 4.0], metadata={"key2": "value2"}),
            Item(id="test_item_3", vector=[5.0, 6.0], metadata={"key1": "value3", "key3": "value3"}),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    search_response = vector_index_client.search(index_name, query_vector=[1.0, 2.0], top_k=3)
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 3

    assert search_response.hits == [
        SearchHit(id="test_item_3", distance=17.0),
        SearchHit(id="test_item_2", distance=11.0),
        SearchHit(id="test_item_1", distance=5.0),
    ]

    search_response = vector_index_client.search(index_name, query_vector=[1.0, 2.0], top_k=3, metadata_fields=["key1"])
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 3

    assert search_response.hits == [
        SearchHit(id="test_item_3", distance=17.0, metadata={"key1": "value3"}),
        SearchHit(id="test_item_2", distance=11.0, metadata={}),
        SearchHit(id="test_item_1", distance=5.0, metadata={"key1": "value1"}),
    ]

    search_response = vector_index_client.search(
        index_name, query_vector=[1.0, 2.0], top_k=3, metadata_fields=["key1", "key2", "key3", "key4"]
    )
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 3

    assert search_response.hits == [
        SearchHit(id="test_item_3", distance=17.0, metadata={"key1": "value3", "key3": "value3"}),
        SearchHit(id="test_item_2", distance=11.0, metadata={"key2": "value2"}),
        SearchHit(id="test_item_1", distance=5.0, metadata={"key1": "value1"}),
    ]


def test_upsert_with_bad_metadata(vector_index_client: PreviewVectorIndexClient) -> None:
    response = vector_index_client.upsert_item_batch(
        index_name="test_index",
        items=[Item(id="test_item", vector=[1.0, 2.0], metadata={"key": {"subkey": "subvalue"}})],  # type: ignore
    )
    assert isinstance(response, UpsertItemBatch.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert (
        response.message
        == "Invalid argument passed to Momento client: Metadata values must be either str, int, float, bool, or list[str]. Field 'key' has a value of type <class 'dict'> with value {'subkey': 'subvalue'}."  # noqa: E501 W503
    )


def test_upsert_and_search_with_all_metadata_happy_path(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=2, similarity_metric=SimilarityMetric.INNER_PRODUCT
    )
    assert isinstance(create_response, CreateIndex.Success)

    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[1.0, 2.0], metadata={"key1": "value1"}),
            Item(id="test_item_2", vector=[3.0, 4.0], metadata={"key2": "value2"}),
            Item(id="test_item_3", vector=[5.0, 6.0], metadata={"key1": "value3", "key3": "value3"}),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    search_response = vector_index_client.search(index_name, query_vector=[1.0, 2.0], top_k=3)
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 3

    assert search_response.hits == [
        SearchHit(id="test_item_3", distance=17.0),
        SearchHit(id="test_item_2", distance=11.0),
        SearchHit(id="test_item_1", distance=5.0),
    ]

    search_response = vector_index_client.search(
        index_name, query_vector=[1.0, 2.0], top_k=3, metadata_fields=ALL_METADATA
    )
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 3

    assert search_response.hits == [
        SearchHit(id="test_item_3", distance=17.0, metadata={"key1": "value3", "key3": "value3"}),
        SearchHit(id="test_item_2", distance=11.0, metadata={"key2": "value2"}),
        SearchHit(id="test_item_1", distance=5.0, metadata={"key1": "value1"}),
    ]


def test_upsert_and_search_with_diverse_metadata_happy_path(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=2, similarity_metric=SimilarityMetric.INNER_PRODUCT
    )
    assert isinstance(create_response, CreateIndex.Success)

    metadata: dict[str, str | bool | int | float | list[str]] = {
        "string": "value",
        "bool": True,
        "int": 1,
        "float": 3.14,
        "list": ["a", "b", "c"],
        "empty_list": [],
    }
    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[1.0, 2.0], metadata=metadata),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    search_response = vector_index_client.search(
        index_name, query_vector=[1.0, 2.0], top_k=1, metadata_fields=ALL_METADATA
    )
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 1

    assert search_response.hits == [
        SearchHit(
            id="test_item_1",
            metadata=metadata,
            distance=5.0,
        ),
    ]


def test_upsert_replaces_existing_items(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=2, similarity_metric=SimilarityMetric.INNER_PRODUCT
    )
    assert isinstance(create_response, CreateIndex.Success)

    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[1.0, 2.0], metadata={"key1": "value1"}),
            Item(id="test_item_2", vector=[3.0, 4.0], metadata={"key2": "value2"}),
            Item(id="test_item_3", vector=[5.0, 6.0], metadata={"key1": "value3", "key3": "value3"}),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[2.0, 4.0], metadata={"key4": "value4"}),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    search_response = vector_index_client.search(
        index_name, query_vector=[1.0, 2.0], top_k=5, metadata_fields=["key1", "key2", "key3", "key4"]
    )
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 3

    assert search_response.hits == [
        SearchHit(id="test_item_3", distance=17.0, metadata={"key1": "value3", "key3": "value3"}),
        SearchHit(id="test_item_2", distance=11.0, metadata={"key2": "value2"}),
        SearchHit(id="test_item_1", distance=10.0, metadata={"key4": "value4"}),
    ]


def test_create_index_upsert_item_dimensions_different_than_num_dimensions_error(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=2, similarity_metric=SimilarityMetric.INNER_PRODUCT
    )
    assert isinstance(create_response, CreateIndex.Success)

    # upserting 3 dimensions
    upsert_response = vector_index_client.upsert_item_batch(
        index_name, items=[Item(id="test_item", vector=[1.0, 2.0, 3.0])]
    )
    assert isinstance(upsert_response, UpsertItemBatch.Error)

    expected_inner_ex_message = "invalid parameter: vector, vector dimension has to match the index's dimension"
    expected_message = f"Invalid argument passed to Momento client: {expected_inner_ex_message}"
    assert upsert_response.message == expected_message
    assert upsert_response.inner_exception.message == expected_inner_ex_message


def test_create_index_upsert_multiple_items_search_with_top_k_query_vector_dimensions_incorrect(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=2, similarity_metric=SimilarityMetric.INNER_PRODUCT
    )
    assert isinstance(create_response, CreateIndex.Success)

    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[1.0, 2.0]),
            Item(id="test_item_2", vector=[3.0, 4.0]),
            Item(id="test_item_3", vector=[5.0, 6.0]),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    search_response = vector_index_client.search(index_name, query_vector=[1.0, 2.0, 3.0], top_k=2)
    assert isinstance(search_response, Search.Error)

    expected_inner_ex_message = "invalid parameter: query_vector, query vector dimension must match the index dimension"
    expected_resp_message = f"Invalid argument passed to Momento client: {expected_inner_ex_message}"

    assert search_response.inner_exception.message == expected_inner_ex_message
    assert search_response.message == expected_resp_message


def test_upsert_validates_index_name(vector_index_client: PreviewVectorIndexClient) -> None:
    response = vector_index_client.upsert_item_batch(index_name="", items=[Item(id="test_item", vector=[1.0, 2.0])])
    assert isinstance(response, UpsertItemBatch.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR


def test_search_validates_index_name(vector_index_client: PreviewVectorIndexClient) -> None:
    response = vector_index_client.search(index_name="", query_vector=[1.0, 2.0])
    assert isinstance(response, Search.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR


def test_search_validates_top_k(vector_index_client: PreviewVectorIndexClient) -> None:
    response = vector_index_client.search(index_name="test_index", query_vector=[1.0, 2.0], top_k=0)
    assert isinstance(response, Search.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR
    assert response.inner_exception.message == "Top k must be a positive integer."


@pytest.mark.parametrize(
    ["similarity_metric", "distances", "thresholds"],
    [
        # Distances are the distance to the same 3 data vectors from the same query vector.
        # Thresholds are those that should:
        # 1. exclude lowest two matches
        # 2. keep all matches
        # 3. exclude all matches
        (SimilarityMetric.COSINE_SIMILARITY, [1.0, 0.0, -1.0], [0.5, -1.01, 1.0]),
        (SimilarityMetric.INNER_PRODUCT, [4.0, 0.0, -4.0], [0.0, -4.01, 4.0]),
        (SimilarityMetric.EUCLIDEAN_SIMILARITY, [2, 10, 18], [3, 20, -0.01]),
    ],
)
def test_search_score_threshold_happy_path(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
    similarity_metric: SimilarityMetric,
    distances: list[float],
    thresholds: list[float],
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    num_dimensions = 2
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=num_dimensions, similarity_metric=similarity_metric
    )
    assert isinstance(create_response, CreateIndex.Success)

    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[1.0, 1.0]),
            Item(id="test_item_2", vector=[-1.0, 1.0]),
            Item(id="test_item_3", vector=[-1.0, -1.0]),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    search_hits = [SearchHit(id=f"test_item_{i+1}", distance=distance) for i, distance in enumerate(distances)]

    search_response = vector_index_client.search(
        index_name, query_vector=[2.0, 2.0], top_k=3, score_threshold=thresholds[0]
    )
    assert isinstance(search_response, Search.Success)
    assert search_response.hits == [search_hits[0]]

    search_response2 = vector_index_client.search(
        index_name, query_vector=[2.0, 2.0], top_k=3, score_threshold=thresholds[1]
    )
    assert isinstance(search_response2, Search.Success)
    assert search_response2.hits == search_hits

    search_response3 = vector_index_client.search(
        index_name, query_vector=[2.0, 2.0], top_k=3, score_threshold=thresholds[2]
    )
    assert isinstance(search_response3, Search.Success)
    assert search_response3.hits == []


def test_delete_validates_index_name(vector_index_client: PreviewVectorIndexClient) -> None:
    response = vector_index_client.delete_item_batch(index_name="", ids=[])
    assert isinstance(response, DeleteItemBatch.Error)
    assert response.error_code == MomentoErrorCode.INVALID_ARGUMENT_ERROR


def test_delete_deletes_ids(
    vector_index_client: PreviewVectorIndexClient,
    unique_vector_index_name: TUniqueVectorIndexName,
) -> None:
    index_name = unique_vector_index_name(vector_index_client)
    create_response = vector_index_client.create_index(
        index_name, num_dimensions=2, similarity_metric=SimilarityMetric.INNER_PRODUCT
    )
    assert isinstance(create_response, CreateIndex.Success)

    upsert_response = vector_index_client.upsert_item_batch(
        index_name,
        items=[
            Item(id="test_item_1", vector=[1.0, 2.0]),
            Item(id="test_item_2", vector=[3.0, 4.0]),
            Item(id="test_item_3", vector=[5.0, 6.0]),
            Item(id="test_item_3", vector=[7.0, 8.0]),
        ],
    )
    assert isinstance(upsert_response, UpsertItemBatch.Success)

    sleep(2)

    search_response = vector_index_client.search(index_name, query_vector=[1.0, 2.0], top_k=10)
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 3

    assert search_response.hits == [
        SearchHit(id="test_item_3", distance=23.0),
        SearchHit(id="test_item_2", distance=11.0),
        SearchHit(id="test_item_1", distance=5.0),
    ]

    delete_response = vector_index_client.delete_item_batch(index_name, ids=["test_item_1", "test_item_3"])
    assert isinstance(delete_response, DeleteItemBatch.Success)

    sleep(2)

    search_response = vector_index_client.search(index_name, query_vector=[1.0, 2.0], top_k=10)
    assert isinstance(search_response, Search.Success)
    assert len(search_response.hits) == 1

    assert search_response.hits == [
        SearchHit(id="test_item_2", distance=11.0),
    ]
