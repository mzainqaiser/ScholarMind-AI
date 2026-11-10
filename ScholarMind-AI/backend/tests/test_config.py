import os

from backend.app.config import _load_dotenv


def test_dotenv_parsed_comments_stripped_and_env_wins(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comment\nSM_TEST_A=hello   # trailing comment\nSM_TEST_B=\"quoted\"\nSM_TEST_C=from_file\n\nnot a pair\n")
    monkeypatch.delenv("SM_TEST_A", raising=False)
    monkeypatch.delenv("SM_TEST_B", raising=False)
    monkeypatch.setenv("SM_TEST_C", "from_real_env")
    _load_dotenv(env)
    assert os.environ["SM_TEST_A"] == "hello" and os.environ["SM_TEST_B"] == "quoted"
    assert os.environ["SM_TEST_C"] == "from_real_env"            # real environment variable is never overridden
    for k in ("SM_TEST_A", "SM_TEST_B"):
        os.environ.pop(k, None)


def test_missing_dotenv_is_fine(tmp_path):
    _load_dotenv(tmp_path / "nope.env")
