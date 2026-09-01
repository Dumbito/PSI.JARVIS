from psi_jarvis.core.result import Result


def test_result_ok():
    result = Result.ok(
        data={"papers": 10},
        message="Operation completed",
    )

    assert result.success is True
    assert result.data == {"papers": 10}
    assert result.message == "Operation completed"


def test_result_fail():
    result = Result.fail("Invalid dataset")

    assert result.success is False
    assert result.data is None
    assert result.message == "Invalid dataset"


def test_result_is_immutable():
    result = Result.ok(data=10)

    try:
        result.success = False
    except AttributeError:
        pass
    else:
        raise AssertionError("Result should be immutable")
