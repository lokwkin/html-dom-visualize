import requests
import argparse
import sys
from bs4 import BeautifulSoup, Tag
import plotly.graph_objects as go
from collections import defaultdict
from typing import Callable, Optional


def html_dom_visualize(
    html: str,
    *,
    branch_filter: Optional[Callable[[Tag], bool]] = None,
    should_mask: Optional[Callable[[Tag], bool]] = None,
    mask_fn: Optional[Callable[[Tag], str]] = None,
):
    """
    Visualizes the DOM structure of the given HTML string.

    Args:
    html (str): The HTML string to visualize.

    This function parses the HTML and create a visual representation.
    """
    soup = BeautifulSoup(html, "html.parser")

    if branch_filter is not None:
        _filter_branches(soup, branch_filter)

    if should_mask is not None:

        def default_mask_fn(node: Tag):
            if node.name == "a":
                return f"href: {node.get("href", "N/A")}"
            return str(node)

        _mask_elements(soup, should_mask, mask_fn or default_mask_fn)

    figure = _plot_dom_treemap(soup)
    figure.show()


def _filter_branches(
    node: Tag,
    branch_filter: Optional[Callable[[Tag], bool]]
):
    """
    Filters the DOM tree based on the provided branch_filter function.

    Args:
    node (Tag): The root node of the DOM tree or subtree.
    branch_filter (Optional[Callable[[Tag], bool]]): A function that determines
    whether a node should be kept in the tree.

    Returns:
    bool: True if the node or any of its children should be kept, False
    otherwise.

    This function recursively traverses the DOM tree, applying the
    branch_filter to each node and removing nodes that don't meet the filter
    criteria.
    """
    if not branch_filter:
        return True

    # if it meets the filter, keep it no matter it is leaf node or not
    if branch_filter(node):
        return True

    children = list(node.children)
    # if it is leaf node and doesn't match the filter, remove it
    if len(children) == 0 and not branch_filter(node):
        return False

    should_keep = False
    for child in children:
        if isinstance(child, Tag):
            if _filter_branches(child, branch_filter):
                should_keep = True
            else:
                child.decompose()
        else:  # NavigableString or Comment
            pass

    return should_keep


def _mask_elements(
    node: Tag,
    should_mask: Optional[Callable[[Tag], bool]],
    mask_fn: Optional[Callable[[Tag], str]],
):
    """
    Masks specific elements in the DOM tree based on the provided criteria. If
    an element is determined to be masked, mask_fn() will be called and the
    resulting string will be added into `el-mask` attribute. All children of
    the element are removed.

    Args:
    node (Tag): The root node of the DOM tree or subtree.
    should_mask (Optional[Callable[[Tag], bool]]): A function that determines
    whether a node should be masked.
    mask_fn (Optional[Callable[[Tag], str]]): A function that provides the
    masking value for a node.

    This function traverses the DOM tree, applying the masking function to
    nodes that meet the masking criteria.
    """
    if should_mask(node) and mask_fn is not None:
        node.attrs["el-mask"] = mask_fn(node)
        for child in list(node.children):
            if isinstance(child, Tag):
                child.decompose()
        return

    for child in list(node.children):
        if isinstance(child, Tag):
            _mask_elements(child, should_mask, mask_fn)
        else:  # NavigableString or Comment
            pass


def _plot_dom_treemap(node: Tag):
    """
    Creates a treemap visualization of the DOM tree.

    Args:
    node (Tag): The root node of the DOM tree.

    Returns:
    Figure: A Plotly Figure object representing the DOM tree as a treemap.

    This function traverses the DOM tree and creates a treemap visualization
    using Plotly, showing the structure and relationships of the HTML elements.
    """

    def traverse(element: Tag, parent_id):
        node_id = f"{element.name}_{id(element)}"
        tree_data["ids"].append(node_id)
        tree_data["labels"].append(element.name)
        tree_data["parents"].append(parent_id)
        tree_data["hover_text"].append(_add_line_breaks(
            element.attrs["el-mask"]
            if "el-mask" in element.attrs
            else str(element.attrs))
        )
        for child in element.children:
            if child.name:
                traverse(child, node_id)

    tree_data = defaultdict(list)
    traverse(node, "")

    fig = go.Figure(
        go.Treemap(
            ids=tree_data["ids"],
            labels=tree_data["labels"],
            parents=tree_data["parents"],
            root_color="lightgrey",
            hovertext=tree_data["hover_text"],
            hoverinfo="text",
            branchvalues="total",
            maxdepth=15,
        )
    )

    fig.update_layout(title="DOM Visualization", width=1600, height=800)

    return fig


def _add_line_breaks(text, char_limit=120):
    result = []
    current_line = []
    current_length = 0

    for word in text.split():
        if current_length + len(word) > char_limit:
            result.append(' '.join(current_line) + '<br />')
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + 1  # +1 for the space

    if current_line:
        result.append(' '.join(current_line))

    return ' '.join(result)


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

    args = parser.parse_args()

    if not (args.url or args.file):
        print("Error: Please provide either a URL or a file path.")
        parser.print_help()
        sys.exit(1)

    content = None
    if args.url:
        response = requests.get(args.url)
        response.raise_for_status()
        content = response.text
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as file:
            content = file.read()

    if not content:
        print("Error: No content found.")

    html_dom_visualize(
        content,
        branch_filter=(
            lambda node: node.name in args.branch) if args.branch else None,
        should_mask=(
            lambda node: node.name in args.mask) if args.mask else None,
    )


if __name__ == "__main__":
    main()

