package distributed_sessions

import redis.clients.jedis.{Jedis, JedisPool, JedisPoolConfig}
import java.time.Instant
import java.util.UUID
import scala.concurrent.{ExecutionContext, Future}
import scala.util.{Failure, Success}

case class SessionData(sessionId: String, userId: String, createdAt: Long, expiresAt: Long)

class RedisSessionManager(redisHost: String, redisPort: Int, maxSessionDuration: Long = 3600000L)(implicit ec: ExecutionContext) {

  private val jedisPoolConfig = new JedisPoolConfig()
  jedisPoolConfig.setMaxTotal(128)
  private val jedisPool = new JedisPool(jedisPoolConfig, redisHost, redisPort)

  // Create a new session for the user
  def createSession(userId: String): Future[SessionData] = Future {
    val sessionId = UUID.randomUUID().toString
    val createdAt = Instant.now().toEpochMilli
    val expiresAt = createdAt + maxSessionDuration

    val sessionData = SessionData(sessionId, userId, createdAt, expiresAt)

    val jedis = jedisPool.getResource
    try {
      jedis.hmset(sessionId, Map(
        "userId" -> userId,
        "createdAt" -> createdAt.toString,
        "expiresAt" -> expiresAt.toString
      ).asJava)
      jedis.expireAt(sessionId, expiresAt / 1000)
    } finally {
      jedis.close()
    }

    sessionData
  }

  // Retrieve a session by sessionId
  def getSession(sessionId: String): Future[Option[SessionData]] = Future {
    val jedis = jedisPool.getResource
    try {
      val sessionInfo = jedis.hgetAll(sessionId)
      if (sessionInfo.isEmpty) {
        None
      } else {
        Some(SessionData(
          sessionId,
          sessionInfo.get("userId"),
          sessionInfo.get("createdAt").toLong,
          sessionInfo.get("expiresAt").toLong
        ))
      }
    } finally {
      jedis.close()
    }
  }

  // Extend a session's expiration time
  def extendSession(sessionId: String, extraTime: Long): Future[Boolean] = Future {
    val jedis = jedisPool.getResource
    try {
      val sessionInfo = jedis.hgetAll(sessionId)
      if (sessionInfo.isEmpty) {
        false
      } else {
        val newExpiresAt = Instant.now().toEpochMilli + extraTime
        jedis.hset(sessionId, "expiresAt", newExpiresAt.toString)
        jedis.expireAt(sessionId, newExpiresAt / 1000)
        true
      }
    } finally {
      jedis.close()
    }
  }

  // Invalidate a session
  def invalidateSession(sessionId: String): Future[Boolean] = Future {
    val jedis = jedisPool.getResource
    try {
      jedis.del(sessionId) > 0
    } finally {
      jedis.close()
    }
  }

  // Clean up expired sessions
  def cleanupExpiredSessions(): Future[Unit] = Future {
    val jedis = jedisPool.getResource
    try {
      val sessionKeys = jedis.keys("*").asScala
      sessionKeys.foreach { sessionId =>
        val sessionInfo = jedis.hgetAll(sessionId)
        val expiresAt = sessionInfo.get("expiresAt").toLong
        if (Instant.now().toEpochMilli > expiresAt) {
          jedis.del(sessionId)
        }
      }
    } finally {
      jedis.close()
    }
  }

  // Check if a session is valid
  def isSessionValid(sessionId: String): Future[Boolean] = getSession(sessionId).map {
    case Some(session) => Instant.now().toEpochMilli < session.expiresAt
    case None => false
  }

  // Shutdown the Redis connection pool
  def shutdown(): Unit = {
    jedisPool.destroy()
  }
}

object RedisSessionManagerApp extends App {
  implicit val ec: ExecutionContext = ExecutionContext.global
  val sessionManager = new RedisSessionManager("localhost", 6379)

  // Create a new session
  sessionManager.createSession("user123").onComplete {
    case Success(sessionData) =>
      println(s"Created session: $sessionData")
    case Failure(exception) =>
      println(s"Failed to create session: ${exception.getMessage}")
  }

  // Fetch a session
  sessionManager.getSession("some-session-id").onComplete {
    case Success(Some(sessionData)) =>
      println(s"Session data: $sessionData")
    case Success(None) =>
      println("Session not found")
    case Failure(exception) =>
      println(s"Failed to retrieve session: ${exception.getMessage}")
  }

  // Extend a session
  sessionManager.extendSession("some-session-id", 3600000L).onComplete {
    case Success(true) =>
      println("Session extended successfully")
    case Success(false) =>
      println("Session not found")
    case Failure(exception) =>
      println(s"Failed to extend session: ${exception.getMessage}")
  }

  // Invalidate a session
  sessionManager.invalidateSession("some-session-id").onComplete {
    case Success(true) =>
      println("Session invalidated successfully")
    case Success(false) =>
      println("Session not found")
    case Failure(exception) =>
      println(s"Failed to invalidate session: ${exception.getMessage}")
  }

  // Clean up expired sessions
  sessionManager.cleanupExpiredSessions().onComplete {
    case Success(_) =>
      println("Expired sessions cleaned up")
    case Failure(exception) =>
      println(s"Failed to clean up expired sessions: ${exception.getMessage}")
  }

  // Shutdown the session manager
  sys.addShutdownHook {
    sessionManager.shutdown()
  }
}