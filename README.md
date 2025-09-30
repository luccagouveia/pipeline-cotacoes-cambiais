# 🚀 Pipeline de Cotações Cambiais com Python + LLM

**Projeto Final - MBA em Data Engineering**  
*Python Programming for Data Engineers*  
   
Elaborado por:
- Lucas Alves Gouveia RA: 2500399
- Kauan Gomes RA: 2502147
- Carina de Oliveira RA: 2100205

Professor: Eduardo Miranda

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

---

## 📋 Visão Geral do Projeto

Pipeline de dados end-to-end para coleta, processamento e análise de cotações cambiais de 163 moedas, com integração de Large Language Models (LLM) para geração automática de insights executivos.

### 🎯 Objetivos Principais

1. **Coletar** taxas de câmbio em tempo real via API
2. **Processar** dados em arquitetura Medallion (Raw → Silver → Gold)
3. **Validar** com Pydantic e métricas de qualidade
4. **Gerar insights** automatizados com OpenAI GPT
5. **Visualizar** através de dashboard interativo

---

## 🏗️ Arquitetura do Projeto

### Estrutura de Diretórios

```
pipeline-cotacoes-cambiais/
│
├── 📁 data/                    # Arquitetura Medallion
│   ├── 📁 raw/                 # Dados brutos da API (JSON)
│   ├── 📁 silver/              # Dados limpos e validados (Parquet)
│   └── 📁 gold/                # Agregações e métricas (Parquet/JSON)
│
├── 📁 src/                     # Código fonte modularizado
│   ├── 📁 ingest/              # Ingestão de dados (Exchange Rate API)
│   ├── 📁 transform/           # Transformação e validação (Pydantic)
│   ├── 📁 load/                # Carga Gold Layer
│   ├── 📁 llm/                 # Geração de insights (OpenAI)
│   └── 📁 utils/               # Utilitários e logging estruturado
│
├── 📁 config/                  # Configurações YAML
├── 📁 tests/                   # Testes unitários (pytest)
├── 📁 logs/                    # Logs estruturados (structlog)
├── 📁 outputs/reports/         # Relatórios LLM (JSON/MD/TXT)
│
├── 📄 main.py                  # Pipeline principal orquestrador
├── 📄 streamlit_app.py         # Dashboard interativo
├── 📄 requirements.txt         # Dependências Python
├── 📄 requirements_streamlit.txt  # Dependências Streamlit Cloud
├── 📄 .env.template           # Template de variáveis de ambiente
└── 📄 README.md               # Esta documentação
```

### 🏛️ Arquitetura Medallion

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Raw Layer  │───▶│ Silver Layer │───▶│ Gold Layer  │
│   (JSON)    │    │   (Parquet)  │    │(Parquet/JSON)│
└─────────────┘    └──────────────┘    └─────────────┘
      │                    │                    │
      ▼                    ▼                    ▼
  API Bruta          Validado +            Agregações
  4KB/dia           Normalizado            + Métricas
                    15+ regras              5 arquivos
```

---

## ⚙️ Configuração do Ambiente

### Pré-requisitos

- Python 3.8+
- Git
- Conta [Exchange Rate API](https://www.exchangerate-api.com/) (gratuita)
- Conta [OpenAI](https://platform.openai.com/) (opcional, para LLM)

### 🔧 Instalação

#### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/pipeline-cotacoes-cambiais.git
cd pipeline-cotacoes-cambiais
```

#### 2. Ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

#### 3. Instale dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure variáveis de ambiente
```bash
# Copie o template
copy .env.template .env  # Windows
cp .env.template .env    # Linux/Mac

# Edite .env com suas credenciais
```

**Conteúdo do `.env`:**
```bash
# Exchange Rate API (obrigatório)
EXCHANGE_API_KEY=sua_chave_aqui
EXCHANGE_API_BASE_URL=https://v6.exchangerate-api.com/v6

# OpenAI API (opcional - apenas para LLM)
OPENAI_API_KEY=sua_chave_openai_aqui
OPENAI_MODEL=gpt-3.5-turbo

# Configurações do Pipeline
BASE_CURRENCY=USD
LOG_LEVEL=INFO
```

---

## 🚀 Como Executar

### Pipeline Completo

```bash
# Ativar ambiente virtual
venv\Scripts\activate  # Windows

# Pipeline completo (todas as fases)
python main.py --stage all --log-level INFO
```

#### Execução por Estágios

# Execução padrão (todas as etapas)
python main.py

# Com data específica
python main.py --date 2024-01-15

# Com logging detalhado
python main.py --log-level DEBUG

# Continuar mesmo se LLM falhar
python main.py --skip-llm-on-error
```

### Execução por Estágios

```bash
# 1. Ingestão (coleta dados da API)
python main.py --stage ingest

