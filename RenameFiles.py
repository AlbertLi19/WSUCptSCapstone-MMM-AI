
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import uuid
import re


def natural_sort_key(path):
    """
    Sort filenames naturally.

    Example:
    image_2.bmp comes before image_10.bmp.
    """

    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def select_folder():
    """Ask the user to select a folder."""

    root = tk.Tk()
    root.withdraw()

    folder_path = filedialog.askdirectory(
        title="Select Folder Containing Indentation Images"
    )

    if not folder_path:
        print("No folder selected.")
        root.destroy()
        return None, None

    return Path(folder_path), root


def rename_images(folder_path):
    """Rename all BMP files first, followed by TIF files."""

    # ---------------------------------
    # Step 1: Find all BMP images
    # ---------------------------------

    bmp_files = sorted(
        [
            file
            for file in folder_path.iterdir()
            if file.is_file()
            and file.suffix.lower() == ".bmp"
        ],
        key=natural_sort_key
    )

    # ---------------------------------
    # Step 2: Find all TIF images
    # ---------------------------------

    tif_files = sorted(
        [
            file
            for file in folder_path.iterdir()
            if file.is_file()
            and file.suffix.lower() == ".tif"
        ],
        key=natural_sort_key
    )

    # BMP files always come first.
    # TIF files continue the numbering.

    all_images = bmp_files + tif_files

    if not all_images:

        messagebox.showinfo(
            "No Images Found",
            "No BMP or TIF images were found "
            "in the selected folder."
        )

        return

    # ---------------------------------
    # Step 3: Generate new filenames
    # ---------------------------------

    rename_plan = []

    for index, original_path in enumerate(
        all_images,
        start=1
    ):

        extension = original_path.suffix.lower()

        new_name = f"indentation_{index}{extension}"

        new_path = folder_path / new_name

        rename_plan.append(
            (original_path, new_path)
        )

    # ---------------------------------
    # Step 4: Confirm the operation
    # ---------------------------------

    confirmed = messagebox.askyesno(
        "Confirm Renaming",
        f"Folder: {folder_path}\n\n"
        f"BMP images: {len(bmp_files)}\n"
        f"TIF images: {len(tif_files)}\n"
        f"Total images: {len(all_images)}\n\n"
        "The images will be renamed sequentially, "
        "with BMP files first and TIF files second.\n\n"
        "Do you want to continue?"
    )

    if not confirmed:

        print("Renaming cancelled.")
        return

    # ---------------------------------
    # Step 5: Check for filename conflicts
    # ---------------------------------

    original_paths = {
        path for path, _ in rename_plan
    }

    for original_path, new_path in rename_plan:

        # A target filename may already exist
        # if it belongs to an image being renamed.
        # Temporary names will handle that case.

        if (
            new_path.exists()
            and new_path not in original_paths
        ):

            messagebox.showerror(
                "Filename Conflict",
                f"Cannot rename images because "
                f"'{new_path.name}' already exists "
                "and is not part of the rename operation."
            )

            return

    # ---------------------------------
    # Step 6: Rename images temporarily
    # ---------------------------------

    # First rename all images to unique temporary
    # filenames to avoid overwriting other images.

    temporary_files = []

    try:

        for original_path, new_path in rename_plan:

            while True:

                temporary_name = (
                    f".indentation_temp_"
                    f"{uuid.uuid4().hex}.tmp"
                )

                temporary_path = (
                    folder_path / temporary_name
                )

                if not temporary_path.exists():
                    break

            original_path.rename(temporary_path)

            temporary_files.append(
                (original_path, temporary_path, new_path)
            )

        # ---------------------------------
        # Step 7: Apply the final filenames
        # ---------------------------------

        for original_path, temporary_path, new_path in (
            temporary_files
        ):

            temporary_path.rename(new_path)

            print(
                f"{original_path.name} "
                f"-> {new_path.name}"
            )

    except OSError as error:

        messagebox.showerror(
            "Renaming Error",
            "An error occurred while renaming images.\n\n"
            f"{error}\n\n"
            "Check the folder before running the "
            "program again. Some files may have "
            "already been renamed."
        )

        return

    # ---------------------------------
    # Step 8: Display the results
    # ---------------------------------

    messagebox.showinfo(
        "Renaming Complete",
        f"Successfully renamed {len(all_images)} images!\n\n"
        f"BMP files: {len(bmp_files)}\n"
        f"TIF files: {len(tif_files)}\n\n"
        f"Folder: {folder_path}"
    )

    print("\nRenaming complete.")


def main():

    folder_path, root = select_folder()

    if folder_path is None:
        return

    try:

        rename_images(folder_path)

    finally:

        root.destroy()


if __name__ == "__main__":
    main()