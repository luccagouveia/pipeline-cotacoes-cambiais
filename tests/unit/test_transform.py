"""
Testes Unitários para o Módulo de Transformação
Pipeline de Cotações Cambiais - MBA Data Engineering

Este arquivo contém testes para validar:
1. Funcionamento do DataTransformer
2. Validação de dados com Pydantic
3. Verificações de qualidade dos dados
4. Conversão para formato Parquet
"""

import pytest
import pandas as pd
import json
import tempfile
from datetime import datetime, date
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Imports do módulo a ser testado
from src.transform.data_processor import DataTransformer, DataQualityChecker, ExchangeRateRecord
from src.utils.data_validator import CurrencyValidator, ExchangeRateValidator, TimestampValidator


class TestExchangeRateRecord:
    """
    Testes para o modelo Pydantic ExchangeRateRecord
    """
    
    def test_valid_record_creation(self):
        """
        Testa criação de registro válido
        """
        record_data = {
            'base_currency': 'USD',
            'target_currency': 'BRL',
            'exchange_rate': 5.1234,
            'collection_timestamp': datetime(2024, 1, 15, 10, 30, 0),
            'collection_date': date(2024, 1, 15),
            'last_update_timestamp': datetime(2024, 1, 15, 10, 0, 0),
            'pipeline_version': '1.0.0'
        }
        
        record = ExchangeRateRecord(**record_data)
        
        assert record.base_currency == 'USD'
        assert record.target_currency == 'BRL'
        assert record.exchange_rate == 5.1234
        assert record.pipeline_version == '1.0.0'
    
    def test_currency_code_validation(self):
        """
        Testa validação de códigos de moeda
        """
        record_data = {
            'base_currency': 'us',  # Inválido - deve ter 3 caracteres
            'target_currency': 'BRL',
            'exchange_rate': 5.1234,
            'collection_timestamp': datetime(2024, 1, 15, 10, 30, 0),
            'collection_date': date(2024, 1, 15),
            'last_update_timestamp': datetime(2024, 1, 15, 10, 0, 0),
            'pipeline_version': '1.0.0'
        }
        
        with pytest.raises(ValueError, match="Código de moeda deve ter 3 letras"):
            ExchangeRateRecord(**record_data)
    
    def test_exchange_rate_validation_negative(self):
        """
        Testa validação de taxa de câmbio negativa
        """
        record_data = {
            'base_currency': 'USD',
            'target_currency': 'BRL',
            'exchange_rate': -5.1234,  # Taxa negativa inválida
            'collection_timestamp': datetime(2024, 1, 15, 10, 30, 0),
            'collection_date': date(2024, 1, 15),
            'last_update_timestamp': datetime(2024, 1, 15, 10, 0, 0),
            'pipeline_version': '1.0.0'
        }
        
        with pytest.raises(ValueError, match="Taxa de câmbio deve ser positiva"):
            ExchangeRateRecord(**record_data)
    
    def test_exchange_rate_validation_too_high(self):
        """
        Testa validação de taxa de câmbio muito alta
        """
        record_data = {
            'base_currency': 'USD',
            'target_currency': 'BRL',
            'exchange_rate': 2000000.0,  # Taxa muito alta
            'collection_timestamp': datetime(2024, 1, 15, 10, 30, 0),
            'collection_date': date(2024, 1, 15),
            'last_update_timestamp': datetime(2024, 1, 15, 10, 0, 0),
            'pipeline_version': '1.0.0'
        }
        
        with pytest.raises(ValueError, match="Taxa de câmbio parece muito alta"):
            ExchangeRateRecord(**record_data)
    
    def test_timestamp_validation(self):
        """
        Testa validação de timestamps
        """
        record_data = {
            'base_currency': 'USD',
            'target_currency': 'BRL',
            'exchange_rate': 5.1234,
            'collection_timestamp': datetime(1999, 1, 15, 10, 30, 0),  # Ano muito antigo
            'collection_date': date(2024, 1, 15),
            'last_update_timestamp': datetime(2024, 1, 15, 10, 0, 0),
            'pipeline_version': '1.0.0'
        }
        
        with pytest.raises(ValueError, match="Timestamp fora do intervalo válido"):
            ExchangeRateRecord(**record_data)


