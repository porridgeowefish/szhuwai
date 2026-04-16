"""SessionManager 单元测试"""
from src.agent.session import SessionManager


class InMemoryRedis:
    def __init__(self):
        self._store = {}

    def set(self, key, value, ex=None):
        self._store[key] = value
        return True

    def get(self, key):
        return self._store.get(key)

    def delete(self, key):
        self._store.pop(key, None)

    def exists(self, key):
        return key in self._store


def test_create_and_get_session():
    redis = InMemoryRedis()
    sm = SessionManager(redis)
    sm.create_session("sess-1", 42)
    session = sm.get_session("sess-1", 42)
    assert session is not None
    assert session["user_id"] == 42


def test_get_session_wrong_user():
    redis = InMemoryRedis()
    sm = SessionManager(redis)
    sm.create_session("sess-1", 42)
    assert sm.get_session("sess-1", 99) is None


def test_get_session_not_found():
    redis = InMemoryRedis()
    sm = SessionManager(redis)
    assert sm.get_session("nonexistent", 1) is None


def test_append_and_get_messages():
    redis = InMemoryRedis()
    sm = SessionManager(redis)
    sm.create_session("sess-1", 42)
    sm.append_message("sess-1", "user", "你好")
    sm.append_message("sess-1", "assistant", "你好！有什么可以帮你？")
    messages = sm.get_messages("sess-1")
    assert len(messages) == 2
    assert messages[0].content == "你好"
    assert messages[1].content == "你好！有什么可以帮你？"


def test_attachment():
    redis = InMemoryRedis()
    sm = SessionManager(redis)
    sm.create_session("sess-1", 42)
    sm.set_attachment("sess-1", "track_file", "/tmp/test.gpx")
    assert sm.get_attachment("sess-1", "track_file") == "/tmp/test.gpx"
    assert sm.get_attachment("sess-1", "nonexistent") is None
