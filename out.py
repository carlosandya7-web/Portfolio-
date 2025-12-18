import os
from astropy.io import fits
from astropy.table import Table
from astropy.visualization import simple_norm
import matplotlib.pyplot as plt
from tabulate import tabulate

# ANSI colors for cool alternating rows and bold text
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"

def print_colored_table(table, file_base, table_index):
    """Pretty print table with alternating cyan/blue rows."""
    rows = table.as_array().tolist()
    headers = table.colnames
    
    colored_headers = [f"{BOLD}{CYAN}{h}{RESET}" for h in headers]
    colored_rows = []
    for i, row in enumerate(rows):
        color = CYAN if i % 2 == 0 else BLUE
        colored_row = [f"{color}{str(cell)}{RESET}" for cell in row]
        colored_rows.append(colored_row)
    
    print(f"\n{BOLD}{GREEN}Table {table_index} (from {file_base}.fits){RESET}")
    print(tabulate(colored_rows, headers=colored_headers, tablefmt="grid"))

def save_image_preview(data, file_base, ext_index, ext_name):
    """Save a quick PNG preview of image data."""
    norm = simple_norm(data, 'sqrt', percent=99.5)  # Good stretch for astronomy images
    plt.figure(figsize=(8, 8))
    plt.imshow(data, cmap='gray', norm=norm, origin='lower')
    plt.title(f"Preview: {file_base}.fits [{ext_index}:{ext_name}]")
    plt.colorbar(label='Counts')
    plt.axis('off')
    
    png_name = f"{file_base}_ext{ext_index}_{ext_name}.png"
    plt.savefig(png_name, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"{YELLOW}   → Saved preview: {png_name}{RESET}")

# ------------------- CONFIGURATION -------------------
# Main directory containing your downloaded MAST data
base_dir = "MAST_2025-12-18T13_08_21.848Z/HST"

# Set to True if you have nested subfolders and want to process everything recursively
recursive = False  
# ----------------------------------------------------

print(f"{BOLD}Processing FITS files in: {base_dir}{RESET}\n")

if recursive:
    fits_files = []
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.endswith('.fits'):
                fits_files.append(os.path.join(root, f))
else:
    fits_files = [os.path.join(base_dir, f) for f in os.listdir(base_dir) if f.endswith('.fits')]

fits_files.sort()  # Nice alphabetical order

print(f"Found {len(fits_files)} FITS file(s):\n" + "\n".join([f"  • {os.path.basename(f)}" for f in fits_files]))
print("\n" + "="*100 + "\n")

for fits_path in fits_files:
    file_base = os.path.splitext(os.path.basename(fits_path))[0]
    print(f"{BOLD}{GREEN}Processing: {os.path.basename(fits_path)}{RESET}")
    
    try:
        with fits.open(fits_path) as hdul:
            print(f"{BOLD}FITS structure:{RESET}")
            hdul.info()
            print()
            
            table_count = 0
            for i, hdu in enumerate(hdul):
                # ----- Image data (PrimaryHDU or ImageHDU with 2D+ data) -----
                if hasattr(hdu, 'data') and hdu.data is not None and hdu.data.ndim >= 2:
                    print(f"{YELLOW}   Image extension {i}: {hdu.name} - shape {hdu.data.shape} - dtype {hdu.data.dtype}{RESET}")
                    print(f"      Stats: min={hdu.data.min():.2f}, max={hdu.data.max():.2f}, mean={hdu.data.mean():.2f}")
                    save_image_preview(hdu.data if hdu.data.ndim == 2 else hdu.data[0], file_base, i, hdu.name or f"IMG{i}")
                
                # ----- Table data (BinTableHDU or TableHDU) -----
                elif isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)) and hdu.data is not None:
                    table_count += 1
                    t = Table(hdu.data)
                    print_colored_table(t, file_base, table_count)
                    
                    # Export to CSV
                    csv_name = f"{file_base}_table_{table_count}.csv"
                    t.write(csv_name, format='csv', overwrite=True)
                    print(f"{YELLOW}   → Exported table to {csv_name}{RESET}")
            
            if table_count == 0:
                print("   No table extensions found in this file.")
            print("\n" + "-"*80 + "\n")
            
    except Exception as e:
        print(f"{BOLD}Error processing {fits_path}: {e}{RESET}\n")

print(f"{BOLD}{GREEN}All done! Check your folder for CSVs and PNG previews. 🫨{RESET}")
