#!/usr/bin/env python3
"""
Create Simple, Clean PhazeVPN Logos
Minimalist design that works at all sizes
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_simple_logo(size, output_path):
    """Create a simple, clean PhazeVPN logo"""
    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Clean color scheme
    primary_color = (102, 126, 234)  # #667eea - PhazeVPN purple
    white = (255, 255, 255, 255)
    
    center_x, center_y = size // 2, size // 2
    
    # SIMPLE DESIGN: Just a clean "P" letter in a circle
    # This works at ALL sizes and is instantly recognizable
    
    # Draw circle background
    circle_radius = int(size * 0.4)
    circle_padding = int(size * 0.05)
    
    # Outer circle (border)
    draw.ellipse(
        [center_x - circle_radius - circle_padding, center_y - circle_radius - circle_padding,
         center_x + circle_radius + circle_padding, center_y + circle_radius + circle_padding],
        fill=primary_color,
        outline=None
    )
    
    # Inner circle (white background for letter)
    inner_radius = int(circle_radius * 0.85)
    draw.ellipse(
        [center_x - inner_radius, center_y - inner_radius,
         center_x + inner_radius, center_y + inner_radius],
        fill=white,
        outline=None
    )
    
    # Draw "P" letter - simple and bold
    if size >= 32:
        # For larger sizes, draw a clean "P"
        # P is made of a vertical line and a half-circle
        
        # Vertical line of P
        line_width = max(2, size // 16)
        line_height = int(size * 0.35)
        line_x = center_x - int(size * 0.15)
        line_top = center_y - line_height // 2
        line_bottom = center_y + line_height // 2
        
        draw.rectangle(
            [line_x, line_top, line_x + line_width, line_bottom],
            fill=primary_color
        )
        
        # Top horizontal line of P
        top_line_width = int(size * 0.25)
        draw.rectangle(
            [line_x, line_top, line_x + top_line_width, line_top + line_width],
            fill=primary_color
        )
        
        # Curved part of P (half circle)
        curve_radius = int(size * 0.12)
        curve_center_x = line_x + top_line_width // 2
        curve_center_y = line_top + line_height // 4
        
        # Draw arc for the P curve
        draw.arc(
            [curve_center_x - curve_radius, curve_center_y - curve_radius,
             curve_center_x + curve_radius, curve_center_y + curve_radius],
            start=0, end=180,
            fill=primary_color,
            width=line_width
        )
        
        # Fill the curve area
        draw.ellipse(
            [curve_center_x - curve_radius, curve_center_y - curve_radius,
             curve_center_x + curve_radius, curve_center_y + curve_radius],
            fill=primary_color
        )
        
        # Remove bottom half of curve circle to make it a half-circle
        draw.ellipse(
            [curve_center_x - curve_radius, curve_center_y,
             curve_center_x + curve_radius, curve_center_y + curve_radius * 2],
            fill=white
        )
    
    else:
        # For tiny sizes (16x16, 24x24), just draw a simple filled circle
        # The circle itself is the logo
        pass  # Circle is already drawn above
    
    # Save
    img.save(output_path, 'PNG', optimize=True)
    print(f"✅ Created: {output_path} ({size}x{size})")

def create_alternative_logo(size, output_path):
    """Alternative: Even simpler - just a shield shape"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    primary_color = (102, 126, 234)  # #667eea
    white = (255, 255, 255, 255)
    
    center_x, center_y = size // 2, size // 2
    
    # Simple shield - just 3 points: top point, two bottom corners
    shield_width = int(size * 0.6)
    shield_height = int(size * 0.7)
    
    shield_points = [
        (center_x, center_y - shield_height // 2),  # Top point
        (center_x - shield_width // 2, center_y - shield_height // 4),  # Top left
        (center_x - shield_width // 2, center_y + shield_height // 2),  # Bottom left
        (center_x, center_y + shield_height // 2),  # Bottom center
        (center_x + shield_width // 2, center_y + shield_height // 2),  # Bottom right
        (center_x + shield_width // 2, center_y - shield_height // 4),  # Top right
    ]
    
    # Draw shield
    draw.polygon(shield_points, fill=primary_color, outline=white, width=max(2, size//32))
    
    # Add simple checkmark for "secure" (only on larger sizes)
    if size >= 64:
        check_size = int(size * 0.2)
        check_x = center_x
        check_y = center_y + int(size * 0.1)
        
        # Simple checkmark
        draw.line(
            [check_x - check_size // 3, check_y,
             check_x - check_size // 6, check_y + check_size // 3,
             check_x + check_size // 3, check_y - check_size // 3],
            fill=white,
            width=max(2, size//20)
        )
    
    img.save(output_path, 'PNG', optimize=True)
    print(f"✅ Created (alt): {output_path} ({size}x{size})")

def main():
    """Generate all logo sizes"""
    output_dir = 'assets/icons'
    os.makedirs(output_dir, exist_ok=True)
    
    # Sizes to generate
    sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512]
    
    print("🎨 Creating SIMPLE, CLEAN PhazeVPN logos...")
    print("=" * 50)
    print("Design: Clean 'P' in a circle - works at ALL sizes")
    print("=" * 50)
    
    for size in sizes:
        output_path = os.path.join(output_dir, f'phazevpn-{size}x{size}.png')
        create_simple_logo(size, output_path)
    
    # Also create generic names
    create_simple_logo(128, os.path.join(output_dir, 'phazevpn.png'))
    create_simple_logo(256, os.path.join(output_dir, 'phazevpn-icon.png'))
    
    print("=" * 50)
    print("✅ All simple logos created!")
    print(f"📂 Location: {output_dir}/")
    print("\n💡 Clean, simple design that works everywhere!")

if __name__ == '__main__':
    main()

