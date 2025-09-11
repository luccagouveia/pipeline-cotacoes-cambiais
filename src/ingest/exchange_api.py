"""
Módulo de Ingestão da Exchange Rate API
Pipeline de Cotações Cambiais - MBA Data Engineering

Este módulo é responsável por:
1. Conectar com a Exchange Rate API
2. Coletar dados de cotações cambiais
3. Implementar retry logic e error handling
4. Salvar dados brutos em formato JSON
"""

import os
import json
import requests
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from pathlib import Path
import structlog
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logger estruturado
logger = structlog.get_logger()


class ExchangeRateAPIClient:
    """
    Cliente para interagir com a Exchange Rate API
    
    Atributos:
        api_key: Chave da API
        base_url: URL base da API
        timeout: Timeout para requisições
        retry_attempts: Número de tentativas em caso de falha
        retry_delay: Delay entre tentativas (segundos)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_delay: int = 5
    ):
        """
        Inicializa o cliente da API
        
        Args:
            api_key: Chave da API (se None, pega do .env)
            base_url: URL base da API (se None, pega do .env)
            timeout: Timeout em segundos
            retry_attempts: Número de tentativas
            retry_delay: Delay entre tentativas
        """
        self.api_key = api_key or os.getenv('EXCHANGE_API_KEY')
        self.base_url = base_url or os.getenv('EXCHANGE_API_BASE_URL', 'https://v6.exchangerate-api.com/v6')
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # Validações
        if not self.api_key:
            raise ValueError("API key não encontrada. Verifique o arquivo .env")
        
        logger.info(
            "Cliente API inicializado",
            api_key_length=len(self.api_key),
            base_url=self.base_url,
            timeout=self.timeout,
            retry_attempts=self.retry_attempts
        )
    
    def get_latest_rates(self, base_currency: str = 'USD') -> Dict[str, Any]:
        """
        Busca as cotações mais recentes para a moeda base especificada
        
        Args:
            base_currency: Código da moeda base (ex: 'USD', 'EUR')
            
        Returns:
            Dict com os dados da API
            
        Raises:
            requests.RequestException: Em caso de erro na requisição
            ValueError: Em caso de resposta inválida da API
        """
        url = f"{self.base_url}/{self.api_key}/latest/{base_currency}"
        
        logger.info(
            "Iniciando coleta de cotações",
            base_currency=base_currency,
            url=url.replace(self.api_key, "***")  # Mascarar API key nos logs
        )
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                logger.info("Fazendo requisição", attempt=attempt, max_attempts=self.retry_attempts)
                
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={
                        'User-Agent': 'Pipeline-Cotacoes-Cambiais/1.0',
                        'Accept': 'application/json'
                    }
                )
                
                # Log da resposta
                logger.info(
                    "Resposta recebida",
                    status_code=response.status_code,
                    response_size=len(response.content),
                    attempt=attempt
                )
                
                # Verificar se a requisição foi bem-sucedida
                response.raise_for_status()
                
                # Parse do JSON
                data = response.json()
                
                # Validar estrutura da resposta
                self._validate_api_response(data)
                
                logger.info(
                    "Cotações coletadas com sucesso",
                    base_currency=base_currency,
                    num_rates=len(data.get('conversion_rates', {})),
                    last_update=data.get('time_last_update_utc', 'N/A')
                )
                
                return data
                
            except requests.exceptions.Timeout:
                logger.warning(
                    "Timeout na requisição",
                    attempt=attempt,
                    timeout=self.timeout
                )
                
            except requests.exceptions.ConnectionError:
                logger.warning(
                    "Erro de conexão",
                    attempt=attempt
                )
                
            except requests.exceptions.HTTPError as e:
                logger.error(
                    "Erro HTTP",
                    attempt=attempt,
                    status_code=response.status_code,
                    error=str(e)
                )
                
                # Se for erro 4xx, não vale a pena tentar novamente
                if 400 <= response.status_code < 500:
                    raise
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(
                    "Erro no processamento da resposta",
                    attempt=attempt,
                    error=str(e)
                )
                
            # Se não for a última tentativa, esperar antes de tentar novamente
            if attempt < self.retry_attempts:
                logger.info(f"Aguardando {self.retry_delay}s antes da próxima tentativa...")
                time.sleep(self.retry_delay)
        
        # Se chegou aqui, todas as tentativas falharam
        error_msg = f"Falha ao coletar cotações após {self.retry_attempts} tentativas"
        logger.error(error_msg, base_currency=base_currency)
        raise requests.RequestException(error_msg)
    
    def _validate_api_response(self, data: Dict[str, Any]) -> None:
        """
        Valida se a resposta da API tem a estrutura esperada
        
        Args:
            data: Dados retornados pela API
            
        Raises:
            ValueError: Se a estrutura estiver inválida
        """
        required_fields = ['result', 'base_code', 'conversion_rates']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo obrigatório '{field}' não encontrado na resposta da API")
        
        if data['result'] != 'success':
            raise ValueError(f"API retornou erro: {data.get('error-type', 'desconhecido')}")
        
        if not isinstance(data['conversion_rates'], dict):
            raise ValueError("Campo 'conversion_rates' deve ser um dicionário")
        
        if len(data['conversion_rates']) == 0:
            raise ValueError("Nenhuma cotação encontrada na resposta")


class DataIngester:
    """
    Classe responsável por orquestrar a ingestão e armazenamento dos dados
    """
    
    def __init__(self, raw_data_path: str = 'data/raw'):
        """
        Inicializa o ingester
        
        Args:
            raw_data_path: Caminho para salvar dados brutos
        """
        self.raw_data_path = Path(raw_data_path)
        self.api_client = ExchangeRateAPIClient()
        
        # Criar diretório se não existir
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "DataIngester inicializado",
            raw_data_path=str(self.raw_data_path)
        )
    
    def collect_and_save_daily_rates(
        self, 
        base_currency: str = 'USD',
        target_date: Optional[date] = None
    ) -> str:
        """
        Coleta cotações e salva no formato YYYY-MM-DD.json
        
        Args:
            base_currency: Moeda base para cotações
            target_date: Data alvo (se None, usa data atual)
            
        Returns:
            Caminho do arquivo salvo
        """
        if target_date is None:
            target_date = date.today()
            
        timestamp_start = datetime.now()
        
        logger.info(
            "Iniciando coleta diária de cotações",
            base_currency=base_currency,
            target_date=target_date.isoformat(),
            timestamp=timestamp_start.isoformat()
        )
        
        try:
            # Coletar dados da API
            raw_data = self.api_client.get_latest_rates(base_currency)
            
            # Adicionar metadados do pipeline
            enriched_data = {
                "pipeline_metadata": {
                    "collection_timestamp": timestamp_start.isoformat(),
                    "collection_date": target_date.isoformat(),
                    "base_currency": base_currency,
                    "pipeline_version": "1.0.0"
                },
                "api_response": raw_data
            }
            
            # Definir nome do arquivo
            filename = f"{target_date.strftime('%Y-%m-%d')}.json"
            filepath = self.raw_data_path / filename
            
            # Salvar arquivo JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(enriched_data, f, indent=2, ensure_ascii=False)
            
            # Calcular tempo de execução
            execution_time = (datetime.now() - timestamp_start).total_seconds()
            
            logger.info(
                "Dados coletados e salvos com sucesso",
                filepath=str(filepath),
                file_size_kb=filepath.stat().st_size / 1024,
                num_rates=len(raw_data.get('conversion_rates', {})),
                execution_time_seconds=execution_time,
                base_currency=base_currency
            )
            
            return str(filepath)
            
        except Exception as e:
            logger.error(
                "Erro durante coleta de dados",
                error=str(e),
                error_type=type(e).__name__,
                base_currency=base_currency,
                target_date=target_date.isoformat()
            )
            raise


def main():
    """
    Função principal para executar a ingestão de dados
    """
    logger.info("=== INICIANDO PIPELINE DE INGESTÃO ===")
    
    try:
        # Inicializar ingester
        ingester = DataIngester()
        
        # Coletar dados para hoje
        filepath = ingester.collect_and_save_daily_rates()
        
        logger.info(
            "Pipeline de ingestão concluído com sucesso",
            output_file=filepath
        )
        
    except Exception as e:
        logger.error(
            "Pipeline de ingestão falhou",
            error=str(e),
            error_type=type(e).__name__
        )
        raise


if __name__ == "__main__":
    main()