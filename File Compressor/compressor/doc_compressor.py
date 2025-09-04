
from PIL import Image
import io, os, zipfile, shutil

def compress_doc(input_file, output_file, quality=50):
    """
    Compresses images inside a .docx file by lowering their quality.
    Re-saves the document as a new .docx.
    """
    try:
        # Create a temp folder to extract docx (since it's a zip archive)
        temp_dir = input_file + "_temp"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        # Unzip docx
        with zipfile.ZipFile(input_file, 'r') as docx_zip:
            docx_zip.extractall(temp_dir)

        media_path = os.path.join(temp_dir, "word", "media")
        if os.path.exists(media_path):
            for img_name in os.listdir(media_path):
                img_path = os.path.join(media_path, img_name)
                try:
                    img = Image.open(img_path)

                    # Convert non-JPEGs to JPEG for better compression
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    # Save compressed image back
                    img.save(img_path, "JPEG", optimize=True, quality=quality)
                    print(f"Compressed: {img_name}")
                except Exception as e:
                    print(f"Skipping {img_name}: {e}")

        # Re-zip into new docx
        shutil.make_archive("compressed_docx", 'zip', temp_dir)
        if os.path.exists(output_file):
            os.remove(output_file)
        os.rename("compressed_docx.zip", output_file)

        # Cleanup temp
        shutil.rmtree(temp_dir)

        print(f"✅ DOCX compressed: {output_file}")
        return True
    except Exception as e:
        print("❌ DOCX compression failed:", e)
        return False
