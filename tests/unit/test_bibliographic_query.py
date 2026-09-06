from psi_jarvis.application.acquisition import BibliographicQuery


def test_bibliographic_query_normalizes_text_and_is_immutable():
    query = BibliographicQuery(
        text="  working memory  ",
        parameters=(("language", "en"), ("year_from", "2020")),
    )

    assert query.text == "working memory"
    assert query.parameters == (("language", "en"), ("year_from", "2020"))
    assert query.payload() == {
        "parameters": {"language": "en", "year_from": "2020"},
        "text": "working memory",
    }

    try:
        query.text = "other"
    except AttributeError:
        pass
    else:
        raise AssertionError("BibliographicQuery should be immutable")


def test_bibliographic_query_rejects_empty_text_and_duplicate_parameters():
    try:
        BibliographicQuery(text="   ")
    except ValueError as exc:
        assert str(exc) == "Bibliographic query text cannot be empty"
    else:
        raise AssertionError("Empty bibliographic query text should be rejected")

    try:
        BibliographicQuery(parameters=(("year", "2020"), ("year", "2021")))
    except ValueError as exc:
        assert str(exc) == "Bibliographic query parameter names must be unique"
    else:
        raise AssertionError("Duplicate bibliographic query parameters should be rejected")
