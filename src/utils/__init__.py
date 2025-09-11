"""
Utilitários - Pipeline de Cotações Cambiais
MBA em Data Engineering

Este módulo contém funções e classes auxiliares utilizadas
em todo o pipeline.

Módulos:
- logging_config: Configuração de logging estruturado
"""

from .logging_config import setup_logging, get_logger, LoggerMixin

__version__ = "1.0.0"
__all__ = ["setup_logging", "get_logger", "LoggerMixin"]