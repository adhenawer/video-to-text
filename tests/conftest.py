"""Shared fixtures for all tests."""
import os
import sys
import tempfile

import pytest

# Add src/ to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a temporary directory."""
    return tmp_path


@pytest.fixture
def sample_translated_txt(tmp_path):
    """Create a sample translated .txt file with sections."""
    content = """================================================================================
INTRODUÇÃO

Este é o primeiro parágrafo da introdução. Ele contém informações importantes sobre o tema.

Este é o segundo parágrafo com mais detalhes.

================================================================================
CONCEITOS FUNDAMENTAIS

Aqui explicamos os conceitos fundamentais do assunto.

Um exemplo prático é apresentado nesta seção.

================================================================================
CONCLUSÃO

Resumo final com as principais conclusões do artigo.
"""
    path = tmp_path / "test_pt.txt"
    path.write_text(content)
    return str(path)


@pytest.fixture
def sample_slides_json(tmp_path):
    """Create a sample slides JSON manifest."""
    import json
    slides = [
        {"timestamp": 0, "timestamp_fmt": "0:00", "path": "img/test/slide-0001.jpg", "nearest_text": "intro"},
        {"timestamp": 60, "timestamp_fmt": "1:00", "path": "img/test/slide-0002.jpg", "nearest_text": "concepts"},
        {"timestamp": 120, "timestamp_fmt": "2:00", "path": "img/test/slide-0003.jpg", "nearest_text": "conclusion"},
    ]
    path = tmp_path / "slides.json"
    path.write_text(json.dumps(slides))
    return str(path)
