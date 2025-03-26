import os

def get_new_files_delta():
    """
    Returns a list of files that exist in ./storage/input but not in ./storage/output.
    
    Returns:
        list: List of filenames (without path) that need to be processed
    """
    input_dir = os.path.join("storage", "input")
    output_dir = os.path.join("storage", "output")
    
    # Ensure the directories exist
    if not os.path.exists(input_dir) or not os.path.exists(output_dir):
        return []
    
    # Get list of files in input directory with their full paths
    input_files = os.listdir(input_dir)
    
    # Get list of files in output directory with their full paths
    output_files = os.listdir(output_dir)
    
    # Extract filenames without extensions for comparison
    input_filenames = {os.path.splitext(file)[0] for file in input_files}
    output_filenames = {os.path.splitext(file)[0] for file in output_files}
    
    # Find files that are in input but their base name is not in output
    new_filenames = input_filenames - output_filenames
    
    # Get the original filenames (with extensions) for files that need processing
    new_files = [file for file in input_files if os.path.splitext(file)[0] in new_filenames]
    
    return list(new_files)


# Example usage
if __name__ == "__main__":
    new_files = get_new_files_delta()
    if new_files:
        print(f"Found {len(new_files)} new files to process:")
        for file in new_files:
            print(f"  - {file}")
    else:
        print("No new files to process.")
