import com.rabbitmq.client.{Channel, Connection, ConnectionFactory, DeliverCallback, AMQP}
import scala.util.{Try, Success, Failure}
import scala.concurrent.{ExecutionContext, Future, Promise}
import java.util.concurrent.TimeoutException

// RabbitMQProtocol to manage publishing and consuming messages
object RabbitMQProtocol {

  private val factory = new ConnectionFactory()
  factory.setHost("localhost") 
  factory.setPort(5672)       
  factory.setUsername("guest") 
  factory.setPassword("guest") 

  // Establish connection to RabbitMQ
  def createConnection(): Try[Connection] = {
    Try(factory.newConnection()) match {
      case Success(connection) => Success(connection)
      case Failure(exception) => 
        println(s"Failed to connect to RabbitMQ: ${exception.getMessage}")
        Failure(exception)
    }
  }

  // Create channel from the connection
  def createChannel(connection: Connection): Try[Channel] = {
    Try(connection.createChannel()) match {
      case Success(channel) => Success(channel)
      case Failure(exception) => 
        println(s"Failed to create channel: ${exception.getMessage}")
        Failure(exception)
    }
  }

  // Declare a queue
  def declareQueue(channel: Channel, queueName: String): Unit = {
    channel.queueDeclare(queueName, true, false, false, null)
  }

  // Publish message to the queue
  def publishMessage(channel: Channel, queueName: String, message: String): Unit = {
    val messageBytes = message.getBytes("UTF-8")
    channel.basicPublish("", queueName, null, messageBytes)
    println(s"Message published to queue $queueName: $message")
  }

  // Consume message from the queue
  def consumeMessage(channel: Channel, queueName: String)(implicit ec: ExecutionContext): Future[String] = {
    val promise = Promise[String]()
    val deliverCallback: DeliverCallback = (consumerTag, delivery) => {
      val message = new String(delivery.getBody, "UTF-8")
      println(s"Message received: $message")
      promise.success(message)
    }
    channel.basicConsume(queueName, true, deliverCallback, _ => {})
    promise.future
  }

  // Close the channel and connection
  def close(channel: Channel, connection: Connection): Unit = {
    Try(channel.close())
    Try(connection.close())
  }

  // Publish and consume message utility
  def publishAndConsume(queueName: String, message: String)(implicit ec: ExecutionContext): Future[String] = {
    createConnection() match {
      case Success(connection) => 
        createChannel(connection) match {
          case Success(channel) =>
            declareQueue(channel, queueName)
            publishMessage(channel, queueName, message)
            val result = consumeMessage(channel, queueName)
            result.onComplete(_ => close(channel, connection))
            result
          case Failure(e) => 
            println("Failed to create channel.")
            Future.failed(e)
        }
      case Failure(e) =>
        println("Failed to create connection.")
        Future.failed(e)
    }
  }
}

// Usage
import scala.concurrent.ExecutionContext.Implicits.global
import scala.concurrent.duration._
import scala.concurrent.Await

object RabbitMQTestApp extends App {

  val queueName = "testQueue"
  val testMessage = "Hello RabbitMQ!"

  val result = RabbitMQProtocol.publishAndConsume(queueName, testMessage)

  result.onComplete {
    case Success(msg) => println(s"Received message: $msg")
    case Failure(e) => println(s"Error: ${e.getMessage}")
  }

  Await.result(result, 10.seconds) 
}