import re

# Load saved HTML
with open('amazon_response.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Test same code as scraper
image_pattern = r'https://m\.media-amazon\.com/images/I/[^"\']+\.(?:jpg|png)'
image_matches = re.findall(image_pattern, html)

print(f"Found {len(image_matches)} image matches")

if image_matches:
    # Get largest available image
    high_res_images = [img for img in image_matches if 'SL1000' in img or 'SL1500' in img]
    if high_res_images:
        image_url = high_res_images[0]
    else:
        base_img = image_matches[0]
        image_url = re.sub(r'_AC_[^.]+', '_AC_SL1000_', base_img)
    
    print(f"Final image URL: {image_url}")
