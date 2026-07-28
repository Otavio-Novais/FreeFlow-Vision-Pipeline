"""
Módulo de persistência de dados para o sistema Free Flow.

Este pacote gerencia todas as operações de banco de dados,
incluindo modelagem relacional, registro de transações e 
cruzamento com tags OBO.
"""

from .connection import DatabaseConnection
from .repository import TransactionRepository

# Define a API pública do pacote
__all__ = [
    'DatabaseConnection',
    'TransactionRepository',
]

# Versão do módulo (útil para debugging)
__version__ = '1.0.0'