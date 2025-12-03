#!/usr/bin/env python3
"""
Remove watermark from logo (if needed)
Helps clean up AI-generated logos
"""

from PIL import Image, ImageDraw
import sys
import os

def remove_watermark(input_path, output_path=None):
    """Remove watermark from bottom-right corner"""
    if output_path is None:
        output_path = input_path.replace('.png', '_clean.png')
    
    img = Image.open(input_path)
    
    # Convert to RGBA if needed
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    width, height = img.size
    
    # Remove bottom-right corner (where watermarks usually are)
    # Remove last 10% of width and height
    crop_width = int(width * 0.1)
    crop_height = int(height * 0.1)
    
    # Create mask to fade out watermark area
    mask = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(mask)
    
    # Fade out bottom-right corner
    for y in range(height - crop_height, height):
        alpha = int(255 * (1 - (y - (height - crop_height)) / crop_height))
        draw.rectangle([width - crop_width, y, width, y + 1], fill=alpha)
    
    # Apply mask
    img.putalpha(mask)
    
    # Crop to remove watermark area completely (optional)
    # Uncomment if you want to crop instead of fade:
    # img = img.crop((0, 0, width - crop_width, height - crop_height))
    
    img.save(output_path, 'PNG')
    print(f"✅ Cleaned logo saved: {output_path}")
    return output_path

def make_transparent_background(input_path, output_path=None):
    """Make background transparent (if it's not already)"""
    if output_path is None:
        output_path = input_path.replace('.png', '_transparent.png')
    
    img = Image.open(input_path)
    
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # If background is dark/black, make it transparent
    data = img.getdata()
    new_data = []
    
    for item in data:
        # If pixel is very dark (background), make transparent
        if item[0] < 30 and item[1] < 30 and item[2] < 30:
            new_data.append((0, 0, 0, 0))  # Transparent
        else:
            new_data.append(item)
    
    img.putdata(new_data)
    img.save(output_path, 'PNG')
    print(f"✅ Transparent background saved: {output_path}")
    return output_path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 remove-watermark.py <logo.png> [options]")
        print("\nOptions:")
        print("  --remove-watermark  Remove watermark from bottom-right")
        print("  --transparent       Make dark background transparent")
        print("\nExample:")
        print("  python3 remove-watermark.py phazevpn-source.png --remove-watermark --transparent")
        return
    
    input_path = sys.argv[1]
    
    if not os.path.exists(input_path):
        print(f"❌ Error: {input_path} not found!")
        return
    
    output_path = input_path
    
    if '--remove-watermark' in sys.argv:
        output_path = remove_watermark(input_path)
        input_path = output_path  # Use cleaned version for next step
    
    if '--transparent' in sys.argv:
        make_transparent_background(input_path, output_path)
    
    print("\n✅ Logo cleaned! Now run:")
    print(f"   python3 resize-logos.py {output_path}")

if __name__ == '__main__':
    main()