# 2. Transformação (valida e normaliza)
python main.py --stage transform

# 3. Carga (gera Gold Layer)
python main.py --stage load

# 4. Insights LLM (gera relatórios)
python main.py --stage llm

# Pipeline completo
python main.py --stage all
```

### Opções Disponíveis

```bash
python main.py --help

Opções:
  --stage {ingest,transform,load,llm,all}
                        Estágio a executar (padrão: all)
  --date YYYY-MM-DD     Data para processamento (padrão: hoje)
  --currency XXX        Moeda base (padrão: USD)
  --log-level {DEBUG,INFO,WARNING,ERROR}
                        Nível de logging (padrão: INFO)
  --log-format {console,json}
                        Formato de logs (padrão: console)
  --output-path PATH    Caminho para dados (padrão: data)
  --skip-llm-on-error   Continuar se LLM falhar
```

### Dashboard Interativo

```bash
# Execução local
streamlit run streamlit_app.py

# Acesse em: http://localhost:8501
```

---

## 📊 Dados Processados

### Raw Layer (`data/raw/`)
- **Formato**: JSON
- **Conteúdo**: 163 moedas vs USD com timestamp
- **Tamanho**: ~4KB por dia
- **Exemplo**: `2025-09-30.json`

### Silver Layer (`data/silver/`)
- **Formato**: Parquet (Snappy)
- **Validações**: 15+ regras Pydantic
- **Quality Score**: Calculado automaticamente
- **Exemplo**: `exchange_rates_2025-09-30.parquet`

### Gold Layer (`data/gold/`)

5 arquivos gerados por execução:

1. **daily_metrics_YYYYMMDD_HHMMSS.parquet**
   - Métricas diárias por moeda
   - Taxa atual, min, max, média

2. **historical_trends_YYYYMMDD_HHMMSS.parquet**
   - Séries temporais
   - Médias móveis (7, 14, 30 dias)

3. **currency_summary_YYYYMMDD_HHMMSS.parquet**
   - Resumo consolidado
   - Classificações de tendência e volatilidade

4. **market_overview_YYYYMMDD_HHMMSS.json**
   - Overview geral do mercado
   - Estatísticas agregadas

5. **consolidated_YYYYMMDD_HHMMSS.parquet**
   - Dataset completo unificado
   - Pronto para análise

### Relatórios LLM (`outputs/reports/`)

3 formatos gerados:

1. **insights_report_YYYY-MM-DD.json**
   - Relatório estruturado completo
   - Metadata e contexto

2. **executive_summary_YYYY-MM-DD.md**
   - Resumo executivo formatado
   - Análise técnica detalhada

3. **daily_insights_YYYY-MM-DD.txt**
   - Versão texto simples
   - Fácil compartilhamento

---

## 🔄 Fluxo do Pipeline

### 1. Ingestão (0.5-1s)
- Coleta via Exchange Rate API
- Retry automático (3 tentativas)
- Validação de resposta HTTP
- Salva JSON em Raw Layer

### 2. Transformação (0.04s)
- Normalização para formato tabular
- Validação Pydantic (type-safe)
- Quality score calculation
- Detecção de outliers
- Salva Parquet em Silver Layer

### 3. Carga (0.1s)
- Agregações temporais
- Cálculo de métricas (min, max, avg)
- Classificação de tendências
- Análise de volatilidade
- Gera 5 arquivos Gold Layer

### 4. Insights LLM (2-5s)
- Carrega dados Gold Layer
- Prepara contexto estruturado
- Gera resumo executivo (GPT)
- Gera análise técnica (GPT)
- Salva 3 formatos de relatório
- Fallback automático se API falhar

---

## 🎨 Dashboard Streamlit

### 5 Páginas Interativas

1. **Visão Geral**
   - Status de todas as fases
   - Métricas principais (163 moedas)
   - Arquitetura do sistema

2. **Análise de Mercado**
   - Gráficos interativos (Plotly)
   - Distribuição de tendências
   - Mapa de volatilidade

3. **Dados Detalhados**
   - Tabela filtrada
   - Estatísticas por moeda
   - Exportação de dados

4. **Relatórios LLM**
   - Resumos executivos
   - Análise técnica
   - Downloads disponíveis

5. **Pipeline Status**
   - Log de execuções
   - Métricas de performance
   - Status dos componentes

### Recursos
- Cache inteligente (5 min TTL)
- Fallback para dados de exemplo
- Gráficos adaptativos (Plotly/nativo)
- Responsivo

---

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
pytest

# Com relatório de cobertura
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/unit/test_ingest.py -v
pytest tests/unit/test_transform.py -v
pytest tests/unit/test_load.py -v

# Com logs detalhados
pytest -v -s
```

### Cobertura
- Testes unitários para todas as fases
- Mocks para APIs externas
- Validação end-to-end

---

