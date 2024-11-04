package integration_tests

import org.scalatest.{BeforeAndAfterAll, FunSuite}
import broker.pubsub.{Publisher, Subscriber}
import sessions.{SessionManager, RedisSessions}
import storage.{MessageStore, MongoDBStore}
import notifications.InAppNotifications
import auth.JWTAuth
import api.websocket_gateway.Gateway
import monitoring.prometheus.Exporter
import scala.concurrent.duration._
import scala.concurrent.{Await, Future}
import scala.util.{Failure, Success, Try}
import akka.actor.ActorSystem
import akka.http.scaladsl.Http
import akka.http.scaladsl.model._
import akka.http.scaladsl.model.ws._
import akka.stream.scaladsl.{Flow, Sink, Source}

class IntegrationTests extends FunSuite with BeforeAndAfterAll {

  implicit val system: ActorSystem = ActorSystem("IntegrationTests")
  implicit val ec = system.dispatcher

  var publisher: Publisher = _
  var subscriber: Subscriber = _
  var sessionManager: SessionManager = _
  var messageStore: MessageStore = _
  var redisSessions: RedisSessions = _
  var inAppNotifications: InAppNotifications = _
  var jwtAuth: JWTAuth = _
  var websocketGateway: Gateway = _
  var prometheusExporter: Exporter = _

  override def beforeAll(): Unit = {
    // Initialize components for the test suite
    publisher = new Publisher()
    subscriber = new Subscriber()
    sessionManager = new SessionManager()
    messageStore = new MongoDBStore()
    redisSessions = new RedisSessions()
    inAppNotifications = new InAppNotifications()
    jwtAuth = new JWTAuth()
    websocketGateway = new Gateway()
    prometheusExporter = new Exporter()

    // Simulate setting up necessary configurations and dependencies
    println("Initializing integration test suite...")
  }

  override def afterAll(): Unit = {
    // Cleanup resources after tests are complete
    Await.result(system.terminate(), 10.seconds)
  }

  test("Test message publishing and subscription workflow") {
    val topic = "testTopic"
    val message = "Hello, this is a test message"
    val resultFuture = for {
      _ <- publisher.publish(topic, message)
      receivedMessage <- subscriber.subscribe(topic)
    } yield receivedMessage

    val result = Await.result(resultFuture, 5.seconds)
    assert(result == message, "Subscriber should receive the published message")
  }

  test("Test session management with Redis") {
    val userId = "user123"
    val sessionId = sessionManager.createSession(userId)
    assert(sessionId.nonEmpty, "Session ID should not be empty")
    
    val isSessionActive = redisSessions.isSessionActive(sessionId)
    assert(isSessionActive, "Session should be active after creation")
    
    sessionManager.terminateSession(sessionId)
    val isSessionActiveAfterTermination = redisSessions.isSessionActive(sessionId)
    assert(!isSessionActiveAfterTermination, "Session should be terminated successfully")
  }

  test("Test message storage in MongoDB") {
    val messageId = "msg001"
    val content = "Test message content"
    
    val storeResult = messageStore.storeMessage(messageId, content)
    assert(storeResult, "Message should be stored successfully")
    
    val retrievedMessage = messageStore.retrieveMessage(messageId)
    assert(retrievedMessage == content, "Stored and retrieved message content should match")
  }

  test("Test WebSocket gateway communication") {
    val wsUri = "ws://localhost:8080/ws"
    val testMessage = "Hello WebSocket!"

    val webSocketFlow = Http().webSocketClientFlow(WebSocketRequest(wsUri))

    val messageSource = Source.single(TextMessage(testMessage))
    val messageSink = Sink.head[Message]

    val ((wsUpgrade, responseFuture), receivedMessage) =
      messageSource
        .viaMat(webSocketFlow)(Keep.both)
        .toMat(messageSink)(Keep.both)
        .run()

    val upgradeResponse = Await.result(wsUpgrade, 3.seconds)
    assert(upgradeResponse.response.status == StatusCodes.SwitchingProtocols, "WebSocket upgrade should succeed")

    val receivedText = Await.result(receivedMessage, 3.seconds) match {
      case TextMessage.Strict(text) => text
      case _ => fail("Expected strict text message")
    }

    assert(receivedText == testMessage, "WebSocket should echo back the sent message")
  }

  test("Test JWT authentication") {
    val userId = "user123"
    val token = jwtAuth.generateToken(userId)
    assert(token.nonEmpty, "JWT token should be generated")
    
    val isValid = jwtAuth.validateToken(token)
    assert(isValid, "JWT token should be valid")
  }

  test("Test in-app notifications") {
    val userId = "user123"
    val notificationMessage = "You have a new message"
    
    val notifyResult = inAppNotifications.sendNotification(userId, notificationMessage)
    assert(notifyResult, "Notification should be sent successfully")
    
    val lastNotification = inAppNotifications.getLastNotification(userId)
    assert(lastNotification.contains(notificationMessage), "Last notification should match the sent notification")
  }

  test("Test Prometheus metrics exporter") {
    val metricsData = prometheusExporter.exportMetrics()
    assert(metricsData.nonEmpty, "Metrics data should be exported")
    
    val httpRequestsMetric = metricsData.find(_.name == "http_requests_total")
    assert(httpRequestsMetric.isDefined, "HTTP requests metric should be exported")
  }
}