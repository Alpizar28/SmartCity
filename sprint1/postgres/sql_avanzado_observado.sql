-- Solo lectura, v1/v2. Ranking de CANALES OBSERVADOS, no sensores físicos.
-- Evita depender del inventario administrativo sintético de PG08.
WITH channel_counts AS (
    SELECT channel_id, COUNT(*) AS reading_count
    FROM smartcity.observations
    WHERE observed_at >= TIMESTAMPTZ '2025-01-01 00:00:00+01'
      AND observed_at < TIMESTAMPTZ '2025-02-01 00:00:00+01'
    GROUP BY channel_id
    HAVING COUNT(*) > 0
)
SELECT channel_id, reading_count,
       DENSE_RANK() OVER (ORDER BY reading_count DESC) AS activity_rank
FROM channel_counts
ORDER BY activity_rank, channel_id
LIMIT 5;