## 📚 Dependências Principais

| Biblioteca | Versão | Uso |
|------------|--------|-----|
| `pandas` | >=2.0.0 | Manipulação de dados |
| `pyarrow` | >=13.0.0 | Formato Parquet |
| `requests` | >=2.31.0 | Chamadas HTTP |
| `pydantic` | >=2.0.0 | Validação de schemas |
| `structlog` | >=23.0.0 | Logging estruturado |
| `openai` | >=1.0.0 | Integração GPT |
| `streamlit` | >=1.28.0 | Dashboard web |
| `plotly` | >=5.0.0 | Visualizações |
| `pytest` | >=7.0.0 | Framework de testes |

---

## 🔧 Troubleshooting

### Erro 429 (OpenAI)
```
You exceeded your current quota
```

**Solução**:
- Adicione créditos em https://platform.openai.com/account/billing
- Use `--skip-llm-on-error` para continuar sem LLM
- O sistema tem fallback automático

### Arquivos Gold Layer não encontrados
```
Nenhum arquivo Gold Layer encontrado para YYYY-MM-DD
```

**Solução**:
```bash
# Execute pipeline completo primeiro
python main.py --stage all --date YYYY-MM-DD

# Depois execute LLM
python main.py --stage llm --date YYYY-MM-DD
```

### Erro de API Key
```
EXCHANGE_API_KEY não encontrada
```

**Solução**:
- Verifique se `.env` existe
- Confirme que a chave está no formato correto
- Reinicie o terminal após editar `.env`

### Dashboard não carrega dados
**Solução**:
- Execute `python main.py --stage all`
- Aguarde 5 minutos (TTL do cache)
- Verifique `data/gold/` contém arquivos

---

## 🚀 Deploy

### Streamlit Cloud

1. Faça push para GitHub
2. Acesse https://share.streamlit.io/deploy
3. Configure:
   - Repository: `seu-usuario/pipeline-cotacoes-cambiais`
   - Branch: `main`
   - Main file: `streamlit_app.py`
4. Adicione secrets (opcional):
   - `OPENAI_API_KEY`
5. Deploy automático

---

## 📈 Métricas de Performance

### Tempo de Execução Típico

| Etapa | Tempo | Output |
|-------|-------|--------|
| Ingestão | ~0.5s | JSON 4KB |
| Transformação | ~0.04s | Parquet otimizado |
| Carga | ~0.1s | 5 arquivos Gold |
| LLM | ~2-5s | 3 relatórios |
| **Total** | **~3s** | Pipeline completo |

### Qualidade de Dados
- **Moedas**: 163
- **Validações**: 15+ regras Pydantic
- **Quality Score**: Automático
- **Outliers**: Detecção automática

---

## 📝 Estrutura de Logs

### Formato Estruturado (JSON)
```json
{
  "timestamp": "2025-09-30T01:01:49.579350",
  "level": "info",
  "event": "Pipeline concluído com sucesso",
  "stage": "all",
  "execution_time_seconds": 3.2,
  "files_created": 8
}
```

### Localização
- `logs/pipeline_YYYY-MM-DD.log`
- Rotação diária automática

---

## 🎯 Status do Projeto

   **Status**: ✅ **100% COMPLETO E FUNCIONAL**  
   **Data**: 30 Setembro 2025  
   **Versão**: 1.0.0

### Progresso por Fase

   | Fase | Status | Conclusão |
   |------|--------|-----------|
   | 1. Estruturação | ✅ Completa | 100% |
   | 2. Ingestão | ✅ Completa | 100% |
   | 3. Transformação | ✅ Completa | 100% |
   | 4. Carga (Gold) | ✅ Completa | 100% |
   | 5. LLM Integration | ✅ Completa | 100% |
   | 6. Dashboard | ✅ Completa | 100% |

**Todas as fases implementadas e integradas**

---

## 🎓 Créditos Acadêmicos

   **Instituição**: MBA em Data Engineering na Faculdade Impacta de Tecnologia
   **Disciplina**: Python Programming for Data Engineers  
   **Professor**: Eduardo Miranda  
   **Data**: Setembro 2025

**Equipe**:
   - Lucas Alves Gouveia
   - Kauan Gomes
   - Carina de Oliveira

---

## 📄 Licença

   Este projeto é desenvolvido para fins acadêmicos como parte do MBA em Data Engineering.

---

## 🔗 Links Úteis

   - [Exchange Rate API Docs](https://www.exchangerate-api.com/docs)
   - [OpenAI API Reference](https://platform.openai.com/docs)
   - [Streamlit Documentation](https://docs.streamlit.io)
   - [Pydantic Guide](https://docs.pydantic.dev)
   - [Parquet Format](https://parquet.apache.org/docs)

---

**Pipeline de Cotações Cambiais - Produção Ready**
