# Runbook Operacional

## Execucao local

```bash
python scripts/run_pipeline.py
streamlit run dashboard/app.py
```

## Checklist de suporte

1. Verificar se os arquivos esperados existem em `data/raw/`.
2. Confirmar configuracoes em `config/sources.yml`.
3. Executar o pipeline.
4. Validar logs em `ops/run_logs/`, quando habilitados.
5. Conferir planilhas em `outputs/excel/`.
6. Abrir o dashboard e validar as tabelas carregadas.

## Problemas comuns

| Sintoma | Possivel causa | Acao |
| --- | --- | --- |
| Banco DuckDB nao encontrado | Pipeline ainda nao executado | Executar `python scripts/run_pipeline.py` |
| Nenhuma tabela no dashboard | SQL de carga ainda vazio | Implementar cargas em `sql/bronze/` |
| Excel sem abas analiticas | Nenhuma tabela com prefixo `gold_` | Criar tabelas finais em `sql/gold/` |

