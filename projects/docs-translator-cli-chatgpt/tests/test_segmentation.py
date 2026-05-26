from __future__ import annotations

from docstrans.services.segmentation import split_text


def test_segmentation_respects_chunk_size():
    text = "One two three four five six seven eight nine ten"
    chunks = split_text(text, chunk_size=12)
    assert chunks
    assert all(len(chunk) <= 12 for chunk in chunks)


def test_segmentation_preserves_blank_lines_as_segments():
    chunks = split_text("A\n\nB", chunk_size=500)
    assert chunks == ["A", "\n\n", "B"]
