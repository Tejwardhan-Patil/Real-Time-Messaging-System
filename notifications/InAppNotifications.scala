package notifications

import scala.collection.mutable.ListBuffer

case class Notification(id: String, message: String, userId: String, read: Boolean = false, timestamp: Long = System.currentTimeMillis())

class InAppNotificationService {

  // List to store all notifications
  private val notifications: ListBuffer[Notification] = ListBuffer()

  // Create a new notification for a user
  def createNotification(message: String, userId: String): Notification = {
    val notification = Notification(generateId(), message, userId)
    notifications += notification
    notification
  }

  // Mark a notification as read
  def markAsRead(notificationId: String, userId: String): Option[Notification] = {
    notifications.find(n => n.id == notificationId && n.userId == userId) match {
      case Some(notification) =>
        val updatedNotification = notification.copy(read = true)
        notifications -= notification
        notifications += updatedNotification
        Some(updatedNotification)
      case None => None
    }
  }

  // Get all notifications for a user
  def getNotificationsForUser(userId: String): List[Notification] = {
    notifications.filter(_.userId == userId).toList
  }

  // Get unread notifications count for a user
  def getUnreadCountForUser(userId: String): Int = {
    notifications.count(n => n.userId == userId && !n.read)
  }

  // Clear all notifications for a user
  def clearNotificationsForUser(userId: String): Unit = {
    notifications --= notifications.filter(_.userId == userId)
  }

  // Generate a unique notification ID
  private def generateId(): String = java.util.UUID.randomUUID().toString
}

// Notification Dispatcher Trait
trait NotificationDispatcher {
  def dispatch(notification: Notification): Unit
}

// In-App Notification Dispatcher (To UI)
class InAppNotificationDispatcher extends NotificationDispatcher {
  override def dispatch(notification: Notification): Unit = {
    println(s"Dispatching in-app notification: ${notification.message} to user ${notification.userId}")
    // Code to send notification to the user's UI (WebSocket, etc)
  }
}

// Service for subscribing and notifying users
class NotificationSubscriber {
  private val listeners = ListBuffer[NotificationDispatcher]()

  def subscribe(listener: NotificationDispatcher): Unit = {
    listeners += listener
  }

  def unsubscribe(listener: NotificationDispatcher): Unit = {
    listeners -= listener
  }

  def notifyListeners(notification: Notification): Unit = {
    listeners.foreach(_.dispatch(notification))
  }
}

// Testing the In-App Notifications functionality
object InAppNotificationsTest {
  def main(args: Array[String]): Unit = {
    val notificationService = new InAppNotificationService
    val notificationSubscriber = new NotificationSubscriber
    val inAppDispatcher = new InAppNotificationDispatcher

    notificationSubscriber.subscribe(inAppDispatcher)

    val userId = "user123"
    val notification = notificationService.createNotification("You have a new message!", userId)

    // Dispatch notification to UI
    notificationSubscriber.notifyListeners(notification)

    // Mark notification as read
    notificationService.markAsRead(notification.id, userId)

    // Get all notifications for a user
    val userNotifications = notificationService.getNotificationsForUser(userId)
    println(s"User $userId has ${userNotifications.length} notifications.")

    // Get unread notifications count
    val unreadCount = notificationService.getUnreadCountForUser(userId)
    println(s"User $userId has $unreadCount unread notifications.")

    // Clear notifications
    notificationService.clearNotificationsForUser(userId)
    println(s"User $userId notifications cleared.")
  }
}

// Real-time WebSocket integration
class WebSocketNotificationDispatcher extends NotificationDispatcher {
  override def dispatch(notification: Notification): Unit = {
    // Send notification through WebSocket connection
    println(s"Sending notification to user ${notification.userId} via WebSocket: ${notification.message}")
  }
}

// Integrate WebSocket notifications
class RealTimeNotificationService {
  private val notificationService = new InAppNotificationService
  private val subscriber = new NotificationSubscriber

  // Subscribe for real-time notifications
  def subscribeToRealTimeNotifications(dispatcher: NotificationDispatcher): Unit = {
    subscriber.subscribe(dispatcher)
  }

  // Notify users in real-time
  def notifyUser(userId: String, message: String): Unit = {
    val notification = notificationService.createNotification(message, userId)
    subscriber.notifyListeners(notification)
  }

  // Handle notification read/unread status
  def markNotificationAsRead(notificationId: String, userId: String): Unit = {
    notificationService.markAsRead(notificationId, userId)
  }

  // Get unread notifications count
  def getUnreadNotifications(userId: String): Int = {
    notificationService.getUnreadCountForUser(userId)
  }

  // Clear user notifications
  def clearUserNotifications(userId: String): Unit = {
    notificationService.clearNotificationsForUser(userId)
  }
}

// Additional real-time use case
class RealTimeWebSocketManager {
  private val realTimeService = new RealTimeNotificationService
  private val webSocketDispatcher = new WebSocketNotificationDispatcher

  // Initialize WebSocket connection and subscribe
  def initializeWebSocketForUser(): Unit = {
    realTimeService.subscribeToRealTimeNotifications(webSocketDispatcher)
  }

  // Notify user through WebSocket
  def notifyUserViaWebSocket(userId: String, message: String): Unit = {
    realTimeService.notifyUser(userId, message)
  }
}