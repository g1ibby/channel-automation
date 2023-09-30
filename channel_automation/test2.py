import re

html = """..."""  # Your HTML content here

regex = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>\s*<h3>')

links = re.findall(regex, html)

print(links)
