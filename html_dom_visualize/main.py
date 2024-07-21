import argparse
import sys
from html_dom_visualize.visualizer import html_dom_visualize


def main():
    parser = argparse.ArgumentParser(
        description="Analyze HTML from a URL or local file."
    )
    parser.add_argument("-u", "--url", help="URL of the HTML page to analyze")
    parser.add_argument(
        "-f", "--file", help="Path to local HTML file to analyze")
    parser.add_argument(
        "-b",
        "--branch",
        action="append",
        help="Element tags that if included, their ancestors and all their "
        "descendants would be preserved. Multiple tags can be specified "
        "If not specified, all elements will be preserved.",
    )
    parser.add_argument(
        "-m",
        "--mask",
        action="append",
        help="Element tags that if included, they will be masked from the "
        "output graph such that their children will be removed, and "
        "only the inner texts will be preserved. "
        "Multiple tags can be specified. "
        "If not specified, no tags will be masked.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path for the visualization. If not provided, the "
        "visualization will be displayed in the browser.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the visualization in the browser. If provided, the "
        "visualization will be displayed.",
    )

    args = parser.parse_args()

    if not (args.url or args.file):
        print("Error: Please provide either a URL or a file path.")
        parser.print_help()
        sys.exit(1)

    html_dom_visualize(
        url=args.url,
        file_path=args.file,
        branch_filter=(
            lambda node: node.name in args.branch) if args.branch else None,
        should_mask=(
            lambda node: node.name in args.mask) if args.mask else None,
        output_path=args.output,
        show=args.show
    )


if __name__ == "__main__":
    main()
