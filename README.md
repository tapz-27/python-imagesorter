# Python Image Sorter

A simple, powerful desktop application to organize your messy photo and video collections. It automatically sorts files into `YYYY-MM` folders based on their creation date (using EXIF metadata where possible).

## Features

- **Format Support**: Handles Images (`.jpg`, `.png`, `.heic`, `.webp`) and Videos (`.mp4`, `.mov`, `.avi`, `.mkv`).
- **Date Accuracy**: Prioritizes `DateTimeOriginal` from EXIF metadata. Falls back to file modification date if metadata is missing.
- **Safety First**:
    - Never overwrites files. Renames duplicates (e.g., `IMG_001_1.jpg`).
    - Skips files already in the destination.
    - Warns against recursive loops (Source inside Destination).
- **Video Support**: Sorts videos by file date.
- **Reporting**: Generates a detailed `sorting_report.txt` in the destination folder.
- **Compact UI**: Simple interface with a progress bar.

## Installation

### Running the Executable (Windows)
No installation required if you use the standalone executable.
1. Download `ImageSorter.exe` (from Releases or build it yourself).
2. Run it.

### Running from Source
1. Clone the repository:
   ```bash
   git clone https://github.com/StartCreating/python-imagesorter.git
   cd python-imagesorter
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python src/main.py
   ```

## Building the Executable

To build the standalone `.exe` yourself:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "ImageSorter" src/main.py
```

The executable will be created in the `dist/` folder.

## License

MIT License. See `LICENSE` file for details.
