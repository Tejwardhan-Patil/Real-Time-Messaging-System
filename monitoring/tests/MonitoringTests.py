import unittest
import subprocess
import requests
import os
import json
import time
from monitoring.logging.LogConfig import LoggerConfig
from monitoring.analytics.ClickstreamAnalysis import ClickstreamAnalyzer

class TestMonitoringComponents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.logger = LoggerConfig().get_logger()
        cls.clickstream_analyzer = ClickstreamAnalyzer()

    def test_prometheus_exporter(self):
        self.logger.info("Testing Prometheus Exporter by invoking the Go binary")
        try:
            result = subprocess.run(
                ['./monitoring/prometheus/Exporter'], 
                capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("metrics", result.stdout)
            self.logger.info("Prometheus Exporter test passed")
        except Exception as e:
            self.fail(f"Prometheus Exporter test failed: {e}")

    def test_prometheus_endpoint(self):
        self.logger.info("Testing Prometheus endpoint")
        url = "http://localhost:9090/metrics"
        try:
            response = requests.get(url)
            self.assertEqual(response.status_code, 200)
            self.logger.info("Prometheus endpoint is active and returning metrics")
        except requests.ConnectionError as e:
            self.fail(f"Prometheus endpoint test failed: {e}")

    def test_logging_configuration(self):
        self.logger.info("Testing logging configuration")
        try:
            self.logger.error("This is an error log test")
            self.logger.warning("This is a warning log test")
            self.logger.info("This is an info log test")
            self.logger.debug("This is a debug log test")
            self.logger.info("Logging configuration is working as expected")
        except Exception as e:
            self.fail(f"Logging configuration test failed: {e}")

    def test_clickstream_analysis(self):
        self.logger.info("Testing clickstream analysis")
        test_data = [
            {"user_id": "user1", "timestamp": time.time(), "event": "click"},
            {"user_id": "user2", "timestamp": time.time(), "event": "scroll"},
            {"user_id": "user3", "timestamp": time.time(), "event": "hover"},
        ]
        try:
            result = self.clickstream_analyzer.analyze(test_data)
            self.assertIsNotNone(result)
            self.assertTrue("user_engagement" in result)
            self.logger.info("Clickstream analysis test passed")
        except Exception as e:
            self.fail(f"Clickstream analysis test failed: {e}")

    def test_logger_file_output(self):
        self.logger.info("Testing logger file output")
        log_file = "/var/log/system_test.log"
        try:
            with open(log_file, "r") as file:
                logs = file.read()
                self.assertIn("info", logs.lower())
                self.logger.info("Logger file output test passed")
        except FileNotFoundError:
            self.fail(f"Log file not found: {log_file}")
        except Exception as e:
            self.fail(f"Logger file output test failed: {e}")

    def test_prometheus_metrics_format(self):
        self.logger.info("Testing Prometheus metrics format by invoking Go-based Exporter")
        try:
            result = subprocess.run(
                ['./monitoring/prometheus/Exporter'], 
                capture_output=True, text=True
            )
            self.assertIn("http_requests_total", result.stdout)
            self.assertIn("request_duration_seconds", result.stdout)
            self.logger.info("Prometheus metrics format is valid")
        except Exception as e:
            self.fail(f"Prometheus metrics format test failed: {e}")

    def test_alerting_system_integration(self):
        self.logger.info("Testing alerting system integration")
        alerts_url = "http://localhost:9093/api/v1/alerts"
        try:
            response = requests.get(alerts_url)
            self.assertEqual(response.status_code, 200)
            self.logger.info("Alerting system integration test passed")
        except requests.ConnectionError as e:
            self.fail(f"Alerting system integration test failed: {e}")

    def test_metrics_scraping(self):
        self.logger.info("Testing metrics scraping from Prometheus")
        scrape_url = "http://localhost:9090/api/v1/query"
        query = {"query": "http_requests_total"}
        try:
            response = requests.get(scrape_url, params=query)
            data = response.json()
            self.assertTrue("data" in data)
            self.logger.info("Metrics scraping test passed")
        except requests.ConnectionError as e:
            self.fail(f"Metrics scraping test failed: {e}")

    def test_grafana_dashboards(self):
        self.logger.info("Testing Grafana dashboards")
        grafana_url = "http://localhost:3000/api/dashboards"
        try:
            response = requests.get(grafana_url)
            self.assertEqual(response.status_code, 200)
            self.logger.info("Grafana dashboard test passed")
        except requests.ConnectionError as e:
            self.fail(f"Grafana dashboard test failed: {e}")

    def test_metrics_storage_influxdb(self):
        self.logger.info("Testing metrics storage in InfluxDB")
        influxdb_url = "http://localhost:8086/query"
        query = "SELECT * FROM http_requests_total"
        params = {
            "db": "metrics",
            "q": query
        }
        try:
            response = requests.get(influxdb_url, params=params)
            data = response.json()
            self.assertTrue("results" in data)
            self.logger.info("Metrics storage in InfluxDB test passed")
        except requests.ConnectionError as e:
            self.fail(f"Metrics storage in InfluxDB test failed: {e}")

    def test_log_file_rotation(self):
        self.logger.info("Testing log file rotation")
        log_file = "/var/log/system_test.log"
        try:
            self.logger.info("Generating logs for rotation")
            for i in range(1000):
                self.logger.debug(f"Log entry {i}")
            log_size = os.path.getsize(log_file)
            self.assertLess(log_size, 10 * 1024 * 1024)  # 10 MB max log size
            self.logger.info("Log file rotation test passed")
        except Exception as e:
            self.fail(f"Log file rotation test failed: {e}")

    def test_system_metrics_healthcheck(self):
        self.logger.info("Testing system metrics healthcheck")
        metrics_url = "http://localhost:9090/-/healthy"
        try:
            response = requests.get(metrics_url)
            self.assertEqual(response.status_code, 200)
            self.logger.info("System metrics healthcheck passed")
        except requests.ConnectionError as e:
            self.fail(f"System metrics healthcheck failed: {e}")

if __name__ == "__main__":
    unittest.main()