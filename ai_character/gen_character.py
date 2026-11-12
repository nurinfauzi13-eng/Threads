"""Generate an AI character portrait on CPU with SD-Turbo (free, open model).
usage: python gen_character.py "prompt" out.png [seed]"""
import sys, time, torch
from diffusers import AutoPipelineForText2Image
prompt, out = sys.argv[1], sys.argv[2]
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
torch.set_num_threads(4)
pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sd-turbo", torch_dtype=torch.float32)
t = time.time()
img = pipe(prompt=prompt, num_inference_steps=2, guidance_scale=0.0, width=512, height=512,
           generator=torch.Generator().manual_seed(seed)).images[0]
img.save(out); print(f"saved {out} in {time.time()-t:.1f}s")
