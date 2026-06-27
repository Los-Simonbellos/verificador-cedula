"""Tests unitarios para utils/validators.py — función pura, sin async."""

import pytest

from app.core.exceptions import InvalidCedulaFormatError
from app.utils.validators import normalize_cedula


class TestNormalizeCedula:
    def test_formato_v_simple(self):
        assert normalize_cedula("V12345678") == ("V", "12345678")

    def test_formato_e_extranjero(self):
        assert normalize_cedula("E11223344") == ("E", "11223344")

    def test_minusculas_normalizadas(self):
        assert normalize_cedula("v12345678") == ("V", "12345678")

    def test_con_guiones_y_puntos(self):
        assert normalize_cedula("v-12.345.678") == ("V", "12345678")

    def test_sin_prefijo_asume_venezolano(self):
        assert normalize_cedula("12345678") == ("V", "12345678")

    def test_con_espacios(self):
        assert normalize_cedula("  V 12345678  ".replace(" ", "")) == ("V", "12345678")

    def test_minimo_digitos(self):
        assert normalize_cedula("V123456") == ("V", "123456")

    def test_maximo_digitos(self):
        assert normalize_cedula("V123456789") == ("V", "123456789")

    def test_error_muy_corto(self):
        with pytest.raises(InvalidCedulaFormatError):
            normalize_cedula("V123")

    def test_error_muy_largo(self):
        with pytest.raises(InvalidCedulaFormatError):
            normalize_cedula("V1234567890")

    def test_error_prefijo_invalido(self):
        with pytest.raises(InvalidCedulaFormatError):
            normalize_cedula("X12345678")

    def test_error_letras_en_numero(self):
        with pytest.raises(InvalidCedulaFormatError):
            normalize_cedula("V1234567A")

    def test_error_vacio(self):
        with pytest.raises(InvalidCedulaFormatError):
            normalize_cedula("")

    def test_error_solo_letras(self):
        with pytest.raises(InvalidCedulaFormatError):
            normalize_cedula("abc")
