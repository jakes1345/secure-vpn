#!/usr/bin/env python3
"""
Create Professional PhazeVPN Logos
Modern, clean design with shield/lock/VPN tunnel theme
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_phazevpn_logo(size, output_path):
    """Create a professional PhazeVPN logo"""
    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Modern color scheme - purple/blue gradient
    primary_color = (102, 126, 234)  # #667eea - PhazeVPN purple
    secondary_color = (118, 75, 162)  # #764ba2 - Darker purple
    accent_color = (255, 255, 255)   # White
    
    # Draw shield shape (modern VPN icon style)
    center_x, center_y = size // 2, size // 2
    shield_width = int(size * 0.7)
    shield_height = int(size * 0.8)
    
    # Shield points
    shield_points = [
        (center_x, center_y - shield_height // 2),  # Top point
        (center_x - shield_width // 2, center_y - shield_height // 3),  # Top left
        (center_x - shield_width // 2, center_y + shield_height // 3),  # Bottom left
        (center_x - shield_width // 4, center_y + shield_height // 2),  # Bottom left curve
        (center_x, center_y + shield_height // 2),  # Bottom center
        (center_x + shield_width // 4, center_y + shield_height // 2),  # Bottom right curve
        (center_x + shield_width // 2, center_y + shield_height // 3),  # Bottom right
        (center_x + shield_width // 2, center_y - shield_height // 3),  # Top right
    ]
    
    # Draw shield with gradient effect
    draw.polygon(shield_points, fill=primary_color, outline=accent_color, width=max(2, size//32))
    
    # Draw lock in center (security symbol)
    lock_size = int(size * 0.25)
    lock_x = center_x
    lock_y = center_y + int(size * 0.05)
    
    # Lock body
    lock_body_width = int(lock_size * 0.6)
    lock_body_height = int(lock_size * 0.7)
    lock_body_x = lock_x - lock_body_width // 2
    lock_body_y = lock_y - lock_body_height // 2
    
    # Lock shackle (U shape)
    shackle_radius = int(lock_size * 0.25)
    shackle_center_y = lock_y - lock_body_height // 2 - shackle_radius
    
    # Draw shackle
    draw.arc(
        [lock_x - shackle_radius, shackle_center_y - shackle_radius,
         lock_x + shackle_radius, shackle_center_y + shackle_radius],
        start=0, end=180, fill=accent_color, width=max(3, size//20)
    )
    
    # Draw lock body
    draw.rectangle(
        [lock_body_x, lock_body_y,
         lock_body_x + lock_body_width, lock_body_y + lock_body_height],
        fill=accent_color, outline=accent_color, width=1
    )
    
    # Add keyhole
    keyhole_size = int(lock_size * 0.15)
    draw.ellipse(
        [lock_x - keyhole_size, lock_y - keyhole_size // 2,
         lock_x + keyhole_size, lock_y + keyhole_size // 2],
        fill=primary_color
    )
    
    # Add "P" letter overlay (subtle)
    if size >= 64:
        try:
            # Try to use a nice font
            font_size = int(size * 0.4)
            # Use default font, or try to load a better one
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Draw "P" in center
            text = "P"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = center_x - text_width // 2
            text_y = center_y - text_height // 2 - int(size * 0.1)
            
            # Draw text with outline for visibility
            draw.text((text_x - 1, text_y - 1), text, font=font, fill=(0, 0, 0, 128))
            draw.text((text_x + 1, text_y + 1), text, font=font, fill=(0, 0, 0, 128))
            draw.text((text_x, text_y), text, font=font, fill=accent_color)
        except:
            pass  # Skip text if font not available
    
    # Add subtle glow effect
    if size >= 128:
        # Draw outer glow
        glow_points = [
            (center_x, center_y - shield_height // 2 - size // 20),
            (center_x - shield_width // 2 - size // 40, center_y - shield_height // 3),
            (center_x - shield_width // 2 - size // 40, center_y + shield_height // 3),
            (center_x - shield_width // 4, center_y + shield_height // 2 + size // 20),
            (center_x, center_y + shield_height // 2 + size // 20),
            (center_x + shield_width // 4, center_y + shield_height // 2 + size // 20),
            (center_x + shield_width // 2 + size // 40, center_y + shield_height // 3),
            (center_x + shield_width // 2 + size // 40, center_y - shield_height // 3),
        ]
        # Subtle outer glow
        glow_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_img)
        glow_draw.polygon(glow_points, fill=(102, 126, 234, 30))
        # Composite with original
        img = Image.alpha_composite(img, glow_img)
    
    # Save
    img.save(output_path, 'PNG', optimize=True)
    print(f"✅ Created: {output_path} ({size}x{size})")

def main():
    """Generate all logo sizes"""
    output_dir = 'assets/icons'
    os.makedirs(output_dir, exist_ok=True)
    
    # Sizes to generate
    sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512]
    
    print("🎨 Creating professional PhazeVPN logos...")
    print("=" * 50)
    
    for size in sizes:
        output_path = os.path.join(output_dir, f'phazevpn-{size}x{size}.png')
        create_phazevpn_logo(size, output_path)
    
    # Also create generic names
    for size in [128, 256]:
        output_path = os.path.join(output_dir, f'phazevpn.png' if size == 128 else 'phazevpn-icon.png')
        create_phazevpn_logo(size, output_path)
    
    print("=" * 50)
    print("✅ All logos created!")
    print(f"📂 Location: {output_dir}/")
    print("\n💡 Your new professional logos are ready!")

if __name__ == '__main__':
    main()

