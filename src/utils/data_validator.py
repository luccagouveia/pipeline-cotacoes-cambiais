"""
Utilitário de Validação de Dados
Pipeline de Cotações Cambiais - MBA Data Engineering

Este módulo contém funções auxiliares para validação
e verificação de qualidade dos dados do pipeline.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
import structlog

logger = structlog.get_logger()


class CurrencyValidator:
    """
    Validador específico para códigos de moeda
    """
    
    # Lista de códigos de moeda ISO 4217 mais comuns
    VALID_CURRENCIES = {
        'USD', 'EUR', 'JPY', 'GBP', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD',
        'MXN', 'SGD', 'HKD', 'NOK', 'KRW', 'TRY', 'RUB', 'INR', 'BRL', 'ZAR',
        'DKK', 'PLN', 'TWD', 'THB', 'IDR', 'HUF', 'CZK', 'ILS', 'CLP', 'PHP',
        'AED', 'COP', 'SAR', 'MYR', 'RON', 'PEN', 'PKR', 'EGP', 'VND', 'QAR',
        'KWD', 'BHD', 'OMR', 'JOD', 'LBP', 'TND', 'DZD', 'MAD', 'IQD', 'LYD',
        'AOA', 'BWP', 'GHS', 'KES', 'MUR', 'NAD', 'NGN', 'SCR', 'TZS', 'UGX',
        'XAF', 'XOF', 'ZMW', 'ETB', 'MZN', 'RWF', 'XCD', 'BBD', 'BZD', 'BMD',
        'BND', 'KYD', 'GYD', 'JMD', 'SRD', 'TTD', 'BSD', 'CUP', 'DOP', 'GTQ',
        'HNL', 'HTG', 'NIO', 'PAB', 'PYG', 'UYU', 'BOB', 'CRC', 'SVC', 'AWG',
        'ANG', 'FJD', 'PGK', 'SBD', 'TOP', 'VUV', 'WST', 'XPF', 'KMF', 'MGA',
        'MVR', 'SZL', 'LSL', 'ERN', 'GMD', 'GNF', 'LRD', 'SLL', 'SLE', 'STN',
        'CVE', 'AFN', 'ALL', 'AMD', 'AZN', 'BYN', 'BAM', 'BGN', 'GEL', 'HRK',
        'ISK', 'KGS', 'KZT', 'MDL', 'MKD', 'RSD', 'TJS', 'TMT', 'UAH', 'UZS',
        'BDT', 'BTN', 'BIF', 'KHR', 'LKR', 'LAK', 'MMK', 'MNT', 'NPR', 'IRR',
        'YER', 'SOS', 'SDG', 'SYP', 'DJF', 'CDF', 'MWK', 'ZWL'
    }
    
    @classmethod
    def is_valid_currency_code(cls, currency_code: str) -> bool:
        """
        Verifica se o código de moeda é válido
        
        Args:
            currency_code: Código de moeda a ser validado
            
        Returns:
            True se válido, False caso contrário
        """
        if not isinstance(currency_code, str):
            return False
            
        currency_upper = currency_code.upper().strip()
        
        # Verificações básicas
        if len(currency_upper) != 3:
            return False
            
        if not currency_upper.isalpha():
            return False
            
        # Verificar se está na lista de moedas conhecidas
        return currency_upper in cls.VALID_CURRENCIES
    
    @classmethod
    def validate_currency_pair(cls, base: str, target: str) -> Tuple[bool, List[str]]:
        """
        Valida um par de moedas
        
        Args:
            base: Moeda base
            target: Moeda alvo
            
        Returns:
            Tuple com (is_valid, list_of_errors)
        """
        errors = []
        
        if not cls.is_valid_currency_code(base):
            errors.append(f"Código de moeda base inválido: {base}")
            
        if not cls.is_valid_currency_code(target):
            errors.append(f"Código de moeda alvo inválido: {target}")
            
        if base == target:
            errors.append("Moeda base e alvo não podem ser iguais")
            
        return len(errors) == 0, errors


class ExchangeRateValidator:
    """
    Validador específico para taxas de câmbio
    """
    
    # Limites razoáveis para taxas de câmbio
    MIN_RATE = 0.0001  # 1/10000
    MAX_RATE = 1000000.0  # 1 milhão
    
    @classmethod
    def is_valid_rate(cls, rate: float) -> bool:
        """
        Verifica se a taxa de câmbio é válida
        
        Args:
            rate: Taxa de câmbio
            
        Returns:
            True se válida, False caso contrário
        """
        try:
            rate_float = float(rate)
            
            # Verificar se é NaN ou infinito
            if pd.isna(rate_float) or np.isinf(rate_float):
                return False
                
            # Verificar limites
            if rate_float < cls.MIN_RATE or rate_float > cls.MAX_RATE:
                return False
                
            return True
            
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def detect_outliers(cls, rates: pd.Series, method: str = 'iqr') -> pd.Series:
        """
        Detecta outliers nas taxas de câmbio
        
        Args:
            rates: Série com taxas de câmbio
            method: Método de detecção ('iqr' ou 'zscore')
            
        Returns:
            Série boolean indicando outliers
        """
        if method == 'iqr':
            Q1 = rates.quantile(0.25)
            Q3 = rates.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return (rates < lower_bound) | (rates > upper_bound)
            
        elif method == 'zscore':
            z_scores = np.abs((rates - rates.mean()) / rates.std())
            return z_scores > 3
            
        else:
            raise ValueError(f"Método desconhecido: {method}")


class TimestampValidator:
    """
    Validador para timestamps
    """
    
    MIN_YEAR = 2000
    MAX_YEAR = 2030
    
    @classmethod
    def is_valid_timestamp(cls, timestamp: datetime) -> bool:
        """
        Verifica se timestamp é válido
        
        Args:
            timestamp: Timestamp a ser validado
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            if not isinstance(timestamp, datetime):
                return False
                
            if timestamp.year < cls.MIN_YEAR or timestamp.year > cls.MAX_YEAR:
                return False
                
            return True
            
        except Exception:
            return False
    
    @classmethod
    def is_reasonable_collection_time(cls, collection_ts: datetime, update_ts: datetime) -> bool:
        """
        Verifica se os timestamps de coleta e atualização são razoáveis
        
        Args:
            collection_ts: Timestamp de coleta
            update_ts: Timestamp de última atualização da API
            
        Returns:
            True se razoável, False caso contrário
        """
        try:
            # Coleta deve ser posterior à atualização (ou muito próxima)
            time_diff = (collection_ts - update_ts).total_seconds()
            
            # Permitir até 7 dias de diferença
            return -7 * 24 * 3600 <= time_diff <= 24 * 3600
            
        except Exception:
            return False


