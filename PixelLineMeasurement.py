
import csv
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk


# Save Length.csv in the same folder as this Python program
CSV_FILE = Path(__file__).resolve().parent / "Length.csv"


def select_image():
    """Prompt the user to select an image."""

    return filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[
            ("Image Files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
            ("All Files", "*.*")
        ]
    )


def display_image(image_path):
    """Open and display the selected image."""

    image_window = tk.Toplevel()
    image_window.title(Path(image_path).name)

    # Load the image
    with Image.open(image_path) as image:
        image = image.convert("RGB")

    # Resize the DISPLAYED image if it is too large
    # The original image file is not modified
    image.thumbnail((1000, 700))

    photo = ImageTk.PhotoImage(image)

    image_label = tk.Label(
        image_window,
        image=photo
    )

    image_label.image = photo
    image_label.pack(padx=10, pady=10)

    image_window.update()

    return image_window


def image_already_exists(image_name):
    """Check whether the image already has an entry in Length.csv."""

    if not CSV_FILE.exists():
        return False

    with open(
        CSV_FILE,
        mode="r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None or "ImageName" not in reader.fieldnames:
            raise ValueError(
                "Length.csv must contain an ImageName column."
            )

        for row in reader:

            if row["ImageName"].casefold() == image_name.casefold():
                return True

    return False


def save_length(image_name, length):
    """Save the image name and length to Length.csv."""

    # Check for an existing entry
    if image_already_exists(image_name):

        messagebox.showinfo(
            "Duplicate Image",
            f"'{image_name}' already exists in Length.csv.\n\n"
            "No new entry was added."
        )

        return

    # Determine whether the CSV needs a header
    new_file = (
        not CSV_FILE.exists()
        or CSV_FILE.stat().st_size == 0
    )

    # Create the CSV if necessary and append the measurement
    with open(
        CSV_FILE,
        mode="a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if new_file:
            writer.writerow(["ImageName", "Length"])

        writer.writerow([image_name, length])

    messagebox.showinfo(
        "Saved",
        f"Measurement saved successfully!\n\n"
        f"Image: {image_name}\n"
        f"Length: {length}\n\n"
        f"File: {CSV_FILE}"
    )


def main():

    root = tk.Tk()
    root.withdraw()

    while True:

        # ---------------------------------
        # Step 1: Select an image
        # ---------------------------------

        image_path = select_image()

        if not image_path:

            keep_going = messagebox.askyesno(
                "Continue?",
                "No image was selected.\n\n"
                "Would you like to try again?"
            )

            if keep_going:
                continue

            break

        image_name = Path(image_path).name

        # ---------------------------------
        # Step 2: Open the image
        # ---------------------------------

        try:
            image_window = display_image(image_path)

        except Exception as error:

            messagebox.showerror(
                "Image Error",
                f"Unable to open image:\n{error}"
            )

            continue

        # ---------------------------------
        # Step 3: Ask user to enter a number
        # ---------------------------------

        length = simpledialog.askfloat(
            "Enter Length",
            f"Image: {image_name}\n\n"
            "Enter the length:",
            parent=image_window,
            minvalue=0.0
        )

        # ---------------------------------
        # Step 4: Save the result
        # ---------------------------------

        if length is not None:

            try:
                save_length(image_name, length)

            except (OSError, ValueError, csv.Error) as error:

                messagebox.showerror(
                    "CSV Error",
                    f"Unable to save measurement:\n{error}"
                )

        else:

            messagebox.showinfo(
                "Cancelled",
                "No length was entered.\n"
                "No measurement was saved."
            )

        # Close the current image
        image_window.destroy()

        # ---------------------------------
        # Step 5: Continue or stop
        # ---------------------------------

        keep_going = messagebox.askyesno(
            "Continue?",
            "Would you like to select another image?"
        )

        if not keep_going:
            break

    root.destroy()

    print("Program finished.")


if __name__ == "__main__":
    main()