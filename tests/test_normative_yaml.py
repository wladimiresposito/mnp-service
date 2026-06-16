from app.testing.normative_runner import assert_cases


def test_normative_yaml_cases():
    results = assert_cases("normative_tests/cases.yaml")
    assert len(results) >= 6
