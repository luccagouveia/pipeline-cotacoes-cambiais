"""
Testes Unitários para o Módulo de Ingestão
Pipeline de Cotações Cambiais - MBA Data Engineering

Este arquivo contém testes para validar:
1. Funcionamento da ExchangeRateAPIClient
2. Validação de responses da API
3. Sistema de retry e error handling
4. Funcionalidade do DataIngester
"""

import pytest
import json
import requests
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from datetime import date, datetime

# Imports do módulo a ser testado
from src.ingest.exchange_api import ExchangeRateAPIClient, DataIngester


class TestExchangeRateAPIClient:
    """
    Testes para a classe ExchangeRateAPIClient
    """
    
    def setup_method(self):
        """
        Configuração executada antes de cada teste
        """
        self.api_key = "test_api_key_123"
        self.base_url = "https://test-api.com/v6"
        self.client = ExchangeRateAPIClient(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=10,
            retry_attempts=2,
            retry_delay=1
        )
    
    def test_init_with_parameters(self):
        """
        Testa inicialização do cliente com parâmetros explícitos
        """
        assert self.client.api_key == self.api_key
        assert self.client.base_url == self.base_url
        assert self.client.timeout == 10
        assert self.client.retry_attempts == 2
        assert self.client.retry_delay == 1
    
    def test_init_without_api_key_raises_error(self):
        """
        Testa se inicialização sem API key levanta erro
        """
        with pytest.raises(ValueError, match="API key não encontrada"):
            ExchangeRateAPIClient(api_key=None, base_url=self.base_url)
    
    @patch.dict('os.environ', {
        'EXCHANGE_API_KEY': 'env_api_key',
        'EXCHANGE_API_BASE_URL': 'https://env-api.com/v6'
    })
    def test_init_from_environment(self):
        """
        Testa inicialização usando variáveis de ambiente
        """
        client = ExchangeRateAPIClient()
        assert client.api_key == 'env_api_key'
        assert client.base_url == 'https://env-api.com/v6'
    
    def test_validate_api_response_success(self):
        """
        Testa validação de resposta válida da API
        """
        valid_response = {
            'result': 'success',
            'base_code': 'USD',
            'conversion_rates': {
                'BRL': 5.1234,
                'EUR': 0.8456
            }
        }
        
        # Não deve levantar exceção
        self.client._validate_api_response(valid_response)
    
    def test_validate_api_response_missing_field(self):
        """
        Testa validação com campo obrigatório faltando
        """
        invalid_response = {
            'result': 'success',
            'base_code': 'USD'
            # conversion_rates está faltando
        }
        
        with pytest.raises(ValueError, match="Campo obrigatório 'conversion_rates' não encontrado"):
            self.client._validate_api_response(invalid_response)
    
    def test_validate_api_response_error_result(self):
        """
        Testa validação quando API retorna erro
        """
        error_response = {
            'result': 'error',
            'error-type': 'invalid-key',
            'base_code': 'USD',
            'conversion_rates': {}
        }
        
        with pytest.raises(ValueError, match="API retornou erro"):
            self.client._validate_api_response(error_response)
    
    def test_validate_api_response_empty_rates(self):
        """
        Testa validação com cotações vazias
        """
        empty_response = {
            'result': 'success',
            'base_code': 'USD',
            'conversion_rates': {}
        }
        
        with pytest.raises(ValueError, match="Nenhuma cotação encontrada"):
            self.client._validate_api_response(empty_response)
    
    @patch('requests.get')
    def test_get_latest_rates_success(self, mock_get):
        """
        Testa coleta bem-sucedida de cotações
        """
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': 'success',
            'base_code': 'USD',
            'conversion_rates': {
                'BRL': 5.1234,
                'EUR': 0.8456
            },
            'time_last_update_utc': 'Mon, 01 Jan 2024 00:00:01 +0000'
        }
        mock_get.return_value = mock_response
        
        # Executar teste
        result = self.client.get_latest_rates('USD')
        
        # Verificações
        assert result['result'] == 'success'
        assert result['base_code'] == 'USD'
        assert 'BRL' in result['conversion_rates']
        assert 'EUR' in result['conversion_rates']
        
        # Verificar se a URL foi chamada corretamente
        expected_url = f"{self.base_url}/{self.api_key}/latest/USD"
        mock_get.assert_called_once_with(
            expected_url,
            timeout=10,
            headers={
                'User-Agent': 'Pipeline-Cotacoes-Cambiais/1.0',
                'Accept': 'application/json'
            }
        )
    
    @patch('requests.get')
    @patch('time.sleep')  # Mock do sleep para acelerar teste
    def test_get_latest_rates_retry_on_timeout(self, mock_sleep, mock_get):
        """
        Testa sistema de retry em caso de timeout
        """
        # Primeira tentativa: timeout
        # Segunda tentativa: sucesso
        mock_get.side_effect = [
            requests.exceptions.Timeout("Timeout occurred"),
            Mock(
                status_code=200,
                json=lambda: {
                    'result': 'success',
                    'base_code': 'USD',
                    'conversion_rates': {'BRL': 5.1234}
                }
            )
        ]
        
        # Executar teste
        result = self.client.get_latest_rates('USD')
        
        # Verificações
        assert result['result'] == 'success'
        assert mock_get.call_count == 2  # Duas tentativas
        mock_sleep.assert_called_once_with(1)  # Delay entre tentativas
    
    @patch('requests.get')
    @patch('time.sleep')
    def test_get_latest_rates_all_retries_fail(self, mock_sleep, mock_get):
        """
        Testa comportamento quando todas as tentativas falham
        """
        # Todas as tentativas falham com timeout
        mock_get.side_effect = requests.exceptions.Timeout("Timeout occurred")
        
        # Executar teste e verificar se levanta exceção
        with pytest.raises(requests.RequestException, match="Falha ao coletar cotações após 2 tentativas"):
            self.client.get_latest_rates('USD')
        
        # Verificar se tentou o número correto de vezes
        assert mock_get.call_count == 2
        assert mock_sleep.call_count == 1  # Sleep entre tentativas


