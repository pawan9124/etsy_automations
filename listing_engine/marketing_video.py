import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# moviepy imports
from moviepy import ImageSequenceClip, AudioFileClip, concatenate_videoclips, VideoFileClip
import cv2

def add_text_to_frame(frame_img, text, alpha, font):
    """Helper to draw text on a PIL frame"""
    W, H = frame_img.size
    txt_overlay = Image.new('RGBA', frame_img.size, (255,255,255,0))
    d = ImageDraw.Draw(txt_overlay)
    
    bbox = d.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (W - text_w) // 2
    y = (H - text_h) // 2
    
    shadow_color = (0, 0, 0, alpha)
    text_color = (255, 255, 255, alpha)
    
    thickness = 4
    for offset_x in range(-thickness, thickness+1):
        for offset_y in range(-thickness, thickness+1):
            d.text((x + offset_x, y + offset_y), text, font=font, fill=shadow_color)
            
    d.text((x, y), text, font=font, fill=text_color)
    return Image.alpha_composite(frame_img.convert("RGBA"), txt_overlay)

def create_video_overlay_clip(video_path, text, fps=30):
    """Loads an existing video (like the spinning tumbler) and adds fading text over it"""
    print(f"Generating video clip for {Path(video_path).name} with text: '{text}'")
    clip = VideoFileClip(video_path)
    
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 70)
    except IOError:
        font = ImageFont.load_default()

    frames = []
    num_frames = int(clip.duration * fps)
    
    # Extract frames and add text
    for i, frame in enumerate(clip.iter_frames(fps=fps)):
        img = Image.fromarray(frame).convert("RGBA")
        # Fade in over 2 seconds
        alpha = int(min(255, (i / (fps * 2)) * 255))
        
        # Apply slight zoom (Ken burns effect on the video itself)
        progress = i / num_frames
        current_scale = 1.0 + (0.05 * progress) # 5% zoom over 5 seconds
        W, H = img.size
        new_w = int(W * current_scale)
        new_h = int(H * current_scale)
        
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - W) // 2
        top = (new_h - H) // 2
        img = resized.crop((left, top, left + W, top + H))
        
        # Add text
        img = add_text_to_frame(img, text, alpha, font)
        frames.append(np.array(img.convert("RGB")))
        
    return ImageSequenceClip(frames, fps=fps)

def create_ken_burns_clip(image_path, text, duration=5, fps=30, scale_start=1.0, scale_end=1.1):
    """Creates a zooming video clip from a static image with fading text."""
    print(f"Generating clip for {Path(image_path).name} with text: '{text}'")
    
    img = Image.open(image_path).convert("RGBA")
    W, H = img.size
    
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 70)
    except IOError:
        font = ImageFont.load_default()
        
    num_frames = duration * fps
    frames = []
    
    for i in range(num_frames):
        progress = i / num_frames
        current_scale = scale_start + (scale_end - scale_start) * progress
        
        new_w = int(W * current_scale)
        new_h = int(H * current_scale)
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        left = (new_w - W) // 2
        top = (new_h - H) // 2
        frame_img = resized.crop((left, top, left + W, top + H))
        
        alpha = int(min(255, (i / (fps * 2)) * 255))
        frame_img = add_text_to_frame(frame_img, text, alpha, font)
        
        frames.append(np.array(frame_img.convert("RGB")))
        
    return ImageSequenceClip(frames, fps=fps)

from listing_engine.video_generator import generate_rotating_video

def generate_marketing_video(bundle_dir, wrap_path, output_path):
    print("Starting Marketing Video Generation...")
    
    # 1. Rotating Video Clip
    # Generate the rotating video dynamically
    rotating_video_path = Path(bundle_dir) / "listing_images" / "temp_rotation.mp4"
    generate_rotating_video(wrap_path, str(rotating_video_path))
    
    clip1 = create_video_overlay_clip(str(rotating_video_path), "Premium Tumbler Wraps")
        
    # 2. Static Images
    img2 = Path(bundle_dir) / "listing_images" / "09_multi_tumbler.png"
    img3 = Path(bundle_dir) / "listing_images" / "05_lifestyle_mockup.png"
    
    clip2 = create_ken_burns_clip(img2, "15 High-Resolution Designs", duration=5)
    clip3 = create_ken_burns_clip(img3, "Upgrade Your Shop Today", duration=5)
    
    # Ensure they are all the same size before concatenation
    w, h = clip1.size
    clip2 = clip2.resized(new_size=(w, h))
    clip3 = clip3.resized(new_size=(w, h))
    
    final_clip = concatenate_videoclips([clip1, clip2, clip3], method="compose")
    
    # Add Audio
    mockup_dir = Path(__file__).parent.parent / "mockup_assets"
    audio_path = mockup_dir / "audio" / "marketing_track.mp3"
    if audio_path.exists():
        print("Adding background audio...")
        audio = AudioFileClip(str(audio_path))
        audio = audio.subclipped(0, final_clip.duration)
        final_clip = final_clip.with_audio(audio)
    
    print(f"Writing final video to {output_path}...")
    final_clip.write_videofile(
        str(output_path),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None 
    )
    
    # Cleanup temp video
    if rotating_video_path.exists():
        # wait a tiny bit to make sure moviepy released the file
        import time
        time.sleep(1)
        try:
            rotating_video_path.unlink()
        except:
            pass
            
    print("Marketing video generated successfully!")

if __name__ == "__main__":
    bundle_path = "output/IMPERIAL MOON COLLECTION"
    out_file = "output/marketing_presentation.mp4"
    wrap_file = list(Path(bundle_path).glob('straight_wraps/*.png'))[0]
    generate_marketing_video(bundle_path, str(wrap_file), out_file)
