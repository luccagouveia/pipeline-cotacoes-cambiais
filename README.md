# 🚀 Pipeline de Cotações Cambiais com Python + LLM

*Python Programming for Data Engineers*  
Professor: Eduardo Miranda

---

## 📋 Visão Geral do Projeto

Este projeto implementa um pipeline de dados completo para coleta, processamento e análise de cotações cambiais, integrando APIs externas com Large Language Models (LLM) para geração de insights em linguagem natural voltados a usuários de negócio.

### 🎯 Objetivos Principais

1. **Coletar** taxas de câmbio da API https://www.exchangerate-api.com/
2. **Processar e validar** os dados em camadas estruturadas (raw, silver, gold)
3. **Integrar com LLM** (ChatGPT) para gerar resumos e insights executivos
4. **Implementar** testes unitários, logging estruturado e observabilidade

---

## 🏗️ Arquitetura do Projeto

### Estrutura de Diretórios

```
pipeline-cotacoes-cambiais/
│
├── 📁 data/                    # Arquitetura Medallion
│   ├── 📁 raw/                 # Dados brutos da API (JSON)
│   ├── 📁 silver/              # Dados limpos e normalizados
│   └── 📁 gold/                # Dados finais em Parquet
│
├── 📁 src/                     # Código fonte principal
│   ├── 📁 ingest/              # Módulos de ingestão de dados
│   ├── 📁 transform/           # Módulos de transformação
│   ├── 📁 load/                # Módulos de carga de dados
│   ├── 📁 llm/                 # Integração com LLM
│   └── 📁 utils/               # Utilitários e funções auxiliares
│
├── 📁 config/                  # Configurações do pipeline
├── 📁 tests/                   # Testes unitários e integração
│   ├── 📁 unit/                # Testes unitários
│   └── 📁 integration/         # Testes de integração
│
├── 📁 logs/                    # Arquivos de log estruturado
├── 📁 outputs/                 # Relatórios e insights da LLM
│   └── 📁 reports/             # Relatórios executivos
│
├── 📁 docs/                    # Documentação adicional
├── 📁 scripts/                 # Scripts auxiliares e automação
│
├── 📄 requirements.txt         # Dependências Python
├── 📄 .env.template           # Template de variáveis de ambiente
├── 📄 .env                    # Variáveis de ambiente (não versionado)
├── 📄 .gitignore              # Arquivos ignorados pelo Git
└── 📄 README.md               # Esta documentação
```

---

## ⚙️ Configuração do Ambiente

### Pré-requisitos

