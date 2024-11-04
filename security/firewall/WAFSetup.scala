import akka.http.scaladsl.model._
import akka.http.scaladsl.server.Directives._
import akka.http.scaladsl.server.Route
import akka.http.scaladsl.Http
import akka.actor.ActorSystem
import akka.stream.ActorMaterializer
import akka.http.scaladsl.server.RejectionHandler
import akka.http.scaladsl.model.StatusCodes._
import scala.concurrent.Future
import scala.io.StdIn
import akka.http.scaladsl.model.headers._

object WAFSetup {

  implicit val system = ActorSystem("WAFSystem")
  implicit val materializer = ActorMaterializer()
  implicit val executionContext = system.dispatcher

  // Allowed methods and headers for CORS
  private val allowedMethods = List("GET", "POST", "PUT", "DELETE", "OPTIONS")
  private val allowedHeaders = List("Content-Type", "Authorization", "X-Requested-With")
  private val allowedOrigins = List("https://website.com")

  // WAF Rules and Definitions
  def blockSQLInjection(uri: Uri): Boolean = {
    val sqlInjectionPatterns = List("select ", "insert ", "update ", "delete ", "drop ")
    sqlInjectionPatterns.exists(pattern => uri.toString.toLowerCase.contains(pattern))
  }

  def blockXSS(payload: String): Boolean = {
    val xssPatterns = List("<script>", "<iframe>", "<img src=", "<body onload=")
    xssPatterns.exists(pattern => payload.toLowerCase.contains(pattern))
  }

  def blockCommonAttacks(uri: Uri, method: HttpMethod, headers: Seq[HttpHeader], payload: String): Option[String] = {
    if (blockSQLInjection(uri)) Some("SQL Injection detected")
    else if (blockXSS(payload)) Some("XSS attack detected")
    else None
  }

  // CORS handling
  def handleCORS(allowedOrigin: String): Route = {
    respondWithHeaders(
      `Access-Control-Allow-Origin`(HttpOrigin(allowedOrigin)),
      `Access-Control-Allow-Methods`(allowedMethods: _*),
      `Access-Control-Allow-Headers`(allowedHeaders: _*)
    )
  }

  // WAF Routes and Rejection Handler
  val rejectionHandler = RejectionHandler.newBuilder()
    .handleNotFound {
      complete((NotFound, "Not Found"))
    }
    .result()

  def wafRoute: Route = handleRejections(rejectionHandler) {
    extractRequest { req =>
      val uri = req.uri
      val method = req.method
      val headers = req.headers
      val payload = req.entity.toString

      blockCommonAttacks(uri, method, headers, payload) match {
        case Some(error) =>
          complete((BadRequest, error))
        case None =>
          handleCORS("https://website.com") {
            path("secured-endpoint") {
              get {
                complete(HttpResponse(OK, entity = "This is a secured endpoint"))
              } ~
              post {
                complete(HttpResponse(OK, entity = "POST request received"))
              }
            }
          }
      }
    }
  }

  // Start WAF Server
  def startServer(): Future[Http.ServerBinding] = {
    Http().bindAndHandle(wafRoute, "0.0.0.0", 8080)
  }

  def main(args: Array[String]): Unit = {
    val bindingFuture = startServer()

    println("WAF server started at http://localhost:8080/")
    println("Press RETURN to stop...")
    StdIn.readLine() // Run until user presses return
    bindingFuture
      .flatMap(_.unbind())
      .onComplete(_ => system.terminate()) // Shut down server
  }
}