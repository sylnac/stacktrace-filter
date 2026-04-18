# stacktrace-filter

> CLI tool to collapse and annotate Python tracebacks for faster debugging in CI logs

---

## Installation

```bash
pip install stacktrace-filter
```

Or with pipx:

```bash
pipx install stacktrace-filter
```

---

## Usage

Pipe your CI output directly into `stacktrace-filter`:

```bash
pytest 2>&1 | stacktrace-filter
```

Or filter an existing log file:

```bash
stacktrace-filter --input build.log
```

**Example output:**

```
[TRACEBACK #1] TypeError in tests/test_api.py:42
  Collapsed 6 frames from site-packages (use --expand to show)
  → app/handlers.py:88 in process_request
  → tests/test_api.py:42 in test_post_invalid_payload
  TypeError: expected str, got NoneType
```

### Options

| Flag | Description |
|------|-------------|
| `--input FILE` | Read from a file instead of stdin |
| `--expand` | Show all frames including third-party libraries |
| `--no-color` | Disable ANSI color output |
| `--only-errors` | Print only traceback blocks, suppress all other output |

---

## Contributing

Bug reports and pull requests are welcome. Please open an issue first to discuss any significant changes.

---

## License

[MIT](LICENSE)