import play.api.libs.json._

// Case class to define the structure of Grafana Panels
case class Panel(
    id: Int,
    title: String,
    gridPos: GridPos,
    targets: Seq[Target],
    `type`: String = "graph"
)

case class GridPos(h: Int, w: Int, x: Int, y: Int)
case class Target(expr: String)

// Grafana Dashboard case class
case class Dashboard(
    id: Option[Int],
    title: String,
    panels: Seq[Panel],
    refresh: Option[String] = Some("5s"),
    schemaVersion: Int = 18
)

object Dashboards {
  // Creates a sample dashboard with panels
  def createMessagingSystemDashboard(): Dashboard = {
    // Define the panels for metrics like total messages, error rates, etc
    val messageRatePanel = Panel(
      id = 1,
      title = "Message Rate",
      gridPos = GridPos(8, 12, 0, 0),
      targets = Seq(Target(expr = "rate(messages_total[5m])"))
    )

    val errorRatePanel = Panel(
      id = 2,
      title = "Error Rate",
      gridPos = GridPos(8, 12, 0, 9),
      targets = Seq(Target(expr = "rate(errors_total[5m])"))
    )

    val activeSessionsPanel = Panel(
      id = 3,
      title = "Active Sessions",
      gridPos = GridPos(8, 12, 12, 0),
      targets = Seq(Target(expr = "session_active_total"))
    )

    val queueLengthPanel = Panel(
      id = 4,
      title = "Queue Length",
      gridPos = GridPos(8, 12, 12, 9),
      targets = Seq(Target(expr = "queue_length"))
    )

    // Create a dashboard by assembling panels
    Dashboard(
      id = None,
      title = "Messaging System Monitoring",
      panels = Seq(messageRatePanel, errorRatePanel, activeSessionsPanel, queueLengthPanel)
    )
  }

  // Convert a dashboard into JSON format to be uploaded to Grafana
  def toJson(dashboard: Dashboard): JsValue = {
    Json.toJson(dashboard)(Json.writes[Dashboard])
  }

  // Function to upload a dashboard to Grafana server
  def uploadToGrafana(dashboard: Dashboard, grafanaUrl: String, apiKey: String): Unit = {
    val jsonDashboard = toJson(dashboard)

    val result = requests.post(
      url = s"$grafanaUrl/api/dashboards/db",
      headers = Map(
        "Authorization" -> s"Bearer $apiKey",
        "Content-Type" -> "application/json"
      ),
      data = jsonDashboard.toString()
    )

    if (result.statusCode == 200) {
      println("Dashboard successfully uploaded to Grafana.")
    } else {
      println(s"Failed to upload dashboard: ${result.statusMessage}")
    }
  }

  // Function to generate a full dashboard configuration
  def generateDashboardConfig(): Unit = {
    val dashboard = createMessagingSystemDashboard()

    val grafanaUrl = "http://grafana.website.com"
    val apiKey = "grafana_api_key_here"

    uploadToGrafana(dashboard, grafanaUrl, apiKey)
  }

  // Method to add new panels dynamically
  def addPanel(
      dashboard: Dashboard,
      title: String,
      expr: String,
      x: Int,
      y: Int,
      w: Int = 12,
      h: Int = 8
  ): Dashboard = {
    val newPanel = Panel(
      id = dashboard.panels.size + 1,
      title = title,
      gridPos = GridPos(h, w, x, y),
      targets = Seq(Target(expr = expr))
    )

    dashboard.copy(panels = dashboard.panels :+ newPanel)
  }

  // Function to create a detailed session monitoring panel
  def sessionMonitoringPanel(): Panel = {
    Panel(
      id = 5,
      title = "Session Duration",
      gridPos = GridPos(8, 12, 0, 18),
      targets = Seq(Target(expr = "histogram_quantile(0.95, rate(session_duration_seconds_bucket[5m]))"))
    )
  }

  // Function to generate an enhanced dashboard with additional metrics
  def generateEnhancedDashboard(): Dashboard = {
    val dashboard = createMessagingSystemDashboard()

    val enhancedDashboard = addPanel(dashboard, "Memory Usage", "node_memory_MemAvailable_bytes", 0, 18)
    addPanel(enhancedDashboard, "CPU Load", "node_load1", 0, 27)
  }

  // Function to remove a panel by ID
  def removePanel(dashboard: Dashboard, panelId: Int): Dashboard = {
    val filteredPanels = dashboard.panels.filterNot(_.id == panelId)
    dashboard.copy(panels = filteredPanels)
  }
}

object GrafanaDashboardApp {
  def main(args: Array[String]): Unit = {
    val dashboard = Dashboards.createMessagingSystemDashboard()

    // Upload the dashboard to Grafana
    Dashboards.generateDashboardConfig()

    // Display the dashboard JSON
    println(Json.prettyPrint(Dashboards.toJson(dashboard)))
  }
}