class TestDataQualityChecker:
    """
    Testes para a classe DataQualityChecker
    """
    
    def setup_method(self):
        """
        Configuração executada antes de cada teste
        """
        self.quality_checker = DataQualityChecker()
    
    def test_check_completeness_perfect_data(self):
        """
        Testa verificação de completude com dados perfeitos
        """
        df = pd.DataFrame({
            'base_currency': ['USD', 'USD', 'USD'],
            'target_currency': ['BRL', 'EUR', 'GBP'],
            'exchange_rate': [5.1, 0.85, 0.79]
        })
        
        result = self.quality_checker.check_completeness(df)
        
        assert result['total_records'] == 3
        assert result['completeness_score'] == 1.0
        assert all(count == 0 for count in result['missing_values'].values())
    
    def test_check_completeness_with_missing_data(self):
        """
        Testa verificação de completude com dados faltantes
        """
        df = pd.DataFrame({
            'base_currency': ['USD', 'USD', None],
            'target_currency': ['BRL', 'EUR', 'GBP'],
            'exchange_rate': [5.1, None, 0.79]
        })
        
        result = self.quality_checker.check_completeness(df)
        
        assert result['total_records'] == 3
        assert result['completeness_score'] < 1.0
        assert result['missing_values']['base_currency'] == 1
        assert result['missing_values']['exchange_rate'] == 1
    
    def test_check_currency_consistency(self):
        """
        Testa verificação de consistência de moedas
        """
        df = pd.DataFrame({
            'base_currency': ['USD', 'USD', 'USD'],
            'target_currency': ['BRL', 'EUR', 'XYZ'],  # XYZ é inválida
            'exchange_rate': [5.1, 0.85, 0.79]
        })
        
        result = self.quality_checker.check_currency_consistency(df)
        
        assert result['unique_base_currencies'] == 1
        assert result['unique_target_currencies'] == 3
        assert result['total_currency_pairs'] == 3
    
    def test_check_rate_distribution(self):
        """
        Testa verificação de distribuição de taxas
        """
        df = pd.DataFrame({
            'exchange_rate': [5.1, 0.85, 0.79, -1.0, 0.0]  # Inclui valores problemáticos
        })
        
        result = self.quality_checker.check_rate_distribution(df)
        
        assert result['negative_rates'] == 1
        assert result['zero_rates'] == 1
        assert result['min_rate'] == -1.0
        assert result['max_rate'] == 5.1
    
    def test_generate_quality_report(self):
        """
        Testa geração de relatório completo de qualidade
        """
        df = pd.DataFrame({
            'base_currency': ['USD', 'USD', 'USD'],
            'target_currency': ['BRL', 'EUR', 'GBP'],
            'exchange_rate': [5.1, 0.85, 0.79]
        })
        
        report = self.quality_checker.generate_quality_report(df)
        
        assert 'timestamp' in report
        assert 'dataset_info' in report
        assert 'completeness' in report
        assert 'currency_consistency' in report
        assert 'rate_distribution' in report
        assert 'overall_quality_score' in report
        assert 0 <= report['overall_quality_score'] <= 1


