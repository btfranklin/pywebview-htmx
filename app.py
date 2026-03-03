import time

from pyhtmx import create_window


class API:
    def fetch_data(self, params: dict) -> str:
        user_id = params.get("user_id", "unknown")
        time.sleep(1)
        return f"<p>Data for user {user_id} fetched successfully!</p>"

    def long_process(self, params: dict) -> str:
        _ = params
        time.sleep(5)
        return "<p>Long-running process complete!</p>"


api = API()

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>pyHTMX Demo</title>
  <style>
    .py-waiting {
      opacity: 0.5;
    }
  </style>
</head>
<body>
  <h1>pyHTMX Demo</h1>
  <button
    py-call="fetch_data"
    py-trigger="click"
    py-target="#result"
    py-swap="innerHTML"
    data-py-params='{"user_id": 42}'
    py-wait="#spinner">
    Fetch Data
  </button>
  <div id="spinner" style="display:inline-block; margin-left: 10px;">Loading...</div>
  <div id="result" style="margin-top: 20px;"></div>

  <br><br>

  <button
    py-call="long_process"
    py-trigger="click"
    py-target="#long-result"
    py-swap="innerHTML"
    data-py-params='{}'
    py-wait="">
    Run Long Process
  </button>
  <div id="long-result" style="margin-top: 20px;"></div>
</body>
</html>
"""

if __name__ == "__main__":
    create_window("pyHTMX Demo", html_content, js_api=api)
