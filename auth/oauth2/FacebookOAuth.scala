package auth.oauth2

import java.net.{HttpURLConnection, URL}
import java.io.{BufferedReader, InputStreamReader}
import java.util.Base64
import java.nio.charset.StandardCharsets
import scala.util.{Failure, Success, Try}
import play.api.libs.json._

object FacebookOAuth {
  
  // Facebook OAuth endpoints
  private val authorizationEndpoint = "https://www.facebook.com/v10.0/dialog/oauth"
  private val tokenEndpoint = "https://graph.facebook.com/v10.0/oauth/access_token"
  private val userInfoEndpoint = "https://graph.facebook.com/me"

  // Client configuration
  private val clientId = "client-id"
  private val clientSecret = "client-secret"
  private val redirectUri = "https://website.com/oauth/facebook/callback"
  private val state = "random-generated-state"
  private val scope = "email public_profile"

  // Build the authorization URL
  def getAuthorizationUrl: String = {
    s"$authorizationEndpoint?client_id=$clientId&redirect_uri=$redirectUri&state=$state&scope=$scope"
  }

  // Exchange authorization code for access token
  def getAccessToken(code: String): Try[String] = {
    val tokenUrl = s"$tokenEndpoint?client_id=$clientId&client_secret=$clientSecret&redirect_uri=$redirectUri&code=$code"
    val connection = new URL(tokenUrl).openConnection().asInstanceOf[HttpURLConnection]
    
    connection.setRequestMethod("GET")
    connection.setDoOutput(true)
    connection.setRequestProperty("Content-Type", "application/json")

    val responseCode = connection.getResponseCode

    if (responseCode == HttpURLConnection.HTTP_OK) {
      val reader = new BufferedReader(new InputStreamReader(connection.getInputStream))
      val response = reader.lines().toArray.mkString
      reader.close()

      val json = Json.parse(response)
      (json \ "access_token").asOpt[String] match {
        case Some(token) => Success(token)
        case None => Failure(new RuntimeException("Access token not found in response"))
      }
    } else {
      Failure(new RuntimeException(s"Failed to get access token. Response code: $responseCode"))
    }
  }

  // Retrieve user information using access token
  def getUserInfo(accessToken: String): Try[FacebookUser] = {
    val userInfoUrl = s"$userInfoEndpoint?access_token=$accessToken&fields=id,name,email"
    val connection = new URL(userInfoUrl).openConnection().asInstanceOf[HttpURLConnection]
    
    connection.setRequestMethod("GET")
    connection.setDoOutput(true)
    connection.setRequestProperty("Content-Type", "application/json")

    val responseCode = connection.getResponseCode

    if (responseCode == HttpURLConnection.HTTP_OK) {
      val reader = new BufferedReader(new InputStreamReader(connection.getInputStream))
      val response = reader.lines().toArray.mkString
      reader.close()

      val json = Json.parse(response)
      val userId = (json \ "id").asOpt[String]
      val name = (json \ "name").asOpt[String]
      val email = (json \ "email").asOpt[String]

      (userId, name, email) match {
        case (Some(id), Some(n), Some(e)) => Success(FacebookUser(id, n, e))
        case _ => Failure(new RuntimeException("Missing user information in response"))
      }
    } else {
      Failure(new RuntimeException(s"Failed to get user info. Response code: $responseCode"))
    }
  }

  // Helper method to encode URL parameters
  private def encodeURIComponent(value: String): String = {
    java.net.URLEncoder.encode(value, StandardCharsets.UTF_8.toString)
  }

  // Facebook user data case class
  case class FacebookUser(id: String, name: String, email: String)

  // Utility function to initiate Facebook OAuth2.0 flow
  def initiateOAuthFlow(): Unit = {
    val authorizationUrl = getAuthorizationUrl
    println(s"Please visit the following URL to authorize the application: $authorizationUrl")
  }

  // Simulate OAuth callback handling
  def handleOAuthCallback(authCode: String): Unit = {
    getAccessToken(authCode) match {
      case Success(accessToken) =>
        println(s"Access token obtained: $accessToken")
        getUserInfo(accessToken) match {
          case Success(user) =>
            println(s"User info: ${user.name}, ${user.email}")
          case Failure(e) =>
            println(s"Failed to retrieve user info: ${e.getMessage}")
        }
      case Failure(e) =>
        println(s"Failed to obtain access token: ${e.getMessage}")
    }
  }

  // Facebook token introspection endpoint
  def introspectAccessToken(accessToken: String): Try[Boolean] = {
    val introspectionUrl = s"https://graph.facebook.com/debug_token?input_token=$accessToken&access_token=$clientId|$clientSecret"
    val connection = new URL(introspectionUrl).openConnection().asInstanceOf[HttpURLConnection]
    
    connection.setRequestMethod("GET")
    connection.setDoOutput(true)
    connection.setRequestProperty("Content-Type", "application/json")

    val responseCode = connection.getResponseCode

    if (responseCode == HttpURLConnection.HTTP_OK) {
      val reader = new BufferedReader(new InputStreamReader(connection.getInputStream))
      val response = reader.lines().toArray.mkString
      reader.close()

      val json = Json.parse(response)
      val isValid = (json \ "data" \ "is_valid").asOpt[Boolean].getOrElse(false)

      Success(isValid)
    } else {
      Failure(new RuntimeException(s"Failed to introspect token. Response code: $responseCode"))
    }
  }

  // Revoke access token
  def revokeAccessToken(accessToken: String): Try[Boolean] = {
    val revokeUrl = s"https://graph.facebook.com/v10.0/me/permissions?access_token=$accessToken"
    val connection = new URL(revokeUrl).openConnection().asInstanceOf[HttpURLConnection]
    
    connection.setRequestMethod("DELETE")
    connection.setDoOutput(true)
    connection.setRequestProperty("Content-Type", "application/json")

    val responseCode = connection.getResponseCode

    if (responseCode == HttpURLConnection.HTTP_OK) {
      Success(true)
    } else {
      Failure(new RuntimeException(s"Failed to revoke token. Response code: $responseCode"))
    }
  }

  // Main method for testing
  def main(args: Array[String]): Unit = {
    // Simulate the OAuth2 flow
    initiateOAuthFlow()
    
    // Simulate handling the OAuth2 callback
    val authCode = "authorization-code"
    handleOAuthCallback(authCode)
  }
}