class TestDataTransformer:
    """
    Testes para a classe DataTransformer
    """
    
    def setup_method(self):
        """
        Configuração executada antes de cada teste
        """
        self.temp_dir = tempfile.mkdtemp()
        self.raw_path = Path(self.temp_dir) / 'raw'
        self.silver_path = Path(self.temp_dir) / 'silver'
        self.raw_path.mkdir(parents=True)
        
        self.transformer = DataTransformer(
            raw_data_path=str(self.raw_path),
            silver_data_path=str(self.silver_path)
        )
    
    def teardown_method(self):
        """
        Limpeza após cada teste
        """
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_sample_raw_data(self, date_str: str = '2024-01-15'):
        """
        Cria arquivo de dados brutos para teste
        """
        sample_data = {
            'pipeline_metadata': {
                'collection_timestamp': '2024-01-15T10:30:00.123456',
                'collection_date': '2024-01-15',
                'base_currency': 'USD',
                'pipeline_version': '1.0.0'
            },
            'api_response': {
                'result': 'success',
                'time_last_update_unix': 1705305600,  # 2024-01-15 10:00:00
                'base_code': 'USD',
                'conversion_rates': {
                    'BRL': 5.1234,
                    'EUR': 0.8456,
                    'GBP': 0.7890
                }
            }
        }
        
        file_path = self.raw_path / f'{date_str}.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2)
        
        return sample_data
    
    def test_load_raw_data_success(self):
        """
        Testa carregamento bem-sucedido de dados brutos
        """
        date_str = '2024-01-15'
        expected_data = self.create_sample_raw_data(date_str)
        
        loaded_data = self.transformer.load_raw_data(date_str)
        
        assert loaded_data == expected_data
        assert 'pipeline_metadata' in loaded_data
        assert 'api_response' in loaded_data
    
    def test_load_raw_data_file_not_found(self):
        """
        Testa comportamento quando arquivo não existe
        """
        with pytest.raises(FileNotFoundError):
            self.transformer.load_raw_data('2024-01-99')  # Data inexistente
    
    def test_transform_to_tabular(self):
        """
        Testa transformação para formato tabular
        """
        raw_data = {
            'pipeline_metadata': {
                'collection_timestamp': '2024-01-15T10:30:00.123456',
                'collection_date': '2024-01-15',
                'base_currency': 'USD',
                'pipeline_version': '1.0.0'
            },
            'api_response': {
                'result': 'success',
                'time_last_update_unix': 1705305600,
                'base_code': 'USD',
                'conversion_rates': {
                    'BRL': 5.1234,
                    'EUR': 0.8456
                }
            }
        }
        
        records = self.transformer.transform_to_tabular(raw_data)
        
        assert len(records) == 2  # BRL e EUR
        assert records[0]['base_currency'] == 'USD'
        assert records[0]['target_currency'] == 'BRL'
        assert records[0]['exchange_rate'] == 5.1234
        assert records[1]['target_currency'] == 'EUR'
        assert records[1]['exchange_rate'] == 0.8456
    
    def test_validate_records_success(self):
        """
        Testa validação bem-sucedida de registros
        """
        records = [
            {
                'base_currency': 'USD',
                'target_currency': 'BRL',
                'exchange_rate': 5.1234,
                'collection_timestamp': datetime(2024, 1, 15, 10, 30, 0),
                'collection_date': date(2024, 1, 15),
                'last_update_timestamp': datetime(2024, 1, 15, 10, 0, 0),
                'pipeline_version': '1.0.0'
            },
            {
                'base_currency': 'USD',
                'target_currency': 'EUR',
                'exchange_rate': 0.8456,
                'collection_timestamp': datetime(2024, 1, 15, 10, 30, 0),
                'collection_date': date(2024, 1, 15),
                'last_update_timestamp': datetime(2024, 1, 15, 10, 0, 0),
                'pipeline_version': '1.0.0'
            }
        ]
        
        validated_records = self.transformer.validate_records(records)
        
        assert len(validated_records) == 2
        assert all(isinstance(record, ExchangeRateRecord) for record in validated_records)
        assert validated_records[0].base_currency == 'USD'
        assert validated_records[0].target_currency == 'BRL'
    
    def test_validate_records_with_invalid_data(self):
        """
        Testa validação com dados inválidos
        """
        records = [
            {
                'base_currency': 'USD',
                'target_currency': 'BRL',
                'exchange_rate': 5.1234,
                'collection_timestamp': datetime(2024, 1, 15, 10, 30, 0),
                'collection_date': date(2024, 1, 15),
                'last_update_timestamp': datetime(2024, 1, 15, 10, 0, 0),
                'pipeline_version': '1.0.0'
            },
            {
                'base_currency': 'USD',
                'target_currency': 'XX',  # Código inválido
                'exchange_rate': -0.8456,  # Taxa negativa
                'collection_timestamp': datetime(2024, 1, 15, 10, 30, 0),
                'collection_date': date(2024, 1, 15),
                'last_update_timestamp': datetime(2024, 1, 15, 10, 0, 0),
                'pipeline_version': '1.0.0'
            }
        ]
        
        validated_records = self.transformer.validate_records(records)
        
        # Apenas o primeiro registro deve ser válido
        assert len(validated_records) == 1
        assert validated_records[0].target_currency == 'BRL'
    
    def test_create_dataframe(self):
        """
        Testa criação de DataFrame
        """
        validated_records = [
            ExchangeRateRecord(
                base_currency='USD',
                target_currency='BRL',
                exchange_rate=5.1234,
                collection_timestamp=datetime(2024, 1, 15, 10, 30, 0),
                collection_date=date(2024, 1, 15),
                last_update_timestamp=datetime(2024, 1, 15, 10, 0, 0),
                pipeline_version='1.0.0'
            )
        ]
        
        df = self.transformer.create_dataframe(validated_records)
        
        assert len(df) == 1
        assert 'base_currency' in df.columns
        assert 'target_currency' in df.columns
        assert 'exchange_rate' in df.columns
        assert df.iloc[0]['base_currency'] == 'USD'
        assert df.iloc[0]['target_currency'] == 'BRL'
    
    @patch('pandas.DataFrame.to_parquet')
    def test_save_to_parquet(self, mock_to_parquet):
        """
        Testa salvamento em formato Parquet
        """
        df = pd.DataFrame({
            'base_currency': ['USD'],
            'target_currency': ['BRL'],
            'exchange_rate': [5.1234]
        })
        
        # Mock do arquivo salvo
        expected_path = self.silver_path / "exchange_rates_2024-01-15.parquet"
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 1024  # 1KB
            
            result_path = self.transformer.save_to_parquet(df, '2024-01-15')
        
        assert str(expected_path) in result_path
        mock_to_parquet.assert_called_once()
    
    def test_process_date_integration(self):
        """
        Testa processamento completo de uma data (teste de integração)
        """
        date_str = '2024-01-15'
        self.create_sample_raw_data(date_str)
        
        with patch('pandas.DataFrame.to_parquet') as mock_to_parquet:
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 2048
                
                report = self.transformer.process_date(date_str)
        
        assert report['status'] == 'success'
        assert report['target_date'] == date_str
        assert 'execution_time_seconds' in report
        assert report['processing']['validated_records'] > 0
        assert report['quality']['overall_quality_score'] > 0


