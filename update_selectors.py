#!/usr/bin/env python3
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


class SelectorUpdater:
    def __init__(self, results_file: str):
        self.results_file = Path(results_file)

    def load_raw_html(self, item_index: int = 0) -> Optional[str]:
        with open(self.results_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == item_index:
                    entry = json.loads(line.strip())
                    if entry.get("status") == "item" and "data" in entry:
                        return entry["data"].get("raw_html", "")
        return None

    def parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    def suggest_selectors(self, html: str) -> Dict[str, List[str]]:
        soup = self.parse_html(html)
        suggestions = {}

        suggestions["title"] = self._find_title_selectors(soup)
        suggestions["link"] = self._find_link_selectors(soup)
        suggestions["snippet"] = self._find_snippet_selectors(soup)
        suggestions["result_container"] = self._find_result_container(soup)

        return suggestions

    def _find_title_selectors(self, soup: BeautifulSoup) -> List[str]:
        selectors = []

        h2_tags = soup.find_all("h2")
        for tag in h2_tags:
            if tag.find("a"):
                selectors.append(f"h2 a span")
                break

        for tag in soup.find_all(["h1", "h2", "h3"]):
            if tag.find("a"):
                class_attr = tag.get("class", [])
                if class_attr:
                    selectors.append(f"{'.'.join(class_attr)} a span")
                break

        return selectors

    def _find_link_selectors(self, soup: BeautifulSoup) -> List[str]:
        selectors = []

        for tag in soup.find_all("a"):
            href = tag.get("href", "")
            if href and "http" in href:
                parent = tag.parent
                if parent:
                    class_attr = parent.get("class", [])
                    if class_attr:
                        selectors.append(f"{'.'.join(class_attr)} a")
                break

        for tag in soup.find_all(["a"], href=True):
            if tag.get("data-testid") == "result-title-a":
                selectors.append('a[data-testid="result-title-a"]')
                break

        for tag in soup.find_all("h2"):
            if tag.find("a"):
                class_attr = tag.get("class", [])
                if class_attr:
                    selectors.append(f"{'.'.join(class_attr)} a")
                break

        return selectors

    def _find_snippet_selectors(self, soup: BeautifulSoup) -> List[str]:
        selectors = []

        for tag in soup.find_all("div"):
            if tag.get("data-result") == "snippet":
                class_attr = tag.get("class", [])
                if class_attr:
                    selectors.append(f"{'.'.join(class_attr)} span")
                selectors.append(f"{'.'.join(class_attr)}")
                break

        for tag in soup.find_all("div", class_=True):
            classes = tag.get("class", [])
            if any("snippet" in c.lower() for c in classes):
                selectors.append(f"{'.'.join(classes)}")
                break

        return selectors

    def _find_result_container(self, soup: BeautifulSoup) -> List[str]:
        selectors = []

        root = soup.find("article")
        if root:
            class_attr = root.get("class", [])
            if class_attr:
                selectors.append(f"article.{'.'.join(class_attr)}")
            selectors.append(f'article[data-testid="result"]')
            selectors.append("article")

        for tag in soup.find_all(["div", "ol"], class_=True):
            classes = tag.get("class", [])
            if any("result" in c.lower() for c in classes):
                selectors.append(f"{'.'.join(classes)}")

        return selectors

    def update_config(self, config_file: str, selectors: Dict[str, str]):
        import yaml

        config_path = Path(config_file)
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        config["selectors"] = selectors

        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        print(f"Updated {config_file} with new selectors:")
        for key, value in selectors.items():
            print(f"  {key}: {value}")

    def display_suggestions(self, suggestions: Dict[str, List[str]]):
        print("\n" + "=" * 80)
        print("SUGGESTED SELECTORS")
        print("=" * 80 + "\n")

        for category, selector_list in suggestions.items():
            print(f"{category.upper()}:")
            for i, selector in enumerate(selector_list, 1):
                print(f"  {i}. {selector}")
            print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Update selectors based on raw HTML")
    parser.add_argument("--file", "-f", required=True, help="JSONL results file")
    parser.add_argument(
        "--item", "-i", type=int, default=0, help="Item index to inspect"
    )
    parser.add_argument(
        "--update", "-u", help="Update config file with suggested selectors"
    )

    args = parser.parse_args()

    updater = SelectorUpdater(args.file)

    html = updater.load_raw_html(args.item)
    if not html:
        print(f"Error: Could not load HTML for item {args.item}")
        return

    suggestions = updater.suggest_selectors(html)
    updater.display_suggestions(suggestions)

    if args.update:
        print(f"\nUpdating config file: {args.update}")

        print("\nSelect which selectors to use:")
        print("  1. Use first suggestion for each category")
        print("  2. Manually enter selectors")

        choice = input("\nChoice (1/2): ").strip()

        if choice == "1":
            new_selectors = {}
            for category, selector_list in suggestions.items():
                if selector_list:
                    new_selectors[category] = selector_list[0]
            updater.update_config(args.update, new_selectors)
        elif choice == "2":
            new_selectors = {}
            for category in suggestions.keys():
                selector = input(f"Enter selector for {category}: ").strip()
                if selector:
                    new_selectors[category] = selector
            updater.update_config(args.update, new_selectors)


if __name__ == "__main__":
    main()