- Python 3.8+
- Conta na [Exchange Rate API](https://www.exchangerate-api.com/)
- Conta na [OpenAI](https://platform.openai.com/) para acesso ao ChatGPT
- Git para controle de versão

### 🔧 Instalação

#### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd pipeline-cotacoes-cambiais
```

#### 2. Crie e ative o ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

#### 3. Instale as dependências
```bash
# Atualizar pip
python -m pip install --upgrade pip

# Instalar dependências principais
pip install requests
pip install pandas
pip install python-dotenv
pip install pyyaml
pip install openai
pip install structlog
pip install pydantic
pip install pytest
pip install pytest-mock
pip install python-dateutil

# Instalar suporte a Parquet
pip install pyarrow
# OU se houver erro de compilação:
# pip install fastparquet
```

#### 4. Configure as variáveis de ambiente
```bash
# Copie o template
copy .env.template .env

# Edite o arquivo .env com suas chaves de API
```

### 🔐 Configuração das APIs

#### Exchange Rate API
1. Acesse https://www.exchangerate-api.com/
2. Crie uma conta gratuita
3. Copie sua API key
4. Adicione no arquivo `.env`:
```bash
EXCHANGE_API_KEY=sua_chave_aqui
```

#### OpenAI API
1. Acesse https://platform.openai.com/
2. Crie uma conta e configure billing
3. Gere uma API key
4. Adicione no arquivo `.env`:
```bash
OPENAI_API_KEY=sua_chave_openai_aqui
```

---

## 📚 Dependências do Projeto

### Bibliotecas Principais

| Biblioteca | Versão | Finalidade |
|------------|--------|------------|
| `requests` | >=2.31.0 | Requisições HTTP para APIs |
| `pandas` | >=2.0.0 | Manipulação e análise de dados |
| `pyarrow` | >=13.0.0 | Processamento de arquivos Parquet |
| `python-dotenv` | >=1.0.0 | Carregamento de variáveis de ambiente |
| `pyyaml` | >=6.0.0 | Processamento de arquivos YAML |
| `openai` | >=1.0.0 | Integração com ChatGPT |
| `structlog` | >=23.0.0 | Logging estruturado |
| `pydantic` | >=2.0.0 | Validação de dados |
| `pytest` | >=7.0.0 | Framework de testes |

### Arquivos de Configuração

#### `.env` (Template)
```bash
# APIs
EXCHANGE_API_KEY=your_exchange_api_key_here
EXCHANGE_API_BASE_URL=https://v6.exchangerate-api.com/v6
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Pipeline
BASE_CURRENCY=USD
TARGET_CURRENCIES=BRL,EUR,GBP,JPY,CAD,AUD,CHF,CNY
LOG_LEVEL=INFO
LOG_FORMAT=json
DATA_RETENTION_DAYS=90
BATCH_SIZE=1000
```

#### `config/pipeline_config.yaml`
```yaml
# Configurações da API
api:
  exchange_rate:
    base_url: "https://v6.exchangerate-api.com/v6"
    timeout: 30
    retry_attempts: 3
    retry_delay: 5

# Configurações de moedas
currencies:
  base: "USD"
  targets:
    - "BRL"  # Real Brasileiro
    - "EUR"  # Euro
    - "GBP"  # Libra Esterlina
    - "JPY"  # Iene Japonês
    - "CAD"  # Dólar Canadense
    - "AUD"  # Dólar Australiano
    - "CHF"  # Franco Suíço
    - "CNY"  # Yuan Chinês

# Configurações de dados
data:
  raw:
    path: "data/raw"
    format: "json"
  silver:
    path: "data/silver" 
    format: "parquet"
    compression: "snappy"
  gold:
    path: "data/gold"
    format: "parquet"
    compression: "snappy"

# Configurações da LLM
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"
  temperature: 0.3
  max_tokens: 500
```

---

## 🔄 Fluxo do Pipeline

### 1. **Ingestão (Ingest)**
- Coleta dados da Exchange Rate API
- Salva resposta JSON bruta em `/data/raw/`
- Nomenclatura: `YYYY-MM-DD.json`
- Configuração via `.env`, sem hardcode

### 2. **Transformação (Transform)**
- Normaliza dados (moeda, taxa, base_currency, timestamp)
- Aplica validações de qualidade (taxas não negativas/nulas)
- Armazena em `/data/silver/` em formato Parquet

### 3. **Carga (Load)**
- Processa dados finais para `/data/gold/` em Parquet
- Estrutura otimizada para análise
- (Opcional) Carregamento em banco relacional

### 4. **Enriquecimento com LLM**
- Integração com ChatGPT para análise dos dados
- Geração de insights executivos em português
- Explicações em linguagem natural para usuários de negócio
- Armazenamento de relatórios em `/outputs/reports/`

### 5. **Observabilidade**
- Logging estruturado com `structlog`
- Testes unitários com `pytest`
- Validação de dados com `pydantic`

---

## 🚀 Como Executar

### Execução Manual
```bash
# Ativar ambiente virtual
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Executar pipeline completo
python main.py

# Executar módulos específicos
python -m src.ingest.exchange_api
python -m src.transform.data_processor
python -m src.load.parquet_writer
python -m src.llm.insight_generator
```

### Testes
```bash
# Executar todos os testes
pytest

# Executar com coverage
pytest --cov=src

# Executar testes específicos
pytest tests/unit/test_ingest.py
```

---

## 📊 Estrutura dos Dados

### Raw Layer (`/data/raw/`)
```json
{
  "result": "success",
  "documentation": "https://www.exchangerate-api.com/docs",
  "terms_of_use": "https://www.exchangerate-api.com/terms",
  "time_last_update_unix": 1694592001,
  "time_last_update_utc": "Wed, 13 Sep 2023 00:00:01 +0000",
  "time_next_update_unix": 1694678401,
  "time_next_update_utc": "Thu, 14 Sep 2023 00:00:01 +0000",
  "base_code": "USD",
  "conversion_rates": {
    "BRL": 4.9234,
    "EUR": 0.8421,
    "GBP": 0.7901,
    "JPY": 149.52
  }
}
```

### Silver Layer (`/data/silver/`)
```
| base_currency | target_currency | exchange_rate | timestamp           | date       |
|---------------|-----------------|---------------|---------------------|------------|
| USD           | BRL             | 4.9234        | 2023-09-13 00:00:01 | 2023-09-13 |
| USD           | EUR             | 0.8421        | 2023-09-13 00:00:01 | 2023-09-13 |
```

### Gold Layer (`/data/gold/`)
- Dados otimizados em Parquet
- Particionado por data para performance
- Métricas calculadas (variação %, volatilidade)
- Pronto para análise e dashboards

---

## 🤖 Integração com LLM

### Prompts Configurados

#### Resumo Diário Executivo
```
Você é um analista financeiro experiente. Analise os dados de cotações 
cambiais fornecidos e crie um resumo executivo conciso em português brasileiro.

Inclua:
1. Principais movimentações das moedas
2. Destaques de valorização/desvalorização  
3. Contexto para decisões de negócio
4. Alertas importantes

Mantenha linguagem clara e acessível para executivos.
```

### Exemplos de Insights Gerados
- "O Euro está 5% mais valorizado em relação ao mês passado"
- "A volatilidade do JPY em relação ao USD está acima da média"
- "Recomenda-se cautela com operações em GBP devido à alta volatilidade"

---

## 🧪 Testes e Qualidade

### Cobertura de Testes
- ✅ Testes unitários para cada módulo
- ✅ Validação de taxas numéricas
- ✅ Testes de integração com APIs
- ✅ Mocking para chamadas externas

### Logging Estruturado
```python
import structlog

logger = structlog.get_logger()
logger.info("Pipeline iniciado", stage="ingest", timestamp="2023-09-13T10:00:00Z")
```

### Validação de Dados
```python
from pydantic import BaseModel, validator

class ExchangeRate(BaseModel):
    base_code: str
    target_code: str
    conversion_rate: float
    
    @validator('conversion_rate')
    def rate_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Taxa deve ser positiva')
        return v
```

---

## 📈 Roadmap de Desenvolvimento

### ✅ Fase 1 - Estruturação (Concluída)
- [x] Estrutura de diretórios
- [x] Ambiente virtual configurado
- [x] Dependências instaladas
- [x] Arquivos de configuração

### 🔄 Fase 2 - Ingestão (Próxima)
- [ ] Módulo de coleta da API
- [ ] Sistema de retry e error handling
- [ ] Validação de resposta da API

### 🔄 Fase 3 - Transformação
- [ ] Normalização de dados
- [ ] Validações de qualidade
- [ ] Processamento para Silver layer

### 🔄 Fase 4 - Carga
- [ ] Geração de arquivos Parquet
- [ ] Otimizações de performance
- [ ] Gold layer estruturado

### 🔄 Fase 5 - LLM Integration
- [ ] Integração com OpenAI
- [ ] Geração de insights
- [ ] Relatórios executivos

### 🔄 Fase 6 - Observabilidade
- [ ] Testes unitários completos
- [ ] Logging estruturado
- [ ] Monitoramento do pipeline

---

## 🔧 Troubleshooting

### Problemas Comuns

#### Erro de Instalação do PyArrow
```bash
# Solução alternativa
pip install fastparquet
```

#### Erro de API Key
```bash
# Verifique se o arquivo .env está configurado
cat .env | grep EXCHANGE_API_KEY
```

#### Erro de Parsing no PowerShell
```bash
# Execute comandos individualmente
pip install requests
pip install pandas
# ... um por vez
```

---

## 👥 Contribuição

### Padrões de Código
- Formatação: `black`
- Linting: `flake8`
- Documentação: docstrings em português
- Commits: conventional commits

### Estrutura de Branches
- `main`: código de produção
- `develop`: desenvolvimento ativo
- `feature/*`: novas funcionalidades

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs em `/logs/`
2. Execute os testes: `pytest`
3. Consulte a documentação da API
4. Abra uma issue no repositório

---

## 📄 Licença

Este projeto é desenvolvido para fins acadêmicos como parte do MBA em Data Engineering.

---

**Status do Projeto**: 🟡 Em Desenvolvimento  
**Última Atualização**: Setembro 2025
**Próxima Fase**: Desenvolvimento do Módulo de Ingestão