class TestDataIngester:
    """
    Testes para a classe DataIngester
    """
    
    def setup_method(self):
        """
        Configuração executada antes de cada teste
        """
        self.test_path = Path("test_data/raw")
        self.ingester = DataIngester(raw_data_path=str(self.test_path))
    
    @patch('pathlib.Path.mkdir')
    def test_init_creates_directory(self, mock_mkdir):
        """
        Testa se inicialização cria diretório necessário
        """
        DataIngester(raw_data_path="test/path")
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    @patch('src.ingest.exchange_api.ExchangeRateAPIClient')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('pathlib.Path.stat')
    def test_collect_and_save_daily_rates_success(
        self, 
        mock_stat, 
        mock_json_dump,
        mock_file_open,
        mock_api_client_class
    ):
        """
        Testa coleta e salvamento bem-sucedido de cotações diárias
        """
        # Mock do cliente da API
        mock_api_client = Mock()
        mock_api_response = {
            'result': 'success',
            'base_code': 'USD',
            'conversion_rates': {
                'BRL': 5.1234,
                'EUR': 0.8456
            },
            'time_last_update_utc': 'Mon, 01 Jan 2024 00:00:01 +0000'
        }
        mock_api_client.get_latest_rates.return_value = mock_api_response
        mock_api_client_class.return_value = mock_api_client
        
        # Mock do stat do arquivo (para tamanho)
        mock_stat_result = Mock()
        mock_stat_result.st_size = 1024  # 1KB
        mock_stat.return_value = mock_stat_result
        
        # Executar teste
        target_date = date(2024, 1, 1)
        result_path = self.ingester.collect_and_save_daily_rates(
            base_currency='USD',
            target_date=target_date
        )
        
        # Verificações
        expected_filename = "2024-01-01.json"
        assert expected_filename in result_path
        
        # Verificar se API foi chamada corretamente
        mock_api_client.get_latest_rates.assert_called_once_with('USD')
        
        # Verificar se arquivo foi aberto para escrita
        mock_file_open.assert_called_once()
        
        # Verificar se JSON foi salvo
        mock_json_dump.assert_called_once()
        call_args = mock_json_dump.call_args[0]
        saved_data = call_args[0]
        
        # Verificar estrutura dos dados salvos
        assert 'pipeline_metadata' in saved_data
        assert 'api_response' in saved_data
        assert saved_data['pipeline_metadata']['collection_date'] == '2024-01-01'
        assert saved_data['pipeline_metadata']['base_currency'] == 'USD'
        assert saved_data['api_response'] == mock_api_response
    
    @patch('src.ingest.exchange_api.ExchangeRateAPIClient')
    def test_collect_and_save_daily_rates_api_failure(self, mock_api_client_class):
        """
        Testa comportamento quando API falha
        """
        # Mock do cliente da API que falha
        mock_api_client = Mock()
        mock_api_client.get_latest_rates.side_effect = requests.RequestException("API Error")
        mock_api_client_class.return_value = mock_api_client
        
        # Executar teste e verificar se levanta exceção
        with pytest.raises(requests.RequestException):
            self.ingester.collect_and_save_daily_rates()


