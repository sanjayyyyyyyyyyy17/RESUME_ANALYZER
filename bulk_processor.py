import os
import asyncio
import mimetypes
import argparse
import time
from main import process_resume_data

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.png', '.jpg', '.jpeg'}

async def process_directory(directory_path, delay=2):
    """
    Finds all resumes in a directory and processes them one by one.
    """
    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory.")
        return

    files = [
        f for f in os.listdir(directory_path) 
        if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
    ]
    
    total = len(files)
    print(f"Found {total} resumes to process.")
    
    for i, filename in enumerate(files, 1):
        file_path = os.path.join(directory_path, filename)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Fallback for docx which mimetypes sometimes misses
        if not mime_type:
            if filename.endswith('.docx'):
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            else:
                mime_type = "application/octet-stream"

        print(f"[{i}/{total}] Processing: {filename} ({mime_type})...")
        
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            
            # Using our refactored pipeline from main.py
            # Since we have no metadata, process_resume_data will extract identity from text
            sub_id, result = await process_resume_data(
                file_bytes=file_bytes,
                filename=filename,
                content_type=mime_type,
                student_metadata=None
            )
            
            print(f"  ✓ Success! Submission ID: {sub_id} | Score: {result.get('overall_score')}%")
            
        except Exception as e:
            print(f"  ✗ Failed: {filename} | Error: {str(e)}")
        
        # Rate limit management
        if i < total:
            print(f"  Waiting {delay}s for next file...")
            await asyncio.sleep(delay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk Resume Processor for AI Resume Platform")
    parser.add_argument("--path", required=True, help="Directory containing resumes")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between files (seconds) to manage rate limits")
    
    args = parser.parse_args()
    
    asyncio.run(process_directory(args.path, args.delay))
