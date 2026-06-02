WITH mean_euro_venda_2025 AS(
    SELECT cotacao_venda, datahoracotacao FROM {{ source('silver', 'silver_euro_cambio') }}
)

SELECT AVG(cotacao_venda) as Valor_media FROM mean_euro_venda_2025
WHERE EXTRACT(YEAR FROM datahoracotacao) = 2025
