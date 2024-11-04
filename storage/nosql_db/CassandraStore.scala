package storage.nosql_db

import com.datastax.oss.driver.api.core.CqlSession
import com.datastax.oss.driver.api.core.cql.{ResultSet, SimpleStatement, Row}
import com.datastax.oss.driver.api.core.uuid.Uuids
import java.net.InetSocketAddress
import java.util.UUID
import scala.jdk.CollectionConverters._

case class Message(id: UUID, channel: String, sender: String, body: String, timestamp: Long)

object CassandraStore {
  private val cassandraHost = "127.0.0.1"
  private val cassandraPort = 9042
  private val keyspace = "messaging"
  private val messagesTable = "messages"
  private val session: CqlSession = createSession()

  // Initialize connection to Cassandra
  private def createSession(): CqlSession = {
    CqlSession.builder()
      .addContactPoint(new InetSocketAddress(cassandraHost, cassandraPort))
      .withLocalDatacenter("datacenter1")
      .withKeyspace(keyspace)
      .build()
  }

  // Create keyspace and messages table if they don't exist
  def initializeSchema(): Unit = {
    val keyspaceQuery = s"""
      CREATE KEYSPACE IF NOT EXISTS $keyspace
      WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}
    """
    val tableQuery = s"""
      CREATE TABLE IF NOT EXISTS $keyspace.$messagesTable (
        id UUID PRIMARY KEY,
        channel TEXT,
        sender TEXT,
        body TEXT,
        timestamp BIGINT
      )
    """
    session.execute(keyspaceQuery)
    session.execute(tableQuery)
  }

  // Insert a new message into Cassandra
  def insertMessage(message: Message): Unit = {
    val insertQuery = SimpleStatement.newInstance(
      s"INSERT INTO $keyspace.$messagesTable (id, channel, sender, body, timestamp) VALUES (?, ?, ?, ?, ?)",
      message.id, message.channel, message.sender, message.body, message.timestamp
    )
    session.execute(insertQuery)
  }

  // Fetch all messages for a specific channel
  def getMessagesByChannel(channel: String): Seq[Message] = {
    val selectQuery = SimpleStatement.newInstance(
      s"SELECT id, channel, sender, body, timestamp FROM $keyspace.$messagesTable WHERE channel = ?",
      channel
    )
    val resultSet: ResultSet = session.execute(selectQuery)
    resultSet.all().asScala.map(mapRowToMessage).toSeq
  }

  // Fetch a single message by ID
  def getMessageById(messageId: UUID): Option[Message] = {
    val selectQuery = SimpleStatement.newInstance(
      s"SELECT id, channel, sender, body, timestamp FROM $keyspace.$messagesTable WHERE id = ?",
      messageId
    )
    val resultSet: ResultSet = session.execute(selectQuery)
    val row = resultSet.one()
    if (row != null) Some(mapRowToMessage(row)) else None
  }

  // Delete a message by ID
  def deleteMessageById(messageId: UUID): Unit = {
    val deleteQuery = SimpleStatement.newInstance(
      s"DELETE FROM $keyspace.$messagesTable WHERE id = ?",
      messageId
    )
    session.execute(deleteQuery)
  }

  // Update message content by ID
  def updateMessageContent(messageId: UUID, newBody: String): Unit = {
    val updateQuery = SimpleStatement.newInstance(
      s"UPDATE $keyspace.$messagesTable SET body = ? WHERE id = ?",
      newBody, messageId
    )
    session.execute(updateQuery)
  }

  // Helper function to map a row to a Message object
  private def mapRowToMessage(row: Row): Message = {
    Message(
      row.getUuid("id"),
      row.getString("channel"),
      row.getString("sender"),
      row.getString("body"),
      row.getLong("timestamp")
    )
  }

  // Fetch messages with pagination support
  def getMessagesWithPagination(channel: String, pageSize: Int, pagingState: Option[String] = None): (Seq[Message], Option[String]) = {
    val selectQuery = SimpleStatement.builder(
      s"SELECT id, channel, sender, body, timestamp FROM $keyspace.$messagesTable WHERE channel = ?"
    )
      .setPageSize(pageSize)
      .addPositionalValue(channel)
      .build()

    val resultSet: ResultSet = pagingState match {
      case Some(state) => session.execute(selectQuery.setPagingState(state))
      case None => session.execute(selectQuery)
    }

    val messages = resultSet.currentPage().asScala.map(mapRowToMessage).toSeq
    val nextPage = Option(resultSet.getExecutionInfo.getPagingState).map(_.toString)
    (messages, nextPage)
  }

  // Fetch recent messages by timestamp range
  def getMessagesByTimestamp(channel: String, from: Long, to: Long): Seq[Message] = {
    val selectQuery = SimpleStatement.newInstance(
      s"SELECT id, channel, sender, body, timestamp FROM $keyspace.$messagesTable WHERE channel = ? AND timestamp >= ? AND timestamp <= ?",
      channel, from, to
    )
    val resultSet: ResultSet = session.execute(selectQuery)
    resultSet.all().asScala.map(mapRowToMessage).toSeq
  }

  // Get the total count of messages for a channel
  def getMessageCountByChannel(channel: String): Long = {
    val countQuery = SimpleStatement.newInstance(
      s"SELECT COUNT(*) FROM $keyspace.$messagesTable WHERE channel = ?",
      channel
    )
    val resultSet: ResultSet = session.execute(countQuery)
    resultSet.one().getLong(0)
  }

  // Batch insert multiple messages into Cassandra
  def batchInsertMessages(messages: Seq[Message]): Unit = {
    val batchQuery = SimpleStatement.builder(
      s"BEGIN BATCH " +
        messages.map { message =>
          s"INSERT INTO $keyspace.$messagesTable (id, channel, sender, body, timestamp) VALUES (${message.id}, '${message.channel}', '${message.sender}', '${message.body}', ${message.timestamp})"
        }.mkString(" ") +
        " APPLY BATCH;"
    ).build()
    session.execute(batchQuery)
  }

  // Close the Cassandra session
  def close(): Unit = {
    session.close()
  }
}

// Usage
object CassandraStoreApp extends App {
  CassandraStore.initializeSchema()

  // Insert a message
  val message = Message(Uuids.timeBased(), "general", "Person1", "Hello, world!", System.currentTimeMillis())
  CassandraStore.insertMessage(message)

  // Retrieve and print messages
  val messages = CassandraStore.getMessagesByChannel("general")
  messages.foreach(println)

  // Close connection
  CassandraStore.close()
}