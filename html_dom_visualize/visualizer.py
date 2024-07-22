import requests
from bs4 import BeautifulSoup, Tag
import plotly.graph_objects as go
import plotly.io as pio
from collections import defaultdict
from typing import Callable, Optional


def html_dom_visualize(
    *,
    html: Optional[str] = None,
    url: Optional[str] = None,
    file_path: Optional[str] = None,
    branch_filter: Optional[Callable[[Tag], bool]] = None,
    should_mask: Optional[Callable[[Tag], bool]] = None,
    mask_fn: Optional[Callable[[Tag], str]] = None,
    output_path: Optional[str] = None,
    show: Optional[bool] = False
):
    """
    Visualize the DOM structure of an HTML document as a treemap.

    This function takes an HTML string, processes it according to specified
    filters and masking rules, and generates a treemap visualization of the
    resulting DOM structure.

    Parameters:
    -----------
    html : str
        The HTML content to visualize.

    url : Optional[str], default=None
        The URL of the HTML page (if applicable). Not used in the current
        implementation but could be used for reference or additional
        functionality.

    file_path : Optional[str], default=None
        The file path of the HTML file (if applicable). Not used in the
        current implementation but could be used for reference or additional
        functionality.

    branch_filter : Optional[Callable[[Tag], bool]], default=None
        A function that takes a BeautifulSoup Tag object and returns a boolean.
        If provided, only branches (and their descendants) for which this
        function returns True will be included in the visualization.

    should_mask : Optional[Callable[[Tag], bool]], default=None
        A function that takes a BeautifulSoup Tag object and returns a boolean.
        If provided, elements for which this function returns True will be
        masked in the output graph. Their children will be removed, and only
        their inner text (or the result of mask_fn) will be preserved.

    mask_fn : Optional[Callable[[Tag], str]], default=None
        A function that takes a BeautifulSoup Tag object and returns a string.
        This function is used to determine the text that should replace masked
        elements.
        If not provided, by default it would mask by the inner html of the
        element, except that it handles 'a' tags specially by including their
        'href' attribute.
    
    output_path : Optional[str], default=None
        The file path to save the visualization as an image. If not provided,
        the visualization will not be saved as an image.

    show : Optional[bool], default=False
        Whether to display the visualization in the browser. If True, the
        visualization will be displayed.

    Returns:
    --------
    None
    """

    if not html:
        if url:
            response = requests.get(url)
            response.raise_for_status()
            html = response.text
        elif file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                html = file.read()

    if not html:
        print("Error: No HTML provided")
        return

    soup = BeautifulSoup(html, "html.parser")

    if branch_filter is not None:
        _filter_branches(soup, branch_filter)

    if should_mask is not None:

        def default_mask_fn(node: Tag):
            if node.name == "a":
                return f"href: {node.get('href', 'N/A')}"
            return str(node)

        _mask_elements(soup, should_mask, mask_fn or default_mask_fn)

    figure = _plot_dom_treemap(soup)
    
    if output_path:
        pio.write_image(figure, output_path)

    if show:
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
