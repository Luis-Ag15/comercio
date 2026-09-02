"""
Cifrado transparente de campos sensibles usando Fernet (cryptography).

La clave se deriva del SECRET_KEY de Django, por lo que no requiere
ninguna configuración adicional. Los datos se cifran al guardar en la BD
y se descifran automáticamente al leer, sin modificar las vistas ni los
formularios existentes.

Uso:
    from core.encryption import EncryptedCharField, EncryptedTextField

    class MiModelo(models.Model):
        nombre = EncryptedCharField(max_length=100)
        notas  = EncryptedTextField(blank=True)
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


# ──────────────────────────────────────────────────────────────────────────────
# Clave Fernet derivada del SECRET_KEY de Django
# ──────────────────────────────────────────────────────────────────────────────

def _get_fernet() -> Fernet:
    """
    Deriva una clave Fernet de 32 bytes a partir del SECRET_KEY de Django
    usando SHA-256. La codifica en base64-urlsafe para cumplir el formato
    esperado por Fernet.
    """
    secret = settings.SECRET_KEY.encode()
    key_bytes = hashlib.sha256(secret).digest()          # 32 bytes
    fernet_key = base64.urlsafe_b64encode(key_bytes)     # 44 chars urlsafe-b64
    return Fernet(fernet_key)


# ──────────────────────────────────────────────────────────────────────────────
# Funciones de cifrado/descifrado
# ──────────────────────────────────────────────────────────────────────────────

def encrypt_value(value: str) -> str:
    """Cifra un texto plano y devuelve el token Fernet como string."""
    if not value:
        return value
    fernet = _get_fernet()
    token = fernet.encrypt(value.encode('utf-8'))
    return token.decode('utf-8')


def decrypt_value(token: str) -> str:
    """
    Descifra un token Fernet y devuelve el texto original.
    Si el valor no está cifrado (p.ej. datos históricos sin cifrar),
    lo devuelve tal cual para mantener compatibilidad.
    """
    if not token:
        return token
    try:
        fernet = _get_fernet()
        plaintext = fernet.decrypt(token.encode('utf-8'))
        return plaintext.decode('utf-8')
    except (InvalidToken, Exception):
        # Datos existentes sin cifrar: se devuelven sin modificar
        return token


def _is_fernet_token(value: str) -> bool:
    """Detecta si un string ya es un token Fernet cifrado."""
    if not isinstance(value, str):
        return False
    return value.startswith('gAAAAA') and len(value) > 50


# ──────────────────────────────────────────────────────────────────────────────
# Campo personalizado de Django
# ──────────────────────────────────────────────────────────────────────────────

class EncryptedMixin:
    """
    Mixin que añade cifrado/descifrado transparente a cualquier campo de Django.

    • from_db_value: descifra al leer desde la base de datos.
    • get_prep_value: cifra antes de escribir en la BD (solo si no está ya cifrado).
    • to_python:      devuelve el valor limpio para formularios.

    NO usa descriptor Python para no interferir con el ciclo de vida
    de ModelForm (que asigna directamente cleaned_data a la instancia).
    """

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value) if value else value

    def to_python(self, value):
        if value is None:
            return value
        # Si ya es un token cifrado (viene directo de BD sin pasar por from_db_value),
        # descifrar. Si es texto plano (viene de un form), dejarlo como está.
        if _is_fernet_token(value):
            return decrypt_value(value)
        return value

    def get_prep_value(self, value):
        """Cifra antes de escribir en la BD. No cifra si ya es un token Fernet."""
        prepped = super().get_prep_value(value)
        if not prepped:
            return prepped
        if _is_fernet_token(prepped):
            # Ya está cifrado — no cifrar de nuevo
            return prepped
        return encrypt_value(prepped)


class EncryptedCharField(EncryptedMixin, models.TextField):
    """
    Campo de texto corto (equivalente a CharField) con cifrado Fernet.
    Se almacena como TextField en la BD porque el token cifrado es más largo
    que el valor original (overhead de ~100+ caracteres base64).
    """

    def __init__(self, *args, **kwargs):
        # max_length es irrelevante para TextField pero lo aceptamos por
        # compatibilidad con la definición del modelo original.
        kwargs.pop('max_length', None)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs


class EncryptedTextField(EncryptedMixin, models.TextField):
    """Campo de texto largo con cifrado Fernet."""
    pass
