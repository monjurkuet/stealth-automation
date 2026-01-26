#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import argparse


class ResultParser:
    def __init__(self, results_dir: str = "output/results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def get_latest_file(self, platform: str = None) -> Path:
        files = list(self.results_dir.glob("*.jsonl"))
        if platform:
            files = [f for f in files if f.name.startswith(platform)]

        if not files:
            raise FileNotFoundError(
                f"No JSONL files found for platform: {platform or 'all'}"
            )

        return max(files, key=lambda f: f.stat().st_mtime)

    def parse_file(self, filepath: Path) -> List[Dict[str, Any]]:
        results = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    results.append(entry)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line: {e}")
        return results

    def filter_by_status(self, results: List[Dict], status: str) -> List[Dict]:
        return [r for r in results if r.get("status") == status]

    def extract_items(self, results: List[Dict]) -> List[Dict]:
        items = []
        for result in results:
            if result.get("status") == "item" and "data" in result:
                items.append(result["data"])
        return items

    def get_summary(self, results: List[Dict]) -> Dict[str, Any]:
        summary = {
            "total_entries": len(results),
            "by_status": {},
            "platform": results[0].get("platform") if results else "unknown",
            "timestamp": results[0].get("timestamp") if results else "unknown",
            "items_count": 0,
            "errors_count": 0,
            "summaries_count": 0,
        }

        for result in results:
            status = result.get("status", "unknown")
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

            if status == "item":
                summary["items_count"] += 1
            elif status == "error":
                summary["errors_count"] += 1
            elif status == "summary":
                summary["summaries_count"] += 1

        return summary

    def display_items(self, items: List[Dict], show_raw_html: bool = False):
        print(f"\n{'=' * 80}")
        print(f"EXTRACTED ITEMS ({len(items)})")
        print(f"{'=' * 80}\n")

        for item in items:
            rank = item.get("rank", "N/A")
            title = item.get("title", "N/A")
            link = item.get("link", "N/A")
            details = item.get("details", "")

            print(f"Rank {rank}: {title}")
            print(f"  Link: {link}")
            if details:
                print(
                    f"  Details: {details[:150]}{'...' if len(details) > 150 else ''}"
                )

            if show_raw_html and "raw_html" in item:
                print(f"\n  Raw HTML (first 500 chars):")
                print(f"  {item['raw_html'][:500]}...")
                print()

            print()

    def display_summary(self, summary: Dict):
        print(f"\n{'=' * 80}")
        print(f"SUMMARY")
        print(f"{'=' * 80}")
        print(f"Platform: {summary['platform']}")
        print(f"Timestamp: {summary['timestamp']}")
        print(f"Total Entries: {summary['total_entries']}")
        print(f"\nBreakdown:")
        for status, count in summary["by_status"].items():
            print(f"  {status}: {count}")
        print(f"{'=' * 80}\n")

    def display_errors(self, results: List[Dict]):
        errors = [r for r in results if r.get("status") == "error"]
        if errors:
            print(f"\n{'=' * 80}")
            print(f"ERRORS ({len(errors)})")
            print(f"{'=' * 80}\n")

            for error in errors:
                print(f"Error: {error.get('error', {}).get('code', 'Unknown')}")
                print(f"Message: {error.get('error', {}).get('message', 'No message')}")
                if "query" in error.get("error", {}):
                    print(f"Query: {error['error']['query']}")
                print()

    def inspect_raw_html(self, filepath: Path, item_index: int = 0):
        results = self.parse_file(filepath)
        items = self.extract_items(results)

        if not items:
            print("No items found in results")
            return

        if item_index >= len(items):
            print(f"Item index {item_index} out of range (max: {len(items) - 1})")
            return

        item = items[item_index]
        print(f"\n{'=' * 80}")
        print(f"RAW HTML FOR ITEM {item_index + 1}")
        print(f"{'=' * 80}")
        print(f"Title: {item.get('title', 'N/A')}")
        print(f"Link: {item.get('link', 'N/A')}")
        print(f"\nRaw HTML:\n")
        print(item.get("raw_html", "No raw HTML available"))
        print(f"\n{'=' * 80}\n")

    def save_to_csv(self, results: List[Dict], output_file: str):
        import csv

        items = self.extract_items(results)

        if not items:
            print("No items to save")
            return

        fieldnames = ["rank", "title", "link", "details"]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)

        print(f"\nSaved {len(items)} items to {output_file}")

    def save_to_json(self, results: List[Dict], output_file: str):
        items = self.extract_items(results)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

        print(f"\nSaved {len(items)} items to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Parse and analyze Stealth Automation results"
    )
    parser.add_argument(
        "--platform", "-p", help="Platform name (e.g., duckduckgo)", default=None
    )
    parser.add_argument("--file", "-f", help="Specific JSONL file to parse")
    parser.add_argument(
        "--latest", "-l", action="store_true", help="Use latest file for platform"
    )
    parser.add_argument(
        "--items", "-i", action="store_true", help="Display extracted items"
    )
    parser.add_argument(
        "--show-html", action="store_true", help="Show raw HTML for items"
    )
    parser.add_argument("--summary", "-s", action="store_true", help="Display summary")
    parser.add_argument("--errors", "-e", action="store_true", help="Display errors")
    parser.add_argument(
        "--inspect",
        type=int,
        metavar="INDEX",
        help="Inspect raw HTML for specific item",
    )
    parser.add_argument("--csv", type=str, metavar="OUTPUT", help="Export items to CSV")
    parser.add_argument(
        "--json", type=str, metavar="OUTPUT", help="Export items to JSON"
    )

    args = parser.parse_args()

    result_parser = ResultParser()

    try:
        if args.file:
            filepath = Path(args.file)
            if not filepath.exists():
                print(f"Error: File not found: {args.file}")
                sys.exit(1)
        else:
            filepath = result_parser.get_latest_file(args.platform)
            print(f"Using file: {filepath}")

        results = result_parser.parse_file(filepath)

        if not results:
            print("No results found in file")
            sys.exit(0)

        if args.summary:
            summary = result_parser.get_summary(results)
            result_parser.display_summary(summary)

        if args.errors:
            result_parser.display_errors(results)

        if args.items or args.show_html:
            items = result_parser.extract_items(results)
            result_parser.display_items(items, show_raw_html=args.show_html)

        if args.inspect is not None:
            result_parser.inspect_raw_html(filepath, args.inspect)

        if args.csv:
            result_parser.save_to_csv(results, args.csv)

        if args.json:
            result_parser.save_to_json(results, args.json)

        if not any(
            [
                args.summary,
                args.errors,
                args.items,
                args.show_html,
                args.inspect,
                args.csv,
                args.json,
            ]
        ):
            summary = result_parser.get_summary(results)
            result_parser.display_summary(summary)
            items = result_parser.extract_items(results)
            if items:
                result_parser.display_items(items)
            if result_parser.filter_by_status(results, "error"):
                result_parser.display_errors(results)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
