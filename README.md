# html-dom-visualize
A simple HTML to Tree Diagram library that outputs HTML DOM as image for visualization. Supports custom elements filtering and masking.

Useful when analyzing elements composition of HTML documents or developing tools that manipulates HTML DOM structures.

## Install
```
pip install html-dom-visualize
```

## Using in Command line
```
```

```sh
options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path to local HTML file to analyze
  -u URL, --url URL     URL of the HTML page to analyze
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
# only include branches that contains <button> / <input>
# mask out children inside <button> and <a>
html-dom-visualize -f ./webpage.html -b button -b input -m a -m b 

# load from URL
html-dom-visualize -u https://google.com
```