import cv2
from PIL import Image
import numpy as np
from pathlib import Path
from listing_engine.mockup import apply_displacement

def generate_rotating_video(wrap_path, output_video_path, frames_dir=None, N=150):
    """
    Generates a 360-degree rotating tumbler video using a lifestyle mockup background.
    """
    print(f"Generating 360 rotating video for {Path(wrap_path).name}...")
    
    mockup_dir = Path(__file__).parent.parent / "mockup_assets"
    base = Image.open(mockup_dir / 'tumblers_production/5_lifestyle_mockup/5_lifestyle_mockup.png').convert('RGBA')
    mask = Image.open(mockup_dir / 'tumblers_production/5_lifestyle_mockup/5_lifestyle_mockup_mask.png').convert('L').resize(base.size)
    disp = Image.open(mockup_dir / 'tumblers_production/5_lifestyle_mockup/5_lifestyle_mockup_displacment_map.png').convert('L').resize(base.size)
    glass = Image.open(mockup_dir / 'tumblers_production/5_lifestyle_mockup/5_lifestyle_mockup_glass_layer.png').convert('RGBA').resize(base.size)

    wrap = Image.open(wrap_path).convert('RGBA')
    W, H = wrap.size
    
    # Create double-width wrap for seamless scrolling
    double_wrap = Image.new('RGBA', (W * 2, H))
    double_wrap.paste(wrap, (0, 0))
    double_wrap.paste(wrap, (W, 0))

    if frames_dir is None:
        frames_dir = Path(output_video_path).parent / 'temp_frames'
    else:
        frames_dir = Path(frames_dir)
        
    frames_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    
    # Generate frames
    for i in range(N):
        offset = int((i / N) * W)
        shifted_wrap = double_wrap.crop((offset, 0, offset + W, H))
        result = apply_displacement(shifted_wrap, base, mask, disp, glass)
        
        # Save frame temporarily
        frame_path = frames_dir / f'frame_{i:03d}.png'
        result.save(frame_path)
        frames.append(frame_path)
        
        if (i+1) % 50 == 0 or i == 0:
            print(f'Generated rotation frame {i+1}/{N}')

    # Stitch into MP4
    if frames:
        first_frame = cv2.imread(str(frames[0]))
        h, w, _ = first_frame.shape
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_video_path), fourcc, 30.0, (w, h))
        
        for f in frames:
            img_pil = Image.open(f).convert('RGBA')
            frame_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGBA2BGR)
            out.write(frame_cv)
            
        out.release()
        print(f'Rotating video saved to {output_video_path}')
        
        # Cleanup temp frames
        for f in frames:
            f.unlink()
        frames_dir.rmdir()

    return output_video_path
