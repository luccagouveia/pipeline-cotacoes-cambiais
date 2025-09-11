"""
Configuração de Logging Estruturado
Pipeline de Cotações Cambiais - MBA Data Engineering

Este módulo configura o logging estruturado usando structlog
para facilitar o monitoramento e debugging do pipeline.
"""

import os
import sys
import logging
import structlog
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file_path: str = "logs"
) -> None:
    """
    Configura o sistema de logging estruturado
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        log_format: Formato do log ("json" ou "console")
        log_file_path: Diretório para arquivos de log
    """
    
    # Criar diretório de logs se não existir
    Path(log_file_path).mkdir(parents=True, exist_ok=True)
    
    # Configurar nível de log
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configurar formato baseado no ambiente
    if log_format == "json":
        # Formato JSON estruturado (produção)
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ]
    else:
        # Formato colorido para console (desenvolvimento)
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    # Configurar structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging padrão do Python
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )
    
    # Configurar handler para arquivo
    log_filename = f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
    log_filepath = Path(log_file_path) / log_filename
    
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(numeric_level)
    
    # Adicionar handler ao logger root
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    # Log de inicialização
    logger = structlog.get_logger()
    logger.info(
        "Sistema de logging configurado",
        log_level=log_level,
        log_format=log_format,
        log_file=str(log_filepath),
        processors_count=len(processors)
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Retorna um logger configurado
    
    Args:
        name: Nome do logger (opcional)
        
    Returns:
        Logger estruturado configurado
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin para adicionar logging a qualquer classe
    """
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """
        Propriedade que retorna um logger com o nome da classe
        """
        return structlog.get_logger(self.__class__.__name__)


# Configurar logging quando o módulo for importado
def configure_default_logging():
    """
    Configura logging com valores padrão do ambiente
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_format = os.getenv('LOG_FORMAT', 'console')  # console para desenvolvimento
    
    setup_logging(
        log_level=log_level,
        log_format=log_format,
        log_file_path='logs'
    )


# Auto-configuração se não estiver em modo de teste
if not any('pytest' in arg or 'test' in arg for arg in sys.argv):
    configure_default_logging()