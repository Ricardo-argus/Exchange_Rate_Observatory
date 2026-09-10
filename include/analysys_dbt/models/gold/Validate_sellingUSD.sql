SELECT
    data_publicacao,
    cotacao_venda_dol,
    {{validate_variation('cotacao_venda_dol')}} as exceeded_20pct
from {{ source('gold', 'cambio_eur_usd') }}