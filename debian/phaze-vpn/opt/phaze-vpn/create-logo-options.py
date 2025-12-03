#!/usr/bin/env python3
"""
Create Multiple PhazeVPN Logo Style Options
Let user pick what they like
"""

from PIL import Image, ImageDraw
import os

def style1_geometric(size, output_path):
    """Style 1: Modern geometric - abstract VPN tunnel"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    color = (102, 126, 234)  # Purple
    center = size // 2
    
    # Abstract: Two overlapping circles creating a tunnel effect
    radius = int(size * 0.35)
    draw.ellipse([center - radius, center - radius, center + radius, center + radius],
                 fill=color, outline=None)
    draw.ellipse([center - radius//2, center - radius//2, center + radius//2, center + radius//2],
                 fill=(255, 255, 255, 255), outline=None)
    
    img.save(output_path, 'PNG')
    print(f"✅ Style 1: {output_path}")

def style2_gradient_circle(size, output_path):
    """Style 2: Gradient circle with accent"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Solid purple circle
    color = (102, 126, 234)
    center = size // 2
    radius = int(size * 0.4)
    
    draw.ellipse([center - radius, center - radius, center + radius, center + radius],
                 fill=color, outline=None)
    
    # Small white accent dot
    accent_size = int(size * 0.15)
    draw.ellipse([center - accent_size//2, center - accent_size//2 - radius//3,
                  center + accent_size//2, center + accent_size//2 - radius//3],
                 fill=(255, 255, 255, 255))
    
    img.save(output_path, 'PNG')
    print(f"✅ Style 2: {output_path}")

def style3_square_rounded(size, output_path):
    """Style 3: Rounded square with diagonal accent"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    color = (102, 126, 234)
    padding = int(size * 0.1)
    square_size = size - padding * 2
    
    # Rounded square
    draw.rounded_rectangle([padding, padding, size - padding, size - padding],
                          radius=int(size * 0.15), fill=color, outline=None)
    
    # Diagonal line accent
    if size >= 32:
        line_width = max(2, size // 16)
        draw.line([padding + square_size//4, padding + square_size//4,
                   size - padding - square_size//4, size - padding - square_size//4],
                  fill=(255, 255, 255, 255), width=line_width)
    
    img.save(output_path, 'PNG')
    print(f"✅ Style 3: {output_path}")

def style4_minimal_dot(size, output_path):
    """Style 4: Ultra minimal - just a dot with ring"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    color = (102, 126, 234)
    center = size // 2
    
    # Outer ring
    outer_radius = int(size * 0.4)
    inner_radius = int(size * 0.3)
    draw.ellipse([center - outer_radius, center - outer_radius,
                  center + outer_radius, center + outer_radius],
                 fill=None, outline=color, width=max(2, size//16))
    
    # Center dot
    dot_radius = int(size * 0.12)
    draw.ellipse([center - dot_radius, center - dot_radius,
                 center + dot_radius, center + dot_radius],
                fill=color, outline=None)
    
    img.save(output_path, 'PNG')
    print(f"✅ Style 4: {output_path}")

def style5_hexagon_simple(size, output_path):
    """Style 5: Simple hexagon (tech/VPN feel)"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    color = (102, 126, 234)
    center = size // 2
    radius = int(size * 0.4)
    
    # Hexagon points
    import math
    points = []
    for i in range(6):
        angle = math.pi / 3 * i - math.pi / 2
        x = center + radius * math.cos(angle)
        y = center + radius * math.sin(angle)
        points.append((x, y))
    
    draw.polygon(points, fill=color, outline=None)
    
    # Inner circle
    inner_radius = int(radius * 0.5)
    draw.ellipse([center - inner_radius, center - inner_radius,
                  center + inner_radius, center + inner_radius],
                 fill=(255, 255, 255, 255), outline=None)
    
    img.save(output_path, 'PNG')
    print(f"✅ Style 5: {output_path}")

def main():
    """Generate all style options"""
    output_dir = 'assets/icons'
    os.makedirs(output_dir, exist_ok=True)
    
    # Test size
    test_size = 256
    
    print("🎨 Creating 5 Different Logo Style Options...")
    print("=" * 60)
    
    style1_geometric(test_size, os.path.join(output_dir, 'style1-geometric.png'))
    style2_gradient_circle(test_size, os.path.join(output_dir, 'style2-gradient.png'))
    style3_square_rounded(test_size, os.path.join(output_dir, 'style3-square.png'))
    style4_minimal_dot(test_size, os.path.join(output_dir, 'style4-minimal.png'))
    style5_hexagon_simple(test_size, os.path.join(output_dir, 'style5-hexagon.png'))
    
    print("=" * 60)
    print("✅ Created 5 style options!")
    print("📂 Check assets/icons/ for:")
    print("   • style1-geometric.png - Abstract tunnel")
    print("   • style2-gradient.png - Circle with accent")
    print("   • style3-square.png - Rounded square")
    print("   • style4-minimal.png - Ultra minimal dot")
    print("   • style5-hexagon.png - Simple hexagon")
    print("\n💡 Tell me which style you like (1-5) and I'll generate all sizes!")

if __name__ == '__main__':
    main()

