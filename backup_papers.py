import os
import shutil
import datetime

SOURCE_DIR = "paper_output"
ZONES = ["stone", "septic", "latrine"]

def backup_papers():
    # Generate timestamped directory name in Chinese format
    # Example: 2026年03月09日_22时15分30秒
    timestamp = datetime.datetime.now().strftime("%Y年%m月%d日_%H时%M分%S秒")
    
    # Target structure: paper_output/backup/<timestamp>
    backup_root = os.path.join(SOURCE_DIR, "backup")
    target_dir = os.path.join(backup_root, timestamp)
    
    print(f"Creating backup directory: {target_dir}")
    os.makedirs(target_dir, exist_ok=True)
    
    total_copied = 0
    
    for zone in ZONES:
        source_zone_path = os.path.join(SOURCE_DIR, zone)
        target_zone_path = os.path.join(target_dir, zone)
        
        if not os.path.exists(source_zone_path):
            print(f"Skipping {zone}: Directory not found.")
            continue
            
        print(f"Copying {zone}...")
        try:
            # shutil.copytree requires the destination directory to NOT exist
            shutil.copytree(source_zone_path, target_zone_path)
            
            # Count items
            count = len(os.listdir(target_zone_path))
            print(f"  - Copied {count} items from {zone}")
            total_copied += count
        except Exception as e:
            print(f"  - Error copying {zone}: {e}")

    print(f"\nBackup complete! Total items copied: {total_copied}")
    print(f"Location: {target_dir}")

if __name__ == "__main__":
    backup_papers()
