"""Regression tests for fatal downloader failures."""

import sys
import types

import pytest

import download_products


class FailingStreamingDataset:
    """Minimal streaming dataset that fails while records are consumed."""

    def filter(self, _predicate):
        return self

    def __iter__(self):
        raise RuntimeError("503 Service Unavailable")


def test_streaming_failure_is_propagated(monkeypatch, tmp_path):
    """A partial Hugging Face download must make the command fail."""
    datasets_module = types.ModuleType("datasets")
    datasets_module.load_dataset = lambda *_args, **_kwargs: FailingStreamingDataset()
    monkeypatch.setitem(sys.modules, "datasets", datasets_module)
    monkeypatch.setattr(download_products, "load_category_language_model", object)
    monkeypatch.setenv("SAVE_TO_MONGO", "false")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RuntimeError, match="503 Service Unavailable"):
        download_products.download_from_huggingface()
