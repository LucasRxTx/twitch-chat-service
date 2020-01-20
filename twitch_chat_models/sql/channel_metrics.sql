SELECT 
  lulz_per_minute.count as lulz_per_minute,
  messages_per_minute.count as messages_per_minute,
  chat_sentiment.average as chat_sentiment
FROM (
	SELECT 
      count(id) as count 
	FROM 
      `messages`
	WHERE
      `created_at` >= NOW() - INTERVAL 1 MINUTE
      and `channel` = :channel
      and `has_lul` = 1 
) as lulz_per_minute, (
	SELECT
      COUNT(`id`) as count
	FROM
      `messages`
	WHERE
      `created_at` >= NOW() - INTERVAL 1 MINUTE
      and `channel` = :channel
) as messages_per_minute, (
	SELECT
      SUM(`sentiment`) / COUNT(`sentiment`) as average
	FROM
      `messages`
	WHERE
      `created_at` >= NOW() - INTERVAL 15 MINUTE
      and `channel` = :channel
      and `sentiment` != 0.0
) as chat_sentiment, `messages`