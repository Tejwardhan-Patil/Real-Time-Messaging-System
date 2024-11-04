package websocket_gateway

import akka.actor.{ Actor, ActorRef, ActorSystem, Props }
import akka.stream.ActorMaterializer
import akka.http.scaladsl.Http
import akka.http.scaladsl.model.ws.{ Message, TextMessage, WebSocketUpgradeResponse }
import akka.http.scaladsl.server.Directives._
import akka.http.scaladsl.model.{ HttpRequest, HttpResponse }
import akka.stream.scaladsl.{ Flow, Sink, Source }
import scala.concurrent.Future
import akka.http.scaladsl.model.ws.WebSocketRequest
import akka.pattern.ask
import akka.util.Timeout
import scala.concurrent.duration._
import scala.io.StdIn
import akka.event.Logging

object Gateway extends App {

  implicit val system: ActorSystem = ActorSystem("WebSocketGateway")
  implicit val materializer: ActorMaterializer = ActorMaterializer()
  implicit val executionContext = system.dispatcher

  val log = Logging(system, "Gateway")

  val connectionManager: ActorRef = system.actorOf(Props[ConnectionManager], "connectionManager")

  def handleWebSocketMessages(client: ActorRef): Flow[Message, Message, Any] = {
    val incomingMessages: Sink[Message, Any] = Sink.foreach {
      case TextMessage.Strict(msg) =>
        log.info(s"Received message from client: $msg")
        connectionManager ! ConnectionManager.Broadcast(msg)
      case _ =>
        log.warning("Received non-text message")
    }

    val outgoingMessages: Source[Message, ActorRef] = Source.actorRef[String](bufferSize = 10, OverflowStrategy.fail)
      .mapMaterializedValue { outActor =>
        connectionManager ! ConnectionManager.NewClient(outActor)
        outActor
      }
      .map((msg: String) => TextMessage(msg))

    Flow.fromSinkAndSource(incomingMessages, outgoingMessages)
  }

  val websocketRoute =
    path("ws") {
      handleWebSocketMessagesForProtocol(
        handleWebSocketMessages(connectionManager),
        subprotocol = Some("json")
      )
    }

  val bindingFuture: Future[Http.ServerBinding] = Http().bindAndHandle(websocketRoute, "localhost", 8080)

  log.info(s"Server started at ws://localhost:8080/\nPress RETURN to stop...")
  StdIn.readLine()
  bindingFuture
    .flatMap(_.unbind())
    .onComplete(_ => system.terminate())
}

object ConnectionManager {
  case class NewClient(client: ActorRef)
  case class ClientLeft(client: ActorRef)
  case class Broadcast(message: String)
}

class ConnectionManager extends Actor {
  var clients: Set[ActorRef] = Set.empty

  def receive: Receive = {
    case ConnectionManager.NewClient(client) =>
      clients += client
      context.watch(client)
      sender() ! s"Client ${client.path.name} connected"
      broadcast(s"Client ${client.path.name} joined the chat")

    case ConnectionManager.ClientLeft(client) =>
      clients -= client
      broadcast(s"Client ${client.path.name} left the chat")

    case ConnectionManager.Broadcast(message) =>
      broadcast(message)
  }

  def broadcast(message: String): Unit = {
    clients.foreach(_ ! message)
  }
}