import re, unicodedata

path = r"generate_pdf.py"
with open(path, encoding="utf-8") as f:
    text = f.read()

subs = {
    "—": "-", "–": "-", "×": "x", "²": "2",
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "•": "*", "°": " deg", "®": "(R)",
}
for k, v in subs.items():
    text = text.replace(k, v)

# catch any remaining non-latin-1
def safe(c):
    try:
        c.encode("latin-1")
        return c
    except UnicodeEncodeError:
        return "?"

text = "".join(safe(c) for c in text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("Done - all non-latin-1 chars replaced")
