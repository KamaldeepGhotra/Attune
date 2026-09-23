from unittest.mock import MagicMock, patch

from app.llm.client import SearchSuggestions, suggest_search_queries


@patch("app.llm.client.genai.Client")
def test_suggest_search_queries_returns_llm_suggestions(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.parsed = SearchSuggestions(queries=["Beach House", "dream pop"])
    mock_client.models.generate_content.return_value = mock_response

    top_tracks = [
        {"name": "Song A", "artists": [{"name": "Artist A"}]},
        {"name": "Song B", "artists": [{"name": "Artist B"}]},
    ]

    queries = suggest_search_queries(top_tracks, count=2)

    assert queries == ["Beach House", "dream pop"]
    mock_client.models.generate_content.assert_called_once()
    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-flash-latest"
    assert "Artist A" in call_kwargs["contents"]
    assert "Artist B" in call_kwargs["contents"]


@patch("app.llm.client.genai.Client")
def test_suggest_search_queries_excludes_known_artists_from_prompt_instructions(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.parsed = SearchSuggestions(queries=[])
    mock_client.models.generate_content.return_value = mock_response

    top_tracks = [{"name": "Song A", "artists": [{"name": "Tame Impala"}]}]

    suggest_search_queries(top_tracks)

    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert "Tame Impala" in call_kwargs["contents"]
    assert "NOT" in call_kwargs["contents"] or "not already" in call_kwargs["contents"].lower()
