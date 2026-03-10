import os
import glob
from bypy import ByPy

BACKUP_ROOT = "paper_output/backup"

def upload_latest_backup():
    # Find all backup directories
    backups = glob.glob(os.path.join(BACKUP_ROOT, "*"))
    
    if not backups:
        print("No backups found to upload.")
        return

    # Sort by creation time (latest last)
    latest_backup = max(backups, key=os.path.getctime)
    backup_name = os.path.basename(latest_backup)
    
    # Target remote directory as requested
    # Note: bypy usually uploads to /apps/bypy/ by default.
    # To upload to a specific root folder like /shit刊（无水印）, we need to navigate or specify path carefully.
    # However, standard bypy is restricted to /apps/bypy/ unless you use a custom app key with full access.
    # Assuming standard usage, we can create a subfolder inside /apps/bypy/shit刊（无水印）/
    
    # If the user has a custom app or if bypy supports full path (it depends on auth), let's try.
    # Usually `syncup` uploads to `/apps/bypy/<remote_path>`.
    # If the user wants it at the ROOT of Baidu Netdisk (outside /apps/bypy/), standard bypy cannot do that.
    # But based on the screenshot, "My Application Data" (我的应用数据) suggests /apps/bypy/ IS the root visible to the app.
    # So "shit刊（无水印）" should be a folder INSIDE /apps/bypy/.
    
    remote_dir = "shit刊（无水印）"
    remote_path = f"{remote_dir}/{backup_name}"
    
    print(f"Found latest backup: {latest_backup}")
    print(f"Starting upload to Baidu Netdisk...")
    print(f"Target path: /apps/bypy/{remote_path}")
    
    try:
        bp = ByPy()
        
        # Ensure remote directory exists
        # bp.mkdir(remote_dir) 
        
        # syncup(local_path, remote_path)
        bp.syncup(latest_backup, remote_path)
        
        print(f"\n[Success] Uploaded {backup_name} to Baidu Netdisk folder '{remote_dir}'.")
        
    except Exception as e:
        print(f"\n[Error] Upload failed: {e}")
        print("If this is your first time running, please run 'bypy info' in terminal to authenticate.")

if __name__ == "__main__":
    upload_latest_backup()
