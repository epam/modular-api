# Basic conversion
python "C:\Maestro3\m3-modular-admin\docs\docs_converter\src\convert_md_to_docx.py" "C:\Maestro3\m3-modular-admin\docs\docs_converter\examples\m3_setup_guide.md" -o output\m3_setup_guide.docx

# Without custom styles
python "C:\Maestro3\m3-modular-admin\docs\docs_converter\src\convert_md_to_docx.py" "C:\Maestro3\m3-modular-admin\docs\docs_converter\examples\m3_setup_guide.md" -o output\m3_setup_guide.docx --no-styles

# With verbose logging
python "C:\Maestro3\m3-modular-admin\docs\docs_converter\src\convert_md_to_docx.py" "C:\Maestro3\m3-modular-admin\docs\docs_converter\examples\m3_setup_guide.md" -o output\m3_setup_guide.docx --verbose

# Merge files externally (Windows)
type file1.md file2.md > merged.md
python convert_md_to_docx.py merged.md -o output.docx

# Merge files externally (Unix/Linux/Mac)
cat file1.md file2.md > merged.md
python convert_md_to_docx.py merged.md -o output.docx
