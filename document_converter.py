from docling.document_converter import DocumentConverter
import os

def convert_document_to_markdown(input_path, output_path, on_complete=None):
    """
    Converts a document to Markdown format using docling.
    
    Args:
        input_path (str): Path to the input document file
        output_path (str): Path where the Markdown output will be saved
        on_complete (callable, optional): Callback function that will be called when conversion is complete
                                         with output_path as an argument
        
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Convert the document
        converter = DocumentConverter()
        result = converter.convert(input_path)
        markdown_content = result.document.export_to_markdown()
        
        # Write the markdown content to the output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        print(f"Successfully converted {input_path} to {output_path}")
        
        # Call the on_complete callback if provided
        if on_complete:
            on_complete(output_path)
            
        return True
        
    except Exception as e:
        print(f"Error converting document: {str(e)}")
        return False


# Example usage
if __name__ == "__main__":
    # Example: convert a PDF file to Markdown
    input_file = "./storage/input/sample.pdf"
    output_file = "./storage/output/sample.md"
    
    if os.path.exists(input_file):
        convert_document_to_markdown(input_file, output_file)
    else:
        print(f"Input file {input_file} does not exist.")
