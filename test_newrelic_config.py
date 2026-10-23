import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


class NewRelicConfigTests(unittest.TestCase):
    def test_collector_routing(self):
        config_path = Path(__file__).with_name("newrelic.ini")
        cases = [
            ("test-license-key", None, "collector.newrelic.com"),
            ("eu01xtest-license-key", None, "collector.eu01.nr-data.net"),
            ("test-license-key", "collector.eu01.nr-data.net", "collector.eu01.nr-data.net"),
        ]
        for license_key, host_override, expected_host in cases:
            with self.subTest(license_key=license_key, host_override=host_override):
                env = {
                    key: value for key, value in os.environ.items()
                    if not key.startswith("NEW_RELIC_")
                }
                env["NEW_RELIC_LICENSE_KEY"] = license_key
                if host_override:
                    env["NEW_RELIC_HOST"] = host_override
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        "import json, sys, newrelic.agent; "
                        "newrelic.agent.initialize(sys.argv[1]); "
                        "settings = newrelic.agent.global_settings(); "
                        "print(json.dumps([settings.host, settings.license_key, "
                        "settings.app_name, settings.monitor_mode]))",
                        str(config_path),
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                )
                self.assertEqual(
                    json.loads(result.stdout),
                    [expected_host, license_key, "checkout-service", True],
                )


if __name__ == "__main__":
    unittest.main()
