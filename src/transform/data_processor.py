"""
Módulo de Transformação de Dados - Silver Layer
Pipeline de Cotações Cambiais - MBA Data Engineering

Este módulo é responsável por:
1. Ler dados JSON da camada Raw
2. Normalizar estrutura de dados
3. Aplicar validações de qualidade
4. Transformar em formato tabular
5. Salvar em Parquet na camada Silver
"""

import json
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import structlog
from pydantic import BaseModel, validator, ValidationError
import pyarrow as pa
import pyarrow.parquet as pq

logger = structlog.get_logger()


class ExchangeRateRecord(BaseModel):
    """
    Modelo Pydantic para validação de registros de cotação
    """
    base_currency: str
    target_currency: str
    exchange_rate: float
    collection_timestamp: datetime
    collection_date: date
    last_update_timestamp: datetime
    pipeline_version: str
    
    @validator('base_currency', 'target_currency')
    def validate_currency_code(cls, v):
        """Valida código de moeda - deve ter 3 caracteres alfabéticos"""
        if not v or len(v) != 3 or not v.isalpha():
            raise ValueError('Código de moeda deve ter 3 letras (ex: USD, BRL)')
        return v.upper()
    
    @validator('exchange_rate')
    def validate_exchange_rate(cls, v):
        """Valida taxa de câmbio - deve ser positiva e finita"""
        if v <= 0:
            raise ValueError('Taxa de câmbio deve ser positiva')
        if not pd.isna(v) and (v == float('inf') or v != v):  # Check for inf and NaN
            raise ValueError('Taxa de câmbio deve ser um número válido')
        if v > 1000000:  # Sanity check
            raise ValueError('Taxa de câmbio parece muito alta (>1M)')
        return round(v, 8)  # Precisão de 8 casas decimais
    
    @validator('collection_timestamp', 'last_update_timestamp')
    def validate_timestamps(cls, v):
        """Valida timestamps"""
        if v.year < 2000 or v.year > 2030:
            raise ValueError('Timestamp fora do intervalo válido (2000-2030)')
        return v

class DataQualityChecker:
    """
    Classe para verificações de qualidade dos dados
    """
    
    def __init__(self):
        self.quality_issues = []
        self.logger = structlog.get_logger("DataQualityChecker")
    
    def check_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Verifica completude dos dados
        """
        total_records = len(df)
        missing_data = df.isnull().sum()
        
        quality_report = {
            'total_records': total_records,
            'missing_values': missing_data.to_dict(),
            'completeness_score': 1 - (missing_data.sum() / (len(df.columns) * total_records))
        }
        
        # Log issues
        if missing_data.sum() > 0:
            self.quality_issues.append(f"Dados faltantes encontrados: {missing_data.to_dict()}")
            
        return quality_report
    
    def check_currency_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Verifica consistência dos códigos de moeda
        """
        base_currencies = df['base_currency'].unique()
        target_currencies = df['target_currency'].unique()
        
        # Verificar se códigos têm 3 caracteres
        invalid_codes = []
        for currency in list(base_currencies) + list(target_currencies):
            if len(currency) != 3 or not currency.isalpha():
                invalid_codes.append(currency)
        
        quality_report = {
            'unique_base_currencies': len(base_currencies),
            'unique_target_currencies': len(target_currencies),
            'invalid_currency_codes': invalid_codes,
            'total_currency_pairs': len(df)
        }
        
        if invalid_codes:
            self.quality_issues.append(f"Códigos de moeda inválidos: {invalid_codes}")
            
        return quality_report
    
    def check_rate_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Verifica distribuição das taxas de câmbio
        """
        rates = df['exchange_rate']
        
        quality_report = {
            'min_rate': float(rates.min()),
            'max_rate': float(rates.max()),
            'mean_rate': float(rates.mean()),
            'median_rate': float(rates.median()),
            'std_rate': float(rates.std()),
            'zero_rates': int((rates == 0).sum()),
            'negative_rates': int((rates < 0).sum()),
            'extreme_rates': int((rates > 1000).sum())
        }
        
        # Identificar possíveis problemas
        if quality_report['zero_rates'] > 0:
            self.quality_issues.append(f"Encontradas {quality_report['zero_rates']} taxas zeradas")
        if quality_report['negative_rates'] > 0:
            self.quality_issues.append(f"Encontradas {quality_report['negative_rates']} taxas negativas")
        if quality_report['extreme_rates'] > 0:
            self.quality_issues.append(f"Encontradas {quality_report['extreme_rates']} taxas extremas (>1000)")
            
        return quality_report
    
    def generate_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Gera relatório completo de qualidade
        """
        self.quality_issues = []  # Reset issues
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'dataset_info': {
                'total_records': len(df),
                'columns': list(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
            },
            'completeness': self.check_completeness(df),
            'currency_consistency': self.check_currency_consistency(df),
            'rate_distribution': self.check_rate_distribution(df),
            'quality_issues': self.quality_issues,
            'overall_quality_score': self._calculate_overall_score(df)
        }
        
        return report
    
    def _calculate_overall_score(self, df: pd.DataFrame) -> float:
        """
        Calcula score geral de qualidade (0-1)
        """
        score = 1.0
        
        # Penalizar por dados faltantes
        missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
        score -= missing_ratio * 0.3
        
        # Penalizar por taxas inválidas
        invalid_rates = ((df['exchange_rate'] <= 0) | 
                        (df['exchange_rate'] > 1000000)).sum()
        if len(df) > 0:
            score -= (invalid_rates / len(df)) * 0.4
        
        # Penalizar por códigos de moeda inválidos
        invalid_currencies = 0
        for col in ['base_currency', 'target_currency']:
            invalid_currencies += df[col].apply(
                lambda x: len(str(x)) != 3 or not str(x).isalpha()
            ).sum()
        
        if len(df) > 0:
            score -= (invalid_currencies / (len(df) * 2)) * 0.3
        
        return max(0.0, score)


