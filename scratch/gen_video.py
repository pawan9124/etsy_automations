import cv2
from PIL import Image
import numpy as np
import sys
from pathlib import Path

# Add project root to path so we can import listing_engine
sys.path.append('D:\\Ai-Repos\\etsy_automations')
from listing_engine.mockup import apply_displacement

# Load assets for a lifestyle scene
base = Image.open('mockup_assets/tumblers_production/5_lifestyle_mockup/5_lifestyle_mockup.png').convert('RGBA')
mask = Image.open('mockup_assets/tumblers_production/5_lifestyle_mockup/5_lifestyle_mockup_mask.png').convert('L').resize(base.size)
disp = Image.open('mockup_assets/tumblers_production/5_lifestyle_mockup/5_lifestyle_mockup_displacment_map.png').convert('L').resize(base.size)
glass = Image.open('mockup_assets/tumblers_production/5_lifestyle_mockup/5_lifestyle_mockup_glass_layer.png').convert('RGBA').resize(base.size)

# Load first wrap
wrap_path = list(Path('output/IMPERIAL MOON COLLECTION/straight_wraps').glob('*.png'))[0]
wrap = Image.open(wrap_path).convert('RGBA')

W, H = wrap.size
double_wrap = Image.new('RGBA', (W * 2, H))
double_wrap.paste(wrap, (0, 0))
double_wrap.paste(wrap, (W, 0))

frames_dir = Path('scratch/video_frames')
frames_dir.mkdir(parents=True, exist_ok=True)

N = 150
for i in range(N):
    offset = int((i / N) * W)
    shifted_wrap = double_wrap.crop((offset, 0, offset + W, H))
    result = apply_displacement(shifted_wrap, base, mask, disp, glass)
    
    # Save frame
    result.save(frames_dir / f'frame_{i:03d}.png')
    if (i+1) % 10 == 0 or i == 0:
        print(f'Generated frame {i+1}/{N}')

# Stitch into MP4
frames = sorted(frames_dir.glob('*.png'))
if frames:
    first_frame = cv2.imread(str(frames[0]))
    h, w, _ = first_frame.shape
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('scratch/sample_rotation.mp4', fourcc, 30.0, (w, h))
    
    for f in frames:
        img_pil = Image.open(f).convert('RGBA')
        frame_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGBA2BGR)
        out.write(frame_cv)
        
    out.release()
    print('Video saved to scratch/sample_rotation.mp4')
