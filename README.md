# html-dom-visualize
A simple HTML to Diagram library that outputs DOM tree as image for visualization. Supports custom elements filtering and masking.

Useful when analyzing elements composition of HTML documents or developing tools that manipulates HTML DOM structures.

## Using in Command line
```
pip install -r requirements.txt
# OR
python main.py -f ./webpage.html
```

```
options:
  -h, --help            show this help message and exit
  -u URL, --url URL     URL of the HTML page to analyze
  -f FILE, --file FILE  Path to local HTML file to analyze
  -b BRANCH, --branch BRANCH
                        Element tags that if included, their
                        ancestors and all their descendants
                        would be preserved. Multiple tags can
                        be specified If not specified, all
                        elements will be preserved.
  -m MASK, --mask MASK  Element tags that if included, they
                        will be masked from the output graph
                        such that their children will be
                        removed, and only the inner texts will
                        be preserved. Multiple tags can be
                        specified. If not specified, no tags
                        will be masked.

example:
python main.py -u https://google.com -b a -b button -m a

```