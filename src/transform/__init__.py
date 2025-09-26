"""
Módulo de Transformação - Pipeline de Cotações Cambiais
MBA em Data Engineering

Este módulo contém as classes e funções responsáveis pela 
transformação de dados da camada Raw para Silver.

Classes principais:
- DataTransformer: Orquestrador principal da transformação
- DataQualityChecker: Verificador de qualidade dos dados
- ExchangeRateRecord: Modelo Pydantic para validação

Funcionalidades:
- Leitura de dados JSON da camada Raw
- Normalização e estruturação de dados
- Validação com Pydantic
- Verificação de qualidade
- Salvamento em formato Parquet (Silver layer)
"""

from .data_processor import DataTransformer, DataQualityChecker, ExchangeRateRecord

__version__ = "1.0.0"
__all__ = ["DataTransformer", "DataQualityChecker", "ExchangeRateRecord"]