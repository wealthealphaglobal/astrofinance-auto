#!/usr/bin/env python3
"""
Cleanup videos after YouTube upload
Manage disk space and organize files
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import shutil

VIDEOS_DIR = Path("videos")
YOUTUBE_SHORTS_DIR = VIDEOS_DIR / "youtube_shorts"
INSTA_REELS_DIR = VIDEOS_DIR / "instagram_reels"


def get_file_size(filepath):
    """Get file size in MB"""
    return os.path.getsize(filepath) / (1024 * 1024)


def get_file_age_hours(filepath):
    """Get file age in hours"""
    file_time = os.path.getmtime(filepath)
    current_time = datetime.now().timestamp()
    return (current_time - file_time) / 3600


def cleanup_youtube_shorts(older_than_hours=24, dry_run=False):
    """Delete YouTube Shorts videos older than N hours"""
    
    if not YOUTUBE_SHORTS_DIR.exists():
        print("⚠️ YouTube Shorts directory not found")
        return 0
    
    videos = list(YOUTUBE_SHORTS_DIR.glob("*.mp4"))
    
    if not videos:
        print("ℹ️ No YouTube Shorts videos found")
        return 0
    
    deleted_count = 0
    total_freed = 0
    
    print(f"📁 YouTube Shorts directory: {YOUTUBE_SHORTS_DIR}")
    print(f"📋 Found {len(videos)} video(s)")
    print()
    
    for video in sorted(videos):
        age_hours = get_file_age_hours(video)
        size_mb = get_file_size(video)
        
        if age_hours >= older_than_hours:
            status = "WILL DELETE" if dry_run else "DELETED"
            print(f"  {status}: {video.name}")
            print(f"    Age: {age_hours:.1f} hours | Size: {size_mb:.2f} MB")
            
            if not dry_run:
                try:
                    os.remove(video)
                    deleted_count += 1
                    total_freed += size_mb
                except Exception as e:
                    print(f"    ❌ Error: {e}")
        else:
            print(f"  KEEP: {video.name}")
            print(f"    Age: {age_hours:.1f} hours | Size: {size_mb:.2f} MB")
    
    print()
    if dry_run:
        print(f"🔍 Dry run: Would delete {deleted_count} file(s), freeing {total_freed:.2f} MB")
    else:
        print(f"✅ Deleted {deleted_count} file(s), freed {total_freed:.2f} MB")
    
    return deleted_count


def cleanup_instagram_reels(older_than_hours=168, dry_run=False):
    """Delete Instagram Reels older than N hours (default: 7 days)"""
    
    if not INSTA_REELS_DIR.exists():
        print("⚠️ Instagram Reels directory not found")
        return 0
    
    videos = list(INSTA_REELS_DIR.glob("*.mp4"))
    
    if not videos:
        print("ℹ️ No Instagram Reels videos found")
        return 0
    
    deleted_count = 0
    total_freed = 0
    
    print(f"📁 Instagram Reels directory: {INSTA_REELS_DIR}")
    print(f"📋 Found {len(videos)} video(s)")
    print()
    
    for video in sorted(videos):
        age_hours = get_file_age_hours(video)
        size_mb = get_file_size(video)
        
        if age_hours >= older_than_hours:
            status = "WILL DELETE" if dry_run else "DELETED"
            print(f"  {status}: {video.name}")
            print(f"    Age: {age_hours:.1f} hours | Size: {size_mb:.2f} MB")
            
            if not dry_run:
                try:
                    os.remove(video)
                    deleted_count += 1
                    total_freed += size_mb
                except Exception as e:
                    print(f"    ❌ Error: {e}")
        else:
            print(f"  KEEP: {video.name}")
            print(f"    Age: {age_hours:.1f} hours | Size: {size_mb:.2f} MB")
    
    print()
    if dry_run:
        print(f"🔍 Dry run: Would delete {deleted_count} file(s), freeing {total_freed:.2f} MB")
    else:
        print(f"✅ Deleted {deleted_count} file(s), freed {total_freed:.2f} MB")
    
    return deleted_count


def cleanup_temp_files(dry_run=False):
    """Delete temporary files"""
    
    temp_dir = Path("temp")
    
    if not temp_dir.exists():
        print("ℹ️ No temp directory found")
        return 0
    
    files = list(temp_dir.glob("*"))
    
    if not files:
        print("ℹ️ Temp directory is empty")
        return 0
    
    deleted_count = 0
    total_freed = 0
    
    print(f"📁 Temp directory: {temp_dir}")
    print(f"📋 Found {len(files)} file(s)")
    print()
    
    for file in files:
        size_mb = get_file_size(file) if file.is_file() else 0
        status = "WILL DELETE" if dry_run else "DELETED"
        print(f"  {status}: {file.name} ({size_mb:.2f} MB)")
        
        if not dry_run:
            try:
                if file.is_file():
                    os.remove(file)
                    deleted_count += 1
                    total_freed += size_mb
                elif file.is_dir():
                    shutil.rmtree(file)
                    deleted_count += 1
            except Exception as e:
                print(f"    ❌ Error: {e}")
    
    print()
    if dry_run:
        print(f"🔍 Dry run: Would delete {deleted_count} file(s), freeing {total_freed:.2f} MB")
    else:
        print(f"✅ Deleted {deleted_count} file(s), freed {total_freed:.2f} MB")
    
    return deleted_count


def show_disk_usage():
    """Show disk usage of video directories"""
    
    print("📊 DISK USAGE")
    print("="*60)
    print()
    
    total_size = 0
    
    # YouTube Shorts
    if YOUTUBE_SHORTS_DIR.exists():
        videos = list(YOUTUBE_SHORTS_DIR.glob("*.mp4"))
        size = sum(get_file_size(v) for v in videos)
        total_size += size
        print(f"📹 YouTube Shorts: {len(videos)} files, {size:.2f} MB")
        for video in sorted(videos)[:5]:
            print(f"   • {video.name} ({get_file_size(video):.2f} MB)")
        if len(videos) > 5:
            print(f"   ... and {len(videos) - 5} more")
    
    print()
    
    # Instagram Reels
    if INSTA_REELS_DIR.exists():
        videos = list(INSTA_REELS_DIR.glob("*.mp4"))
        size = sum(get_file_size(v) for v in videos)
        total_size += size
        print(f"📸 Instagram Reels: {len(videos)} files, {size:.2f} MB")
        for video in sorted(videos)[:5]:
            print(f"   • {video.name} ({get_file_size(video):.2f} MB)")
        if len(videos) > 5:
            print(f"   ... and {len(videos) - 5} more")
    
    print()
    
    # Temp
    if Path("temp").exists():
        files = list(Path("temp").glob("*"))
        size = sum(get_file_size(f) for f in files if f.is_file())
        total_size += size
        print(f"📦 Temp: {len(files)} files, {size:.2f} MB")
    
    print()
    print(f"💾 TOTAL: {total_size:.2f} MB")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup videos after upload",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup.py usage
  python cleanup.py youtube --dry-run
  python cleanup.py instagram --older-than 168
  python cleanup.py temp
  python cleanup.py all --dry-run
  python cleanup.py all  # Cleanup everything
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Usage
    subparsers.add_parser('usage', help='Show disk usage')
    
    # YouTube Shorts
    youtube_parser = subparsers.add_parser('youtube', help='Cleanup YouTube Shorts')
    youtube_parser.add_argument('--older-than', type=int, default=24, help='Age in hours (default: 24)')
    youtube_parser.add_argument('--dry-run', action='store_true', help='Preview what would be deleted')
    
    # Instagram Reels
    insta_parser = subparsers.add_parser('instagram', help='Cleanup Instagram Reels')
    insta_parser.add_argument('--older-than', type=int, default=168, help='Age in hours (default: 168 = 7 days)')
    insta_parser.add_argument('--dry-run', action='store_true', help='Preview what would be deleted')
    
    # Temp
    temp_parser = subparsers.add_parser('temp', help='Cleanup temp files')
    temp_parser.add_argument('--dry-run', action='store_true', help='Preview what would be deleted')
    
    # All
    all_parser = subparsers.add_parser('all', help='Cleanup all')
    all_parser.add_argument('--dry-run', action='store_true', help='Preview what would be deleted')
    all_parser.add_argument('--youtube-older', type=int, default=24, help='YouTube age in hours (default: 24)')
    all_parser.add_argument('--insta-older', type=int, default=168, help='Instagram age in hours (default: 168)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("="*60)
    print("🧹 AstroFinance Cleanup Manager")
    print("="*60)
    print()
    
    if args.command == 'usage':
        show_disk_usage()
    
    elif args.command == 'youtube':
        cleanup_youtube_shorts(args.older_than, args.dry_run)
    
    elif args.command == 'instagram':
        cleanup_instagram_reels(args.older_than, args.dry_run)
    
    elif args.command == 'temp':
        cleanup_temp_files(args.dry_run)
    
    elif args.command == 'all':
        cleanup_youtube_shorts(args.youtube_older, args.dry_run)
        print()
        cleanup_instagram_reels(args.insta_older, args.dry_run)
        print()
        cleanup_temp_files(args.dry_run)
    
    print()
    print("="*60)


if __name__ == "__main__":
    main()
