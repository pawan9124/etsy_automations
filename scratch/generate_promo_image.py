import os
from PIL import Image, ImageDraw, ImageFont

def create_promo_image():
    # Load images
    before_path = r"D:\Ai-Repos\etsy_automations\output\demo_bundle\listing_images\demo_bundle (5)_1_11_straight.png"
    after_path = r"D:\Ai-Repos\etsy_automations\output\demo_bundle\listing_images\01_1_hero_single_wrap.png"
    
    img_before = Image.open(before_path).convert("RGBA")
    img_after = Image.open(after_path).convert("RGBA")
    
    # Target height
    target_height = 1000
    
    # Resize before image to target height
    aspect_b = img_before.width / img_before.height
    new_w_b = int(target_height * aspect_b)
    img_before = img_before.resize((new_w_b, target_height), Image.Resampling.LANCZOS)
    
    # Resize after image to target height
    aspect_a = img_after.width / img_after.height
    new_w_a = int(target_height * aspect_a)
    img_after = img_after.resize((new_w_a, target_height), Image.Resampling.LANCZOS)
    
    # Create canvas
    canvas_w = new_w_b + new_w_a + 150 # 150 padding
    canvas_h = target_height + 250 # 250 for top text padding
    
    canvas = Image.new("RGB", (canvas_w, canvas_h), "#18181b") # dark zinc background
    draw = ImageDraw.Draw(canvas)
    
    # Paste images
    canvas.paste(img_before, (50, 200), img_before)
    canvas.paste(img_after, (100 + new_w_b, 200), img_after)
    
    # Try to load a nice font, fallback to default
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 60)
        font_sub = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    
    # Draw text
    draw.text((canvas_w//2, 50), "STOP SCROLLING. SEE THE DIFFERENCE.", fill="#10b981", font=font_title, anchor="mm")
    draw.text((canvas_w//2, 120), "I built a free tool to automate Etsy mockups in 60 seconds.", fill="#a1a1aa", font=font_sub, anchor="mm")
    
    # Labels
    draw.rectangle([50, 150, 50 + 350, 210], fill="#ef4444")
    draw.text((50 + 175, 180), "BEFORE: Manual Canva", fill="#ffffff", font=font_sub, anchor="mm")
    
    draw.rectangle([100 + new_w_b, 150, 100 + new_w_b + 420, 210], fill="#10b981")
    draw.text((100 + new_w_b + 210, 180), "AFTER: 1-Click Automation", fill="#ffffff", font=font_sub, anchor="mm")
    
    # Save
    out_path = r"D:\Ai-Repos\etsy_automations\facebook_promo.jpg"
    canvas.save(out_path, "JPEG", quality=95)
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    create_promo_image()
