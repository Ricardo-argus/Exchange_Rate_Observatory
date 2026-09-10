WITH selling_EURUSD_variation_2025 AS(
    SELECT 
    variacao_venda_moeda, 
    data_publicacao 
    FROM {{ source('gold', 'cambio_eur_usd') }}
)

SELECT AVG(variacao_venda_moeda) FROM selling_EURUSD_variation_2025
WHERE EXTRACT(YEAR FROM data_publicacao) = 2025