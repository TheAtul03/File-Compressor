import os
import shutil
import subprocess
import tempfile
import traceback
from PyPDF2 import PdfReader, PdfWriter

# pikepdf import is optional - we'll try/except it
try:
    import pikepdf
except Exception:
    pikepdf = None

def compress_pdf(input_file, output_file):
    """
    Robust PDF compression:
    - Uses pikepdf if available (best).
    - Falls back to Ghostscript (if installed).
    - Final fallback: rewrite with PyPDF2 to guarantee an output file.
    Returns True if a valid output_file was created, False otherwise.
    Debug info printed to console.
    """
    def _size(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0

    # Ensure output dir exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Work in a temp directory (avoids locks)
    tmp_dir = tempfile.mkdtemp(prefix="pdfcompress_")
    tmp_in = os.path.join(tmp_dir, "in.pdf")
    tmp_out = os.path.join(tmp_dir, "out.pdf")

    try:
        shutil.copy2(input_file, tmp_in)
    except Exception as e:
        print("[PDF] Failed to copy input to temp:", e)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return False

    in_size = _size(tmp_in)
    print(f"[PDF] input copied to temp, size={in_size} bytes")

    # --- Method 1: pikepdf (preferred) ---
    if pikepdf is not None:
        try:
            with pikepdf.open(tmp_in) as pdf:
                # aggressive but safe options
                pdf.save(
                    tmp_out,
                    compress_streams=True,
                    object_streams=True,
                    linearize=True
                )
            out_size = _size(tmp_out)
            print(f"[PDF][pikepdf] produced tmp_out size={out_size}")
            if out_size > 0:
                # keep the smaller file (tmp_out or original), copy to output_file
                chosen = tmp_out if out_size <= in_size else tmp_in
                shutil.copy2(chosen, output_file)
                print(f"[PDF][pikepdf] saved {output_file} (size={_size(output_file)})")
                shutil.rmtree(tmp_dir, ignore_errors=True)
                return True
            else:
                print("[PDF][pikepdf] tmp_out is empty; moving on")
        except pikepdf.PasswordError:
            print("[PDF][pikepdf] Password-protected PDF — cannot compress with pikepdf.")
            # don't try to open with ghostscript if encrypted, but we can still fallback
        except Exception:
            print("[PDF][pikepdf] Exception (traceback):")
            traceback.print_exc()

    else:
        print("[PDF] pikepdf not installed or failed to import; skipping pikepdf step.")

    # --- Method 2: Ghostscript (aggressive) ---
    gs_exe = None
    for cand in ("gswin64c", "gswin32c", "gs"):
        if shutil.which(cand):
            gs_exe = cand
            break

    if gs_exe:
        try:
            # Use /ebook or /screen presets depending on desired quality
            cmd = [
                gs_exe,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dPDFSETTINGS=/ebook",   # /screen (smaller), /ebook (medium), /printer (higher), /prepress (best)
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={tmp_out}",
                tmp_in
            ]
            print(f"[PDF][gs] Running Ghostscript: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            out_size = _size(tmp_out)
            print(f"[PDF][gs] produced tmp_out size={out_size}")
            if out_size > 0:
                chosen = tmp_out if out_size <= in_size else tmp_in
                shutil.copy2(chosen, output_file)
                print(f"[PDF][gs] saved {output_file} (size={_size(output_file)})")
                shutil.rmtree(tmp_dir, ignore_errors=True)
                return True
            else:
                print("[PDF][gs] Ghostscript produced empty output; moving on")
        except subprocess.CalledProcessError as e:
            print("[PDF][gs] Ghostscript returned non-zero exit:", e)
        except Exception:
            print("[PDF][gs] Exception (traceback):")
            traceback.print_exc()
    else:
        print("[PDF] Ghostscript not found in PATH; skipping Ghostscript step.")

    # --- Method 3: PyPDF2 rewrite (guarantee output) ---
    try:
        reader = PdfReader(tmp_in)
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)
        with open(tmp_out, "wb") as f:
            writer.write(f)
        out_size = _size(tmp_out)
        print(f"[PDF][PyPDF2] tmp_out size={out_size}")
        if out_size > 0:
            chosen = tmp_out if out_size <= in_size else tmp_in
            shutil.copy2(chosen, output_file)
            print(f"[PDF][PyPDF2] saved {output_file} (size={_size(output_file)})")
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return True
    except Exception:
        print("[PDF][PyPDF2] Exception (traceback):")
        traceback.print_exc()

    # nothing worked
    print("[PDF] All methods failed — no output produced.")
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return False
