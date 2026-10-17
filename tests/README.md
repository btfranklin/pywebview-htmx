# Tests

Run `pdm run test` from the repository root. Python tests check asset injection,
parameter encoding, window setup, and package contents. Browser tests check
runtime behavior in real browser engines with a simulated Python bridge.

Run `pdm run test-native` in a desktop session to check the real Python bridge.
See [development](../docs/development.md) for setup and validation commands.