class TestCurrencyValidator:
    """
    Testes para CurrencyValidator
    """
    
    def test_is_valid_currency_code_valid(self):
        """
        Testa validação de códigos de moeda válidos
        """
        valid_codes = ['USD', 'EUR', 'BRL', 'GBP', 'JPY']
        
        for code in valid_codes:
            assert CurrencyValidator.is_valid_currency_code(code)
            assert CurrencyValidator.is_valid_currency_code(code.lower())  # Case insensitive
    
    def test_is_valid_currency_code_invalid(self):
        """
        Testa validação de códigos de moeda inválidos
        """
        invalid_codes = ['US', 'USDX', '123', 'XX1', '', None, 'XYZ']
        
        for code in invalid_codes:
            assert not CurrencyValidator.is_valid_currency_code(code)
    
    def test_validate_currency_pair_success(self):
        """
        Testa validação bem-sucedida de par de moedas
        """
        is_valid, errors = CurrencyValidator.validate_currency_pair('USD', 'BRL')
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_currency_pair_same_currencies(self):
        """
        Testa validação de par com moedas iguais
        """
        is_valid, errors = CurrencyValidator.validate_currency_pair('USD', 'USD')
        
        assert not is_valid
        assert any('não podem ser iguais' in error for error in errors)


class TestExchangeRateValidator:
    """
    Testes para ExchangeRateValidator
    """
    
    def test_is_valid_rate_valid_rates(self):
        """
        Testa validação de taxas válidas
        """
        valid_rates = [0.1, 1.0, 5.1234, 100.5, 999.99]
        
        for rate in valid_rates:
            assert ExchangeRateValidator.is_valid_rate(rate)
    
    def test_is_valid_rate_invalid_rates(self):
        """
        Testa validação de taxas inválidas
        """
        invalid_rates = [-1.0, 0.0, float('inf'), float('nan'), 2000000.0]
        
        for rate in invalid_rates:
            assert not ExchangeRateValidator.is_valid_rate(rate)
    
    def test_detect_outliers_iqr(self):
        """
        Testa detecção de outliers usando IQR
        """
        rates = pd.Series([1.0, 1.1, 1.2, 1.3, 1.4, 10.0])  # 10.0 é outlier
        
        outliers = ExchangeRateValidator.detect_outliers(rates, method='iqr')
        
        assert outliers.iloc[-1]  # Último valor deve ser outlier
        assert not outliers.iloc[0]  # Primeiro valor não deve ser outlier
    
    def test_detect_outliers_zscore(self):
        """
        Testa detecção de outliers usando Z-score
        """
        rates = pd.Series([1.0, 1.0, 1.0, 1.0, 1.0, 5.0])  # 5.0 é outlier
        
        outliers = ExchangeRateValidator.detect_outliers(rates, method='zscore')
        
        assert outliers.iloc[-1]  # Último valor deve ser outlier


