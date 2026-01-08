import io
import pytest

__all__ = ("test_io",)

@pytest.fixture
def test_io():
    return io.StringIO(), io.StringIO()

