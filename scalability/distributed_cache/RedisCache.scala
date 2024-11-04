import redis.clients.jedis.{Jedis, JedisPool, JedisPoolConfig}
import scala.concurrent.{Future, ExecutionContext}
import scala.util.{Failure, Success, Try}

class RedisCache(host: String, port: Int)(implicit ec: ExecutionContext) {

  private val poolConfig = new JedisPoolConfig()
  poolConfig.setMaxTotal(128)
  poolConfig.setMaxIdle(128)
  poolConfig.setMinIdle(16)
  poolConfig.setTestOnBorrow(true)
  poolConfig.setTestOnReturn(true)
  poolConfig.setTestWhileIdle(true)
  poolConfig.setMinEvictableIdleTimeMillis(60000)
  poolConfig.setTimeBetweenEvictionRunsMillis(30000)
  poolConfig.setNumTestsPerEvictionRun(3)
  poolConfig.setBlockWhenExhausted(true)

  private val jedisPool = new JedisPool(poolConfig, host, port)

  def withRedisClient[T](op: Jedis => T): Try[T] = {
    val jedis = jedisPool.getResource
    try {
      Success(op(jedis))
    } catch {
      case e: Exception => Failure(e)
    } finally {
      jedis.close()
    }
  }

  def set(key: String, value: String, ttl: Int = 0): Future[Boolean] = Future {
    withRedisClient { jedis =>
      val response = if (ttl > 0) jedis.setex(key, ttl, value) else jedis.set(key, value)
      response == "OK"
    }.getOrElse(false)
  }

  def get(key: String): Future[Option[String]] = Future {
    withRedisClient { jedis =>
      Option(jedis.get(key))
    }.getOrElse(None)
  }

  def delete(key: String): Future[Long] = Future {
    withRedisClient { jedis =>
      jedis.del(key)
    }.getOrElse(0L)
  }

  def increment(key: String, by: Long = 1): Future[Long] = Future {
    withRedisClient { jedis =>
      jedis.incrBy(key, by)
    }.getOrElse(0L)
  }

  def exists(key: String): Future[Boolean] = Future {
    withRedisClient { jedis =>
      jedis.exists(key)
    }.getOrElse(false)
  }

  def expire(key: String, ttl: Int): Future[Boolean] = Future {
    withRedisClient { jedis =>
      jedis.expire(key, ttl) == 1
    }.getOrElse(false)
  }

  def flushAll(): Future[Boolean] = Future {
    withRedisClient { jedis =>
      jedis.flushAll()
      true
    }.getOrElse(false)
  }

  def close(): Unit = {
    jedisPool.close()
  }
}

// RedisCache companion object for managing cache initialization and shutdown
object RedisCache {

  private var redisCache: Option[RedisCache] = None

  def init(host: String, port: Int)(implicit ec: ExecutionContext): RedisCache = {
    redisCache match {
      case Some(cache) => cache
      case None =>
        val cache = new RedisCache(host, port)
        redisCache = Some(cache)
        cache
    }
  }

  def shutdown(): Unit = {
    redisCache.foreach(_.close())
    redisCache = None
  }
}

// Usage
import scala.concurrent.ExecutionContext.Implicits.global

object RedisCacheApp extends App {
  val cache = RedisCache.init("localhost", 6379)

  // Set cache value with a TTL
  cache.set("session:123", "user data", 3600).onComplete {
    case Success(status) => println(s"Set status: $status")
    case Failure(ex)     => println(s"Error: $ex")
  }

  // Get cached value
  cache.get("session:123").onComplete {
    case Success(Some(value)) => println(s"Get value: $value")
    case Success(None)        => println("Key not found")
    case Failure(ex)          => println(s"Error: $ex")
  }

  // Increment a counter
  cache.increment("page:views").onComplete {
    case Success(newValue) => println(s"Page views: $newValue")
    case Failure(ex)       => println(s"Error: $ex")
  }

  // Check if key exists
  cache.exists("session:123").onComplete {
    case Success(exists) => println(s"Key exists: $exists")
    case Failure(ex)     => println(s"Error: $ex")
  }

  // Delete a key
  cache.delete("session:123").onComplete {
    case Success(result) => println(s"Delete result: $result")
    case Failure(ex)     => println(s"Error: $ex")
  }

  // Set expiration for a key
  cache.expire("session:123", 600).onComplete {
    case Success(status) => println(s"Expire status: $status")
    case Failure(ex)     => println(s"Error: $ex")
  }

  // Flush all cache data
  cache.flushAll().onComplete {
    case Success(status) => println(s"Flush all status: $status")
    case Failure(ex)     => println(s"Error: $ex")
  }

  // Graceful shutdown
  sys.addShutdownHook {
    RedisCache.shutdown()
  }
}