class DataTransformer:
    """
    Classe principal para transformação de dados
    """
    
    def __init__(self, raw_data_path: str = 'data/raw', silver_data_path: str = 'data/silver'):
        """
        Inicializa o transformador
        
        Args:
            raw_data_path: Caminho dos dados brutos
            silver_data_path: Caminho para dados transformados
        """
        self.raw_data_path = Path(raw_data_path)
        self.silver_data_path = Path(silver_data_path)
        self.quality_checker = DataQualityChecker()
        
        # Criar diretório silver se não existir
        self.silver_data_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "DataTransformer inicializado",
            raw_path=str(self.raw_data_path),
            silver_path=str(self.silver_data_path)
        )
    
    def load_raw_data(self, date_str: str) -> Dict[str, Any]:
        """
        Carrega dados JSON da camada Raw
        
        Args:
            date_str: Data no formato YYYY-MM-DD
            
        Returns:
            Dados JSON carregados
        """
        file_path = self.raw_data_path / f"{date_str}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        logger.info("Carregando dados brutos", file_path=str(file_path))
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validar estrutura básica
        if 'pipeline_metadata' not in data or 'api_response' not in data:
            raise ValueError("Estrutura de dados inválida no arquivo JSON")
        
        logger.info(
            "Dados brutos carregados",
            file_size_kb=file_path.stat().st_size / 1024,
            pipeline_version=data['pipeline_metadata'].get('pipeline_version', 'unknown')
        )
        
        return data
    
    def transform_to_tabular(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transforma dados JSON em formato tabular
        
        Args:
            raw_data: Dados brutos do JSON
            
        Returns:
            Lista de registros tabulares
        """
        logger.info("Iniciando transformação para formato tabular")
        
        # Extrair metadados
        metadata = raw_data['pipeline_metadata']
        api_response = raw_data['api_response']
        
        # Parse timestamps
        collection_timestamp = datetime.fromisoformat(metadata['collection_timestamp'])
        collection_date = date.fromisoformat(metadata['collection_date'])
        
        # Parse last update da API
        last_update_unix = api_response.get('time_last_update_unix')
        if last_update_unix:
            last_update_timestamp = datetime.fromtimestamp(last_update_unix)
        else:
            last_update_timestamp = collection_timestamp
        
        # Extrair moeda base e taxas
        base_currency = api_response['base_code']
        conversion_rates = api_response['conversion_rates']
        
        # Transformar cada taxa em um registro
        records = []
        for target_currency, exchange_rate in conversion_rates.items():
            record = {
                'base_currency': base_currency,
                'target_currency': target_currency,
                'exchange_rate': float(exchange_rate),
                'collection_timestamp': collection_timestamp,
                'collection_date': collection_date,
                'last_update_timestamp': last_update_timestamp,
                'pipeline_version': metadata['pipeline_version']
            }
            records.append(record)
        
        logger.info(
            "Transformação tabular concluída",
            total_records=len(records),
            base_currency=base_currency,
            unique_targets=len(conversion_rates)
        )
        
        return records
    
    def validate_records(self, records: List[Dict[str, Any]]) -> List[ExchangeRateRecord]:
        """
        Valida registros usando Pydantic
        
        Args:
            records: Lista de registros não validados
            
        Returns:
            Lista de registros validados
        """
        logger.info("Iniciando validação de registros", total_records=len(records))
        
        validated_records = []
        validation_errors = []
        
        for i, record in enumerate(records):
            try:
                validated_record = ExchangeRateRecord(**record)
                validated_records.append(validated_record)
            except ValidationError as e:
                error_info = {
                    'record_index': i,
                    'record': record,
                    'errors': e.errors()
                }
                validation_errors.append(error_info)
                logger.warning(
                    "Erro de validação no registro",
                    record_index=i,
                    errors=e.errors()
                )
        
        logger.info(
            "Validação concluída",
            valid_records=len(validated_records),
            invalid_records=len(validation_errors),
            validation_success_rate=len(validated_records) / len(records) if records else 0
        )
        
        if validation_errors:
            logger.error(
                "Registros com erro de validação encontrados",
                total_errors=len(validation_errors),
                sample_errors=validation_errors[:3]  # Primeiros 3 erros como exemplo
            )
        
        return validated_records
    
    def create_dataframe(self, validated_records: List[ExchangeRateRecord]) -> pd.DataFrame:
        """
        Cria DataFrame a partir dos registros validados
        
        Args:
            validated_records: Lista de registros validados
            
        Returns:
            DataFrame pandas
        """
        logger.info("Criando DataFrame", total_records=len(validated_records))
        
        # Converter registros Pydantic para dicts
        records_dict = []
        for record in validated_records:
            # Compatibilidade Pydantic v1/v2
            if hasattr(record, 'model_dump'):
                records_dict.append(record.model_dump())  # v2
            else:
                records_dict.append(record.dict())  # v1
        
        # Criar DataFrame
        df = pd.DataFrame(records_dict)
        
        # Otimizar tipos de dados
        df = self._optimize_datatypes(df)
        
        logger.info(
            "DataFrame criado",
            shape=df.shape,
            columns=list(df.columns),
            memory_usage_mb=df.memory_usage(deep=True).sum() / 1024 / 1024
        )
        
        return df
    
    def _optimize_datatypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Otimiza tipos de dados do DataFrame
        """
        # REMOVIDO: Conversão para categoria que estava causando erro
        # categorical_columns = ['base_currency', 'target_currency', 'pipeline_version']
        # for col in categorical_columns:
        #     if col in df.columns:
        #         df[col] = df[col].astype('category')
        
        # Converter exchange_rate para float32 (suficiente para taxas)
        if 'exchange_rate' in df.columns:
            df['exchange_rate'] = df['exchange_rate'].astype('float32')
        
        return df
    
    def save_to_parquet(self, df: pd.DataFrame, date_str: str) -> str:
        """
        Salva DataFrame em formato Parquet
        
        Args:
            df: DataFrame a ser salvo
            date_str: Data para nome do arquivo
            
        Returns:
            Caminho do arquivo salvo
        """
        # Nome do arquivo
        filename = f"exchange_rates_{date_str}.parquet"
        filepath = self.silver_data_path / filename
        
        logger.info("Salvando em formato Parquet", filepath=str(filepath))
        
        # Salvar com compressão
        df.to_parquet(
            filepath,
            engine='pyarrow',
            compression='snappy',
            index=False
        )
        
        # Verificar arquivo salvo
        file_size_kb = filepath.stat().st_size / 1024
        
        logger.info(
            "Arquivo Parquet salvo com sucesso",
            filepath=str(filepath),
            file_size_kb=file_size_kb,
            compression_ratio=file_size_kb / (df.memory_usage(deep=True).sum() / 1024)
        )
        
        return str(filepath)
    
    def process_date(self, target_date: Union[str, date]) -> Dict[str, Any]:
        """
        Processa dados para uma data específica
        
        Args:
            target_date: Data a ser processada (string YYYY-MM-DD ou objeto date)
            
        Returns:
            Relatório do processamento
        """
        # Converter para string se necessário
        if isinstance(target_date, date):
            date_str = target_date.strftime('%Y-%m-%d')
        else:
            date_str = target_date
        
        start_time = datetime.now()
        
        logger.info(
            "=== INICIANDO TRANSFORMAÇÃO PARA CAMADA SILVER ===",
            target_date=date_str,
            start_time=start_time.isoformat()
        )
        
        try:
            # 1. Carregar dados brutos
            raw_data = self.load_raw_data(date_str)
            
            # 2. Transformar para formato tabular
            records = self.transform_to_tabular(raw_data)
            
            # 3. Validar registros
            validated_records = self.validate_records(records)
            
            if not validated_records:
                raise ValueError("Nenhum registro válido após validação")
            
            # 4. Criar DataFrame
            df = self.create_dataframe(validated_records)
            
            # 5. Verificar qualidade dos dados
            quality_report = self.quality_checker.generate_quality_report(df)
            
            # 6. Salvar em Parquet
            output_filepath = self.save_to_parquet(df, date_str)
            
            # Calcular tempo de execução
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Relatório final
            report = {
                'status': 'success',
                'target_date': date_str,
                'execution_time_seconds': execution_time,
                'input': {
                    'raw_file': str(self.raw_data_path / f"{date_str}.json"),
                    'total_raw_records': len(records)
                },
                'processing': {
                    'validated_records': len(validated_records),
                    'invalid_records': len(records) - len(validated_records),
                    'validation_success_rate': len(validated_records) / len(records)
                },
                'output': {
                    'silver_file': output_filepath,
                    'final_records': len(df),
                    'columns': list(df.columns)
                },
                'quality': quality_report
            }
            
            logger.info(
                "=== TRANSFORMAÇÃO CONCLUÍDA COM SUCESSO ===",
                target_date=date_str,
                execution_time_seconds=execution_time,
                final_records=len(df),
                quality_score=quality_report['overall_quality_score']
            )
            
            return report
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            logger.error(
                "=== TRANSFORMAÇÃO FALHOU ===",
                target_date=date_str,
                execution_time_seconds=execution_time,
                error=str(e),
                error_type=type(e).__name__
            )
            
            return {
                'status': 'error',
                'target_date': date_str,
                'execution_time_seconds': execution_time,
                'error': str(e),
                'error_type': type(e).__name__
            }


def main():
    """
    Função principal para executar transformação
    """
    logger.info("=== INICIANDO PIPELINE DE TRANSFORMAÇÃO ===")
    
    try:
        # Inicializar transformer
        transformer = DataTransformer()
        
        # Processar dados de hoje
        today = date.today()
        report = transformer.process_date(today)
        
        if report['status'] == 'success':
            logger.info(
                "Pipeline de transformação concluído com sucesso",
                output_file=report['output']['silver_file'],
                quality_score=report['quality']['overall_quality_score']
            )
        else:
            logger.error(
                "Pipeline de transformação falhou",
                error=report['error']
            )
            
    except Exception as e:
        logger.error(
            "Erro crítico no pipeline de transformação",
            error=str(e),
            error_type=type(e).__name__
        )
        raise


if __name__ == "__main__":
    main()