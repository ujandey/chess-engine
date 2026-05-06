import pytest


def pytest_collection_modifyitems(config, items):
    for item in items:
        path = item.path.name
        nodeid = item.nodeid

        if path == "test_perft.py":
            item.add_marker(pytest.mark.perft)
        elif path == "test_benchmark_thresholds.py":
            item.add_marker(pytest.mark.benchmark)
        elif "UciParsingTests" in nodeid or "UciProtocolTests" in nodeid:
            item.add_marker(pytest.mark.uci)
        else:
            item.add_marker(pytest.mark.unit)