class TestTimestampValidator:
    """
    Testes para TimestampValidator
    """
    
    def test_is_valid_timestamp_valid(self):
        """
        Testa validação de timestamps válidos
        """
        valid_timestamps = [
            datetime(2024, 1, 15, 10, 30, 0),
            datetime(2023, 12, 31, 23, 59, 59),
            datetime(2025, 6, 15, 12, 0, 0)
        ]
        
        for ts in valid_timestamps:
            assert TimestampValidator.is_valid_timestamp(ts)
    
    def test_is_valid_timestamp_invalid(self):
        """
        Testa validação de timestamps inválidos
        """
        invalid_timestamps = [
            datetime(1999, 1, 1, 0, 0, 0),  # Muito antigo
            datetime(2031, 1, 1, 0, 0, 0),  # Muito futuro
            "2024-01-15",  # Não é datetime
            None
        ]
        
        for ts in invalid_timestamps:
            assert not TimestampValidator.is_valid_timestamp(ts)
    
    def test_is_reasonable_collection_time(self):
        """
        Testa validação de tempo de coleta razoável
        """
        update_ts = datetime(2024, 1, 15, 10, 0, 0)
        collection_ts = datetime(2024, 1, 15, 10, 30, 0)  # 30 min depois
        
        assert TimestampValidator.is_reasonable_collection_time(collection_ts, update_ts)
        
        # Teste com diferença muito grande
        old_update_ts = datetime(2024, 1, 1, 10, 0, 0)  # 2 semanas antes
        assert not TimestampValidator.is_reasonable_collection_time(collection_ts, old_update_ts)


# Fixtures para testes
@pytest.fixture
def sample_dataframe():
    """
    Fixture com DataFrame de exemplo
    """
    return pd.DataFrame({
        'base_currency': ['USD', 'USD', 'USD'],
        'target_currency': ['BRL', 'EUR', 'GBP'],
        'exchange_rate': [5.1234, 0.8456, 0.7890],
        'collection_timestamp': [datetime(2024, 1, 15, 10, 30, 0)] * 3,
        'collection_date': [date(2024, 1, 15)] * 3,
        'last_update_timestamp': [datetime(2024, 1, 15, 10, 0, 0)] * 3,
        'pipeline_version': ['1.0.0'] * 3
    })


@pytest.fixture
def sample_raw_data():
    """
    Fixture com dados brutos de exemplo
    """
    return {
        'pipeline_metadata': {
            'collection_timestamp': '2024-01-15T10:30:00.123456',
            'collection_date': '2024-01-15',
            'base_currency': 'USD',
            'pipeline_version': '1.0.0'
        },
        'api_response': {
            'result': 'success',
            'time_last_update_unix': 1705305600,
            'base_code': 'USD',
            'conversion_rates': {
                'BRL': 5.1234,
                'EUR': 0.8456,
                'GBP': 0.7890,
                'JPY': 149.52,
                'CAD': 1.3245
            }
        }
    }