"""Tests for text segmentation."""

from __future__ import annotations

from docstrans.services.segmentation import segment_text


def test_empty_text_returns_empty():
    assert segment_text("") == []
    assert segment_text("   ") == []


def test_short_text_is_single_segment():
    result = segment_text("Hello world", chunk_size=4000)
    assert result == ["Hello world"]


def test_paragraphs_split_by_blank_lines():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    result = segment_text(text, chunk_size=4000)
    assert len(result) == 3


def test_long_paragraph_split_by_sentences():
    # Create a paragraph longer than chunk_size
    sentences = ["This is sentence number " + str(i) + "." for i in range(100)]
    text = " ".join(sentences)
    result = segment_text(text, chunk_size=200)
    assert len(result) > 1
    for seg in result:
        assert len(seg) <= 300  # allow some slack for sentence boundaries


def test_very_long_word_becomes_single_segment():
    long_word = "a" * 100
    result = segment_text(long_word, chunk_size=50)
    assert len(result) == 1
    assert result[0] == long_word
