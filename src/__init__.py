"""
Pipeline de Cotações Cambiais com Python + LLM
MBA em Data Engineering - Projeto Final

Este pacote implementa um pipeline completo de dados para:
1. Ingestão de cotações cambiais via API
2. Transformação e validação dos dados  
3. Armazenamento em camadas (raw/silver/gold)
4. Geração de insights via LLM

Módulos:
- ingest: Coleta de dados da API
- transform: Processamento e limpeza dos dados
- load: Armazenamento final em Parquet
- llm: Integração com ChatGPT para insights
- utils: Utilitários e funções auxiliares
"""

__version__ = "1.0.0"
__author__ = "MBA Data Engineering"
__description__ = "Pipeline de Cotações Cambiais com Python + LLM"