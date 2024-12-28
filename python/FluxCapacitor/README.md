# FluxCapacitor

**FluxCapacitor** is a Python-based query translation tool that helps users convert between InfluxQL and Flux query languages. It also provides human-readable descriptions of queries for better understanding. The tool leverages Python's `argparse` for command-line arguments and `rich` for colorful and enhanced terminal outputs.

---

## Features
- Translate **InfluxQL** queries into **Flux**.
- Translate **Flux** queries into **InfluxQL**.
- Generate **human-readable descriptions** of queries.
- Provide detailed examples and enhanced help messages.

---

## Requirements
- Python 3.7 or higher
- Dependencies:
  - `rich` (for enhanced terminal output)

Install dependencies using:
```bash
pip install rich
```

---

## Usage

### Command-Line Arguments
The script accepts the following arguments:

| Argument         | Description                                      |
|------------------|--------------------------------------------------|
| `-t`, `--type`   | Type of the input query: `influxql` or `flux`.   |
| `-q`, `--query`  | The query to be translated.                     |
| `--human`        | Generate a plain-English description of the query. |
| `-h`, `--help`   | Show the help message with examples.             |

### Examples

#### Translate an InfluxQL Query to Flux
```bash
./FluxCapacitor.py -t influxql -q "SELECT MEAN(temperature) FROM weather WHERE city = 'San Francisco'"
```
**Output:**
```plaintext
[DEBUG] Extracted measurement: weather
[DEBUG] Extracted WHERE clause: city = 'San Francisco'
Translated Flux Query:
from(bucket: "weather")
|> range(start: -1h)
|> filter(fn: (r) => r.city == 'San Francisco')
|> filter(fn: (r) => r["_field"] == "temperature")
|> mean()
```

#### Translate a Flux Query to InfluxQL
```bash
./FluxCapacitor.py -t flux -q "from(bucket: 'weather') |> range(start: -1h) |> filter(fn: (r) => r.city == 'San Francisco') |> mean()"
```
**Output:**
```plaintext
[DEBUG] Extracted bucket: weather
Translated InfluxQL Query:
SELECT MEAN(*) FROM weather WHERE r.city == 'San Francisco'
```

#### Generate a Human-Readable Description
```bash
./FluxCapacitor.py -t influxql -q "SELECT MAX(humidity) FROM weather" --human
```
**Output:**
```plaintext
Human-Readable Description:
Queries the measurement 'weather', selecting fields 'MAX(humidity)'.
```

---

## How It Works

The script contains two main classes:
- `FluxToInfluxQLTranslator`: Translates Flux queries to InfluxQL.
- `InfluxQLToFluxTranslator`: Translates InfluxQL queries to Flux.

### Key Features:
1. **Regex Parsing**: Extracts and processes query components like measurement, filters, and aggregations.
2. **Human-Readable Descriptions**: Generates plain-English summaries of the query logic.
3. **Debugging Output**: Provides debug messages for better transparency during translation.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

---

## Contribution
Feel free to open issues or submit pull requests to improve this tool.

---
