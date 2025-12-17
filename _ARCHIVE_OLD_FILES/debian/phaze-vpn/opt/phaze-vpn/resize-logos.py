#!/usr/bin/env python3
"""
Resize AI-Generated Logo to All Required Sizes
Takes your AI-generated logo and creates all sizes needed
"""

from PIL import Image
import sys
import os

def resize_logo(source_path, output_dir='assets/icons'):
    """Resize logo to all required sizes"""
    
    if not os.path.exists(source_path):
        print(f"❌ Error: {source_path} not found!")
        return False
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load source image
    try:
        img = Image.open(source_path)
        print(f"✅ Loaded: {source_path} ({img.size[0]}x{img.size[1]})")
    except Exception as e:
        print(f"❌ Error loading image: {e}")
        return False
    
    # Ensure it's RGBA (has transparency)
    if img.mode != 'RGBA':
        print("⚠️  Converting to RGBA (adding transparency)...")
        img = img.convert('RGBA')
    
    # Sizes to generate
    sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512]
    
    print("\n🎨 Resizing to all sizes...")
    print("=" * 50)
    
    for size in sizes:
        # Resize with high-quality resampling
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Save
        output_path = os.path.join(output_dir, f'phazevpn-{size}x{size}.png')
        resized.save(output_path, 'PNG', optimize=True)
        
        file_size = os.path.getsize(output_path) / 1024
        print(f"✅ {size:3d}x{size:3d} → {output_path} ({file_size:.1f} KB)")
    
    # Also create generic names
    img_128 = img.resize((128, 128), Image.Resampling.LANCZOS)
    img_128.save(os.path.join(output_dir, 'phazevpn.png'), 'PNG', optimize=True)
    print(f"✅ 128x128 → phazevpn.png")
    
    img_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    img_256.save(os.path.join(output_dir, 'phazevpn-icon.png'), 'PNG', optimize=True)
    print(f"✅ 256x256 → phazevpn-icon.png")
    
    print("=" * 50)
    print("✅ All sizes created!")
    print(f"📂 Location: {output_dir}/")
    print("\n💡 Your AI-generated logo is now ready to use!")
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 resize-logos.py <source-logo.png>")
        print("\nExample:")
        print("  python3 resize-logos.py my-ai-logo.png")
        print("  python3 resize-logos.py assets/icons/phazevpn-source.png")
        print("\nThis will create all sizes (16px to 512px) automatically.")
        return
    
    source_path = sys.argv[1]
    resize_logo(source_path)

if __name__ == '__main__':
    main()

