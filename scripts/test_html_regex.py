import re

with open('amazon_response.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Test pattern
pattern = r'https://m\.media-amazon\.com/images/I/[^"\']+\.(jpg|png)'
matches = re.findall(pattern, html)

print(f"Found {len(matches)} matches")
if matches:
    for i, match in enumerate(matches[:5]):
        print(f"{i+1}. {match}")
