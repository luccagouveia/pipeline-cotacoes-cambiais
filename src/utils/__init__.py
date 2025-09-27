"""
Utilitários - Pipeline de Cotações Cambiais
MBA em Data Engineering

Este módulo contém funções e classes auxiliares utilizadas
em todo o pipeline.

Módulos:
- logging_config: Configuração de logging estruturado
- data_validator: Validação e verificação de qualidade dos dados
"""

from .logging_config import setup_logging, get_logger, LoggerMixin
from .data_validator import (
    CurrencyValidator, 
    ExchangeRateValidator, 
    TimestampValidator, 
    DataFrameValidator,
    generate_validation_summary
)

__version__ = "1.0.0"
__all__ = [
    "setup_logging", 
    "get_logger", 
    "LoggerMixin",
    "CurrencyValidator",
    "ExchangeRateValidator", 
    "TimestampValidator",
    "DataFrameValidator",
    "generate_validation_summary"
]