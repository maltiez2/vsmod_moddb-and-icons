import os
import sys
import subprocess
import numpy as np
from PIL import Image


def get_paths():
    base        = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(base, "scripts")
    output_dir  = os.path.join(base, "output")
    return {
        "base":               base,
        "scripts_dir":        scripts_dir,
        "output_dir":         output_dir,
        "moddb_psd":          os.path.join(base, "moddb.psd"),
        "modicon_psd":        os.path.join(base, "modicon.psd"),
        "jsx_list_folders":   os.path.join(scripts_dir, "list_folders.jsx"),
        "jsx_moddb_export":   os.path.join(scripts_dir, "moddb_export.jsx"),
        "jsx_modicon_export": os.path.join(scripts_dir, "modicon_export.jsx"),
        "folder_names_txt":   os.path.join(base, "_folder_names.txt"),
        "jsx_combined_temp":  os.path.join(base, "_combined_temp.jsx"),
    }


def find_photoshop():
    candidates = [
        r"C:\Program Files\Adobe\Adobe Photoshop 2026\Photoshop.exe",
        r"C:\Program Files (x86)\Adobe\Adobe Photoshop 2026\Photoshop.exe",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def run_photoshop_script(psd_file, jsx_file, js_vars=None, paths=None):
    """
    Run a JSX file in Photoshop via VBScript COM.
    js_vars: dict of variable names -> string values to inject before the JSX runs.
    Variables and JSX content are merged into a single temp file so they share scope.
    #target directive is stripped as it causes a fresh context when run via COM.
    Forward slashes are used in all paths passed to VBScript.
    """
    base     = paths["base"]
    vbs_file = os.path.join(base, "_run_ps_temp.vbs")

    psd_path_vbs = psd_file.replace("\\", "/")

    # Read main JSX, strip #target line which resets scope when run via COM
    with open(jsx_file, "r", encoding="utf-8") as f:
        jsx_content = f.read()

    jsx_content = "\n".join(
        line for line in jsx_content.splitlines()
        if not line.strip().startswith("#target")
    )

    # Prepend variables so they are in the same scope as the rest of the script
    if js_vars:
        var_lines = []
        for var_name, var_value in js_vars.items():
            escaped = var_value.replace("\\", "/").replace('"', '\\"')
            var_lines.append(f'var {var_name} = "{escaped}";')
        combined = "\n".join(var_lines) + "\n\n" + jsx_content
    else:
        combined = jsx_content

    # Write to temp file and run it
    combined_jsx  = paths["jsx_combined_temp"]
    combined_path = combined_jsx.replace("\\", "/")

    with open(combined_jsx, "w", encoding="utf-8") as f:
        f.write(combined)

    vbs_content = f"""Dim psApp
Set psApp = CreateObject("Photoshop.Application")
psApp.Visible = True

Dim doc
Set doc = psApp.Open("{psd_path_vbs}")

psApp.DoJavaScriptFile "{combined_path}"
"""

    try:
        with open(vbs_file, "w", encoding="utf-8") as f:
            f.write(vbs_content)

        result = subprocess.run(
            ["cscript", "//Nologo", vbs_file],
            capture_output=True,
            text=True
        )

        if result.stdout:
            print("[PS STDOUT]\n" + result.stdout)
        if result.stderr:
            print("[PS STDERR]\n" + result.stderr)

        if result.returncode != 0:
            print(f"[WARN] cscript exited with code {result.returncode}")

    finally:
        if os.path.isfile(vbs_file):
            os.remove(vbs_file)
        if os.path.isfile(combined_jsx):
            os.remove(combined_jsx)


def get_folder_names(paths):
    print("\n[INFO] Fetching folder list from moddb.psd...")

    run_photoshop_script(
        psd_file=paths["moddb_psd"],
        jsx_file=paths["jsx_list_folders"],
        paths=paths
    )

    txt = paths["folder_names_txt"]
    if not os.path.isfile(txt):
        print("[ERROR] _folder_names.txt was not created by Photoshop.")
        sys.exit(1)

    with open(txt, "r", encoding="utf-8") as f:
        names = [line.strip() for line in f if line.strip()]

    os.remove(txt)
    return names


def prompt_user(folder_names):
    print("\n=== Available folders in moddb.psd ===")
    for i, name in enumerate(folder_names):
        print(f"  [{i + 1}] {name}")
    print()

    while True:
        raw = input("Enter folder number to export: ").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(folder_names):
                selected = folder_names[idx]
                print(f"[INFO] Selected: {selected}")
                return selected
        print(f"[WARN] Please enter a number between 1 and {len(folder_names)}")


def run_moddb_export(selected_folder, paths):
    print(f"\n[INFO] Running moddb_export for folder: {selected_folder}")

    run_photoshop_script(
        psd_file=paths["moddb_psd"],
        jsx_file=paths["jsx_moddb_export"],
        js_vars={
            "SELECTED_FOLDER_NAME": selected_folder,
            "OUTPUT_FOLDER_PATH":   paths["output_dir"],
        },
        paths=paths
    )


def process_moddb_images(paths):
    output_dir = paths["output_dir"]
    scale_file = os.path.join(output_dir, "moddb-thumbnail.png")

    for crop_file in [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]:
        if crop_file == "moddb-thumbnail.png" or crop_file == "modicon.png":
            continue
        crop_file = os.path.join(output_dir, crop_file)
        # Crop image from 1920x1280 to 1920x1080
        if not os.path.isfile(crop_file):
            print(f"[WARN] {crop_file} not found, skipping crop.")
        else:
            print(f"\n[INFO] Cropping {crop_file}...")
            img         = Image.open(crop_file)
            top         = (1280 - 1080) // 2
            bottom      = top + 1080
            img_cropped = img.crop((0, top, 1920, bottom))
            img_cropped.save(crop_file)
            print(f"[INFO] Cropped to {img_cropped.size[0]}x{img_cropped.size[1]}")

    # Scale moddb-thumbnail from 1920x1280 to 480x320
    if not os.path.isfile(scale_file):
        print(f"[WARN] {scale_file} not found, skipping scale.")
    else:
        print(f"[INFO] Scaling {scale_file}...")
        img        = Image.open(scale_file)
        img_scaled = img.resize((480, 320), Image.LANCZOS)
        img_scaled.save(scale_file)
        print(f"[INFO] Scaled to {img_scaled.size[0]}x{img_scaled.size[1]}")


def run_modicon_export(selected_folder, paths):
    print(f"\n[INFO] Running modicon_export for folder: {selected_folder}")

    run_photoshop_script(
        psd_file=paths["modicon_psd"],
        jsx_file=paths["jsx_modicon_export"],
        js_vars={
            "TARGET_FOLDER_NAME": selected_folder,
            "OUTPUT_FOLDER_PATH": paths["output_dir"],
        },
        paths=paths
    )


def process_modicon(paths):
    image_path = os.path.join(paths["output_dir"], "modicon.png")

    if not os.path.isfile(image_path):
        print(f"[WARN] {image_path} not found, skipping transparent pixel processing.")
        return

    print(f"\n[INFO] Setting transparent pixels to black in: {image_path}")

    img  = Image.open(image_path).convert("RGBA")
    data = np.array(img, dtype=np.uint8)

    transparent_mask          = data[:, :, 3] == 0
    data[transparent_mask, 0] = 0  # R
    data[transparent_mask, 1] = 0  # G
    data[transparent_mask, 2] = 0  # B
    # alpha stays 0

    Image.fromarray(data, "RGBA").save(image_path)
    print(f"[INFO] Done: {image_path}")


def main():
    paths = get_paths()

    # Validate required files
    for label, path in [
        ("moddb.psd",                  paths["moddb_psd"]),
        ("modicon.psd",                paths["modicon_psd"]),
        ("scripts/list_folders.jsx",   paths["jsx_list_folders"]),
        ("scripts/moddb_export.jsx",   paths["jsx_moddb_export"]),
        ("scripts/modicon_export.jsx", paths["jsx_modicon_export"]),
    ]:
        if not os.path.isfile(path):
            print(f"[ERROR] Required file not found: {label} -> {path}")
            sys.exit(1)

    if not find_photoshop():
        print("[ERROR] Photoshop 2026 executable not found.")
        print("        Edit find_photoshop() with the correct path.")
        sys.exit(1)

    # Create output folder
    os.makedirs(paths["output_dir"], exist_ok=True)
    print(f"[INFO] Output folder: {paths['output_dir']}")

    # 1. Get available folders and prompt user
    folder_names    = get_folder_names(paths)
    selected_folder = prompt_user(folder_names)

    # 2. Export moddb images
    run_moddb_export(selected_folder, paths)

    # 3. Post-process moddb-logo and moddb-thumbnail
    process_moddb_images(paths)

    # 4. Export modicon using the same selected folder
    run_modicon_export(selected_folder, paths)

    # 5. Post-process modicon transparent pixels
    process_modicon(paths)

    print("\n[INFO] Finished")
    print(f"[INFO] Output files are in: {paths['output_dir']}")


if __name__ == "__main__":
    main()