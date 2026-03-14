import pytest
import os
import tempfile
from pathlib import Path

from src.ouroboros.ouroboros_v2 import mode_preset, wrap_noncode, sha256_file

def test_mode_preset():
    # Should resolve standard to Equilibrado
    assert "Equilibrado" in mode_preset("standard")
    assert "Abogado del diablo" in mode_preset("adversarial")
    # Default fallback is standard
    assert "Equilibrado" in mode_preset("unknown_mode")

def test_wrap_noncode():
    lines = [
        "This is a very short line.",
        "This is a much longer line that should probably be wrapped because it exceeds the specified maximum width for text wrapping in this function."
    ]
    wrapped = wrap_noncode(lines, width=50)
    assert "This is a very short line." in wrapped
    # The long line should be split, so it contains newlines.
    assert "\n" in wrapped

def test_sha256_file():
    with tempfile.NamedTemporaryFile("w+", delete=False) as f:
        f.write("hello world")
        tmp_name = f.name
        
    try:
        h = sha256_file(tmp_name)
        # sha256 of "hello world" is b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9
        assert h == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    finally:
        os.remove(tmp_name)
