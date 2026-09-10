WITH selling_currency_2024_to_2025 AS (
    SELECT cotacao_venda_dol, data_publicacao FROM {{source('gold', 'cambio_eur_usd')}}
)

SELECT AVG(cotacao_venda_dol) FROM selling_currency_2024_to_2025
WHERE EXTRACT(YEAR FROM data_publicacao) >=2024