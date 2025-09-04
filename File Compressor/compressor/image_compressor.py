from PIL import Image

def compress_image(input_file, output_file,quality = 20):
    try:
        img = Image.open(input_file)

        # Convert to RGB for JPEG
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.save(output_file, "JPEG", optimize=True, quality=quality)
        print("✅ Image compressed:", output_file)
        return True
    except Exception as e:
        print("❌ Image compression failed:", e)
        return False