class TestIntegration:
    """
    Testes de integração básicos
    """
    
    @patch.dict('os.environ', {
        'EXCHANGE_API_KEY': 'test_key_123',
        'EXCHANGE_API_BASE_URL': 'https://test-api.com/v6'
    })
    def test_full_workflow_with_mocks(self):
        """
        Testa o workflow completo com mocks
        """
        with patch('requests.get') as mock_get:
            # Mock da resposta da API
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'result': 'success',
                'base_code': 'USD',
                'conversion_rates': {
                    'BRL': 5.1234,
                    'EUR': 0.8456,
                    'GBP': 0.7890,
                    'JPY': 149.52
                },
                'time_last_update_utc': 'Mon, 01 Jan 2024 00:00:01 +0000'
            }
            mock_get.return_value = mock_response
            
            # Executar workflow
            ingester = DataIngester(raw_data_path="test_output")
            
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump') as mock_json_dump:
                    with patch('pathlib.Path.stat', return_value=Mock(st_size=2048)):
                        result_path = ingester.collect_and_save_daily_rates('USD')
            
            # Verificações
            assert result_path is not None
            assert "test_output" in result_path
            mock_get.assert_called_once()
            mock_file.assert_called_once()
            mock_json_dump.assert_called_once()


# Fixtures para testes
@pytest.fixture
def sample_api_response():
    """
    Fixture com uma resposta de exemplo da API
    """
    return {
        'result': 'success',
        'documentation': 'https://www.exchangerate-api.com/docs',
        'terms_of_use': 'https://www.exchangerate-api.com/terms',
        'time_last_update_unix': 1704067201,
        'time_last_update_utc': 'Mon, 01 Jan 2024 00:00:01 +0000',
        'time_next_update_unix': 1704153601,
        'time_next_update_utc': 'Tue, 02 Jan 2024 00:00:01 +0000',
        'base_code': 'USD',
        'conversion_rates': {
            'AED': 3.6725,
            'AFN': 70.0,
            'ALL': 92.5,
            'AMD': 404.0,
            'ANG': 1.79,
            'AOA': 830.0,
            'ARS': 808.5,
            'AUD': 1.4785,
            'AWG': 1.79,
            'AZN': 1.7,
            'BAM': 1.7955,
            'BBD': 2.0,
            'BDT': 110.0,
            'BGN': 1.7955,
            'BHD': 0.376,
            'BIF': 2860.0,
            'BMD': 1.0,
            'BND': 1.3315,
            'BOB': 6.91,
            'BRL': 4.9234,
            'BSD': 1.0,
            'BTN': 83.12,
            'BWP': 13.52,
            'BYN': 3.27,
            'BZD': 2.0,
            'CAD': 1.3245,
            'CDF': 2700.0,
            'CHF': 0.8456,
            'CLP': 890.0,
            'CNY': 7.1068,
            'COP': 3900.0,
            'CRC': 520.0,
            'CUP': 24.0,
            'CVE': 101.25,
            'CZK': 22.5,
            'DJF': 177.7,
            'DKK': 6.8405,
            'DOP': 56.5,
            'DZD': 134.0,
            'EGP': 30.85,
            'ERN': 15.0,
            'ETB': 56.5,
            'EUR': 0.9184,
            'FJD': 2.24,
            'FKP': 0.7901,
            'FOK': 6.8405,
            'GBP': 0.7901,
            'GEL': 2.65,
            'GGP': 0.7901,
            'GHS': 12.0,
            'GIP': 0.7901,
            'GMD': 67.0,
            'GNF': 8600.0,
            'GTQ': 7.8,
            'GYD': 209.0,
            'HKD': 7.8,
            'HNL': 24.6,
            'HRK': 6.9205,
            'HTG': 132.0,
            'HUF': 348.5,
            'IDR': 15435.0,
            'ILS': 3.7,
            'IMP': 0.7901,
            'INR': 83.12,
            'IQD': 1310.0,
            'IRR': 42000.0,
            'ISK': 137.5,
            'JEP': 0.7901,
            'JMD': 156.0,
            'JOD': 0.709,
            'JPY': 149.52,
            'KES': 160.0,
            'KGS': 89.0,
            'KHR': 4100.0,
            'KMF': 452.25,
            'KPW': 900.0,
            'KRW': 1305.0,
            'KWD': 0.307,
            'KYD': 0.833,
            'KZT': 450.0,
            'LAK': 20500.0,
            'LBP': 15000.0,
            'LKR': 325.0,
            'LRD': 188.0,
            'LSL': 18.5,
            'LYD': 4.8,
            'MAD': 9.9,
            'MDL': 17.85,
            'MGA': 4500.0,
            'MKD': 56.5,
            'MMK': 2100.0,
            'MNT': 3450.0,
            'MOP': 8.05,
            'MRU': 39.5,
            'MUR': 44.5,
            'MVR': 15.4,
            'MWK': 1690.0,
            'MXN': 17.0,
            'MYR': 4.6,
            'MZN': 63.5,
            'NAD': 18.5,
            'NGN': 920.0,
            'NIO': 36.5,
            'NOK': 10.45,
            'NPR': 133.0,
            'NZD': 1.59,
            'OMR': 0.384,
            'PAB': 1.0,
            'PEN': 3.7,
            'PGK': 3.75,
            'PHP': 55.5,
            'PKR': 280.0,
            'PLN': 4.0,
            'PYG': 7300.0,
            'QAR': 3.64,
            'RON': 4.56,
            'RSD': 107.5,
            'RUB': 90.0,
            'RWF': 1250.0,
            'SAR': 3.75,
            'SBD': 8.45,
            'SCR': 13.4,
            'SDG': 601.0,
            'SEK': 10.25,
            'SGD': 1.3315,
            'SHP': 0.7901,
            'SLE': 22.5,
            'SLL': 22500.0,
            'SOS': 571.0,
            'SRD': 37.5,
            'STN': 22.5,
            'SYP': 13000.0,
            'SZL': 18.5,
            'THB': 34.5,
            'TJS': 10.9,
            'TMT': 3.5,
            'TND': 3.1,
            'TOP': 2.33,
            'TRY': 29.5,
            'TTD': 6.75,
            'TVD': 1.4785,
            'TWD': 31.0,
            'TZS': 2500.0,
            'UAH': 38.0,
            'UGX': 3700.0,
            'UYU': 39.0,
            'UZS': 12300.0,
            'VED': 3550000.0,
            'VES': 35.5,
            'VND': 24500.0,
            'VUV': 119.0,
            'WST': 2.7,
            'XAF': 602.5,
            'XCD': 2.7,
            'XDR': 0.75,
            'XOF': 602.5,
            'XPF': 109.5,
            'YER': 250.0,
            'ZAR': 18.5,
            'ZMW': 26.5,
            'ZWL': 5220.0
        }
    }