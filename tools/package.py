import zipfile
import os

root = "C:/Users/yogen/.gemini/antigravity/scratch/lifecard"
out_zip = "C:/Users/yogen/.gemini/antigravity/scratch/lifecard.zip"
temp_zip = "C:/Users/yogen/.gemini/antigravity/scratch/lifecard_new.zip"

if os.path.exists(temp_zip):
    os.remove(temp_zip)

exclude_dirs = {'.git', '__pycache__', '.pytest_cache'}
exclude_files = {'cloudflared.exe', 'lifecard.db', 'lifecard.zip', 'lifecard_new.zip'}

with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as z:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for f in filenames:
            if f in exclude_files:
                continue
            full_path = os.path.join(dirpath, f)
            arcname = os.path.relpath(full_path, root)
            z.write(full_path, arcname)

if os.path.exists(out_zip):
    os.remove(out_zip)
os.rename(temp_zip, out_zip)
print("Clean package created at:", out_zip, "Size:", os.path.getsize(out_zip))
