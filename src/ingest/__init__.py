"""
Módulo de Ingestão - Pipeline de Cotações Cambiais
MBA em Data Engineering

Este módulo contém as classes e funções responsáveis pela 
coleta de dados da Exchange Rate API.

Classes principais:
- ExchangeRateAPIClient: Cliente para interagir com a API
- DataIngester: Orquestrador da ingestão e armazenamento
"""

from .exchange_api import ExchangeRateAPIClient, DataIngester

__version__ = "1.0.0"
__all__ = ["ExchangeRateAPIClient", "DataIngester"]