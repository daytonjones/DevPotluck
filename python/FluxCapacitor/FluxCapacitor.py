#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import argparse
from rich import print
from rich.console import Console


class FluxToInfluxQLTranslator:
    def __init__(self):
        self.console = Console()

    def translate(self, flux_query, human=False):
        # Normalize the query
        flux_query = " ".join(flux_query.split())

        # Parse Flux components
        from_match = re.search(r'from\(bucket:\s*[\'"](.+?)[\'"]\)', flux_query, re.IGNORECASE)
        range_match = re.search(r'range\(start:\s*(.+?)\)', flux_query, re.IGNORECASE)
        filter_match = re.findall(r'filter\(fn:\s*\(r\)\s*=>\s*(.+?)\)', flux_query, re.IGNORECASE)
        agg_match = re.search(r'\|\>\s*(mean|count|sum|max|min)\(\)', flux_query, re.IGNORECASE)
        field_match = re.search(r'\|\>\s*filter\(fn:\s*\(r\)\s*=>\s*r\["_field"\]\s*==\s*[\'"](.+?)[\'"]\)', flux_query, re.IGNORECASE)
        group_match = re.search(r'group\(columns:\s*\[(.+?)\]\)', flux_query, re.IGNORECASE)
        limit_match = re.search(r'limit\(n:\s*(\d+)\)', flux_query, re.IGNORECASE)

        # Validate bucket extraction
        if not from_match:
            raise ValueError("[red]Invalid Flux query: Missing 'from()' clause[/red]")
        bucket = from_match.group(1).strip()
        print(f"[DEBUG] Extracted bucket: {bucket}")  # Debugging

        # Extract field name if available
        field = field_match.group(1).strip() if field_match else None
        print(f"[DEBUG] Extracted field: {field}")  # Debugging

        # Generate human-readable description
        if human:
            description = f"Uses the bucket '{bucket}' to pull data"
            if range_match:
                description += f" within the time range starting {range_match.group(1)}"
            if filter_match:
                conditions = " and ".join(
                    re.sub(r"r\\.", "", cond).replace("==", "equals") for cond in filter_match
                )
                description += f", filtered by {conditions}"
            if agg_match:
                description += f" and applies the aggregation '{agg_match.group(1).upper()}'"
            if group_match:
                group_columns = group_match.group(1).replace('"', "")
                description += f", grouped by {group_columns}"
            if limit_match:
                description += f", limiting results to {limit_match.group(1)} entries"
            description += "."
            self.console.print("[bold green]Human-Readable Description:[/bold green]")
            self.console.print(f"[yellow]{description}[/yellow]")

        # Build InfluxQL query
        influxql_query = ["SELECT"]
        if agg_match:
            influxql_query.append(f"{agg_match.group(1).upper()}({field})" if field else f"{agg_match.group(1).upper()}(*)")
        else:
            influxql_query.append("*")
        influxql_query.append(f"FROM {bucket}")  # Use extracted bucket name

        # Build WHERE clause
        where_clauses = []
        if range_match:
            where_clauses.append(f"time >= {range_match.group(1)}")
        if filter_match:
            for cond in filter_match:
                clean_cond = re.sub(r"r\\.", "", cond)
                where_clauses.append(clean_cond)
        if where_clauses:
            influxql_query.append(f"WHERE {' AND '.join(where_clauses)}")

        # Add GROUP BY and LIMIT
        if group_match:
            group_columns = group_match.group(1).replace('"', "")
            influxql_query.append(f"GROUP BY {group_columns}")
        if limit_match:
            influxql_query.append(f"LIMIT {limit_match.group(1)}")

        influxql_query_text = " ".join(influxql_query)
        self.console.print("[bold green]Translated InfluxQL Query:[/bold green]")
        self.console.print(f"[blue]{influxql_query_text}[/blue]")
        return influxql_query_text