class DataFrameValidator:
    """
    Validador para DataFrames completos
    """
    
    REQUIRED_COLUMNS = {
        'base_currency', 'target_currency', 'exchange_rate',
        'collection_timestamp', 'collection_date', 'last_update_timestamp'
    }
    
    @classmethod
    def validate_schema(cls, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valida esquema do DataFrame
        
        Args:
            df: DataFrame a ser validado
            
        Returns:
            Tuple com (is_valid, list_of_errors)
        """
        errors = []
        
        # Verificar se DataFrame não está vazio
        if df.empty:
            errors.append("DataFrame está vazio")
            return False, errors
        
        # Verificar colunas obrigatórias
        missing_columns = cls.REQUIRED_COLUMNS - set(df.columns)
        if missing_columns:
            errors.append(f"Colunas obrigatórias faltando: {missing_columns}")
        
        # Verificar tipos de dados
        if 'exchange_rate' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['exchange_rate']):
                errors.append("Coluna 'exchange_rate' deve ser numérica")
        
        if 'collection_timestamp' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['collection_timestamp']):
                errors.append("Coluna 'collection_timestamp' deve ser datetime")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_data_consistency(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valida consistência dos dados
        
        Args:
            df: DataFrame a ser validado
            
        Returns:
            Relatório de consistência
        """
        report = {
            'total_records': len(df),
            'issues': [],
            'warnings': [],
            'statistics': {}
        }
        
        # Verificar duplicatas
        if df.duplicated().any():
            duplicates_count = df.duplicated().sum()
            report['issues'].append(f"Encontradas {duplicates_count} linhas duplicadas")
            report['statistics']['duplicates'] = duplicates_count
        
        # Verificar valores nulos
        null_counts = df.isnull().sum()
        if null_counts.any():
            report['warnings'].append("Valores nulos encontrados")
            report['statistics']['null_values'] = null_counts.to_dict()
        
        # Verificar consistência de datas
        if 'collection_date' in df.columns and 'collection_timestamp' in df.columns:
            date_mismatches = (df['collection_date'] != df['collection_timestamp'].dt.date).sum()
            if date_mismatches > 0:
                report['issues'].append(f"Inconsistência entre collection_date e collection_timestamp: {date_mismatches} registros")
        
        # Verificar moedas
        if 'base_currency' in df.columns:
            unique_base = df['base_currency'].nunique()
            if unique_base > 1:
                report['warnings'].append(f"Múltiplas moedas base encontradas: {unique_base}")
                
        # Verificar taxas extremas
        if 'exchange_rate' in df.columns:
            extreme_rates = ((df['exchange_rate'] < ExchangeRateValidator.MIN_RATE) | 
                           (df['exchange_rate'] > ExchangeRateValidator.MAX_RATE)).sum()
            if extreme_rates > 0:
                report['issues'].append(f"Taxas extremas encontradas: {extreme_rates} registros")
        
        return report


def generate_validation_summary(df: pd.DataFrame, currency_validator_results: Dict = None) -> Dict[str, Any]:
    """
    Gera resumo completo de validação
    
    Args:
        df: DataFrame validado
        currency_validator_results: Resultados do validador de moedas (opcional)
        
    Returns:
        Resumo completo de validação
    """
    logger.info("Gerando resumo de validação", records_count=len(df))
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'validation_results': {}
    }
    
    # Validação de schema
    schema_valid, schema_errors = DataFrameValidator.validate_schema(df)
    summary['validation_results']['schema'] = {
        'valid': schema_valid,
        'errors': schema_errors
    }
    
    # Validação de consistência
    consistency_report = DataFrameValidator.validate_data_consistency(df)
    summary['validation_results']['consistency'] = consistency_report
    
    # Validação de moedas (se fornecida)
    if currency_validator_results:
        summary['validation_results']['currencies'] = currency_validator_results
    
    # Validação de taxas
    if 'exchange_rate' in df.columns:
        rates_valid = df['exchange_rate'].apply(ExchangeRateValidator.is_valid_rate).all()
        outliers = ExchangeRateValidator.detect_outliers(df['exchange_rate'])
        
        summary['validation_results']['exchange_rates'] = {
            'all_valid': rates_valid,
            'outliers_count': outliers.sum(),
            'outlier_percentage': (outliers.sum() / len(df)) * 100,
            'rate_statistics': {
                'min': float(df['exchange_rate'].min()),
                'max': float(df['exchange_rate'].max()),
                'mean': float(df['exchange_rate'].mean()),
                'median': float(df['exchange_rate'].median())
            }
        }
    
    # Score geral de validação
    total_issues = sum([
        len(schema_errors),
        len(consistency_report['issues']),
        outliers.sum() if 'exchange_rate' in df.columns else 0
    ])
    
    validation_score = max(0, 1 - (total_issues / len(df))) if len(df) > 0 else 0
    summary['overall_validation_score'] = validation_score
    
    logger.info(
        "Resumo de validação gerado",
        validation_score=validation_score,
        total_issues=total_issues
    )
    
    return summary