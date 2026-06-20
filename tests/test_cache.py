import time
import pytest
from cftc_cot.cache import MemoryCache, DiskCache, build_cache, COTCache
from cftc_cot.exceptions import COTError


def test_memory_cache_set_get():
    cache = MemoryCache()
    cache.set("k", [1, 2, 3], ttl=60)
    assert cache.get("k") == [1, 2, 3]


def test_memory_cache_miss():
    assert MemoryCache().get("missing") is None


def test_memory_cache_ttl_expiry():
    cache = MemoryCache()
    cache.set("k", "v", ttl=0)  # expires immediately
    time.sleep(0.01)
    assert cache.get("k") is None


def test_build_cache_memory():
    assert isinstance(build_cache("memory"), MemoryCache)


def test_build_cache_none():
    assert build_cache(None) is None


def test_build_cache_unknown():
    with pytest.raises(COTError):
        build_cache("redis")


def test_build_cache_passthrough_instance():
    mc = MemoryCache()
    assert build_cache(mc) is mc


def test_memory_cache_satisfies_protocol():
    assert isinstance(MemoryCache(), COTCache)


def test_disk_cache_roundtrip(tmp_path):
    pytest.importorskip("diskcache")
    cache = DiskCache(str(tmp_path / "cache"))
    cache.set("k", {"a": 1}, ttl=60)
    assert cache.get("k") == {"a": 1}


def test_disk_cache_missing_dependency(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "diskcache":
            raise ImportError("no diskcache")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(COTError):
        DiskCache("./whatever")
