import qap


def test_qap_imports_with_a_development_version() -> None:
    assert qap.__version__