class InfluxQLToFluxTranslator:
    def __init__(self):
        self.console = Console()

    def translate(self, influxql_query, human=False):
        # Normalize the query
        influxql_query = " ".join(influxql_query.split())

        # Parse InfluxQL components
        select_match = re.search(
            r"SELECT\s+(.+?)\s+FROM\s+([a-zA-Z0-9_]+)\s*(?:WHERE\s+(.+?))?(?:\s+GROUP BY\s+(.+?))?(?:\s+LIMIT\s+(\d+))?$",
            influxql_query,
            re.IGNORECASE | re.DOTALL,
        )

        if not select_match:
            raise ValueError("[red]Invalid InfluxQL query format[/red]")

        # Extract components
        select_fields, measurement, where_clause, group_by, limit = select_match.groups()
        measurement = measurement.strip()
        print(f"[DEBUG] Extracted measurement: {measurement}")

        if where_clause:
            where_clause = where_clause.strip()
            print(f"[DEBUG] Extracted WHERE clause: {where_clause}")
        else:
            print("[DEBUG] WHERE clause not found or is empty.")

        # Generate human-readable description
        if human:
            description = f"Queries the measurement '{measurement}'"
            if where_clause:
                description += f", filtered by {where_clause}"
            if select_fields:
                description += f", selecting fields '{select_fields}'"
            if group_by:
                description += f", grouped by {group_by}"
            if limit:
                description += f", limiting results to {limit} entries"
            description += "."
            self.console.print("[bold green]Human-Readable Description:[/bold green]")
            self.console.print(f"[yellow]{description}[/yellow]")

        # Build Flux query
        flux_query = [f'from(bucket: "{measurement}")']
        flux_query.append("|> range(start: -1h)")

        if where_clause:
            flux_query.append(self._translate_where(where_clause))

        if "MEAN(" in select_fields.upper():
            field = re.search(r"MEAN\((.+?)\)", select_fields, re.IGNORECASE).group(1)
            flux_query.append(f'|> filter(fn: (r) => r["_field"] == "{field.strip()}")\n|> mean()')
        else:
            flux_query.append(f'|> filter(fn: (r) => r["_field"] == "{select_fields.strip()}")')

        if group_by:
            flux_query.append(f'|> group(columns: [{self._translate_group_by(group_by)}])')

        if limit:
            flux_query.append(f'|> limit(n: {limit})')

        flux_query_text = "\n".join(flux_query)
        self.console.print("[bold green]Translated Flux Query:[/bold green]")
        self.console.print(f"[blue]{flux_query_text}[/blue]")
        return flux_query_text

    def _translate_where(self, where_clause):
        # Debugging: Check the initial WHERE clause
        print(f"[DEBUG] Raw WHERE clause: {where_clause}")

        # Refined regex to capture valid conditions
        condition_pattern = re.compile(
            r"([a-zA-Z0-9_\.]+)\s*(=|!=|<|>|<=|>=)\s*('[^']*'|\"[^\"]*\"|[a-zA-Z0-9_\.]+)"
        )
        conditions = condition_pattern.findall(where_clause)

        # Process each condition
        valid_conditions = []
        for condition in conditions:
            field, operator, value = condition
            valid_conditions.append(f"r.{field.strip()} {operator} {value.strip()}")

        # Debugging: Output the processed conditions
        print(f"[DEBUG] Processed WHERE conditions: {valid_conditions}")

        # Return the Flux filter string
        return f'|> filter(fn: (r) => {" and ".join(valid_conditions)})'

    def _translate_group_by(self, group_by):
        columns = [f'"{col.strip()}"' for col in group_by.split(",")]
        return ", ".join(columns)


def main():
    parser = argparse.ArgumentParser(
        description="Translate between InfluxQL and Flux queries with optional plain-English descriptions",
        add_help=False,  # Disable default -h/--help
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-t", "--type",
        choices=["influxql", "flux"],
        help="Type of the input query: 'influxql' or 'flux'",
    )
    parser.add_argument(
        "-q", "--query",
        help="The query to be translated. Wrap in quotes if it contains spaces.",
    )
    parser.add_argument(
        "--human",
        action="store_true",
        help="Output a plain-English description of the query",
    )
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show this help message and exit",
    )

    args = parser.parse_args()

    if args.help or not (args.type and args.query):
        print("[bold cyan]Usage Examples:[/bold cyan]")
        print("[green]Translate an InfluxQL query to Flux:[/green]")
        print("  ./FluxCapacitor.py -t influxql -q \"SELECT MEAN(temperature) FROM weather WHERE city = 'San Francisco'\"")
        print("\n[green]Translate a Flux query to InfluxQL:[/green]")
        print("  ./FluxCapacitor.py -t flux -q \"from(bucket: 'weather') |> range(start: -1h) |> filter(fn: (r) => r.city == 'San Francisco') |> mean()\"")
        print("\n[green]Get human-readable descriptions:[/green]")
        print("  ./FluxCapacitor.py -t influxql -q \"SELECT MAX(humidity) FROM weather\" --human")
        print("\n[green]Options:[/green]")
        print("  -t, --type    Type of the input query: 'influxql' or 'flux'")
        print("  -q, --query   The query to be translated. Wrap in quotes if it contains spaces.")
        print("  --human       Output a plain-English description of the query.")
        print("  -h, --help    Show this help message and exit.")
        exit(0)

    query_type = args.type
    query = args.query
    human = args.human

    if query_type == "influxql":
        translator = InfluxQLToFluxTranslator()
    else:
        translator = FluxToInfluxQLTranslator()

    try:
        translator.translate(query, human=human)
    except ValueError as e:
        print(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    main()

