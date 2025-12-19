import os
from astropy.io import fits
from astropy.table import Table
from astropy.visualization import simple_norm
import matplotlib.pyplot as plt
from tabulate import tabulate

# ANSI color codes for cool alternating rows
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

# List of nice colormaps for astronomy images (standard + reversed)
cmaps = ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 
         'hot', 'afmhot', 'gray', 'gist_gray',
         'viridis_r', 'plasma_r', 'inferno_r', 'magma_r', 'cividis_r']

def print_colored_table(table, table_index):
    """Print a nicely formatted table with alternating cool colors."""
    rows = table.as_array().tolist()
    headers = table.colnames
    
    colored_headers = [f"{BOLD}{CYAN}{h}{RESET}" for h in headers]
    
    colored_rows = []
    for i, row in enumerate(rows):
        color = CYAN if i % 2 == 0 else BLUE
        colored_row = [f"{color}{str(cell)}{RESET}" for cell in row]
        colored_rows.append(colored_row)
    
    print(f"\n{BOLD}Table {table_index}:{RESET}")
    print(tabulate(colored_rows, headers=colored_headers, tablefmt="grid"))

# --- Set your single FITS file here ---
fits_filename = "MAST_2025-12-18T13_08_21.848Z/HST/o5i301020_asn.fits"  # Change if needed

try:
    with fits.open(fits_filename) as hdul:
        print(f"{BOLD}FITS file structure for {os.path.basename(fits_filename)}:{RESET}")
        hdul.info()
        print("\n" + "="*100 + "\n")
        
        table_count = 0
        image_count = 0
        
        for i, hdu in enumerate(hdul):
            print(f"{BOLD}Processing HDU {i} - {hdu.name} (type: {type(hdu).__name__}){RESET}")
            
            if hdu.data is None:
                print("  → No data array (likely Primary Header only)\n")
                continue
            
            # Shape and dtype info
            print(f"  Data shape: {hdu.data.shape}")
            print(f"  Data dtype: {hdu.data.dtype}\n")
            
            # ----------- If it's a TABLE (BinTableHDU or TableHDU) -----------
            if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                table_count += 1
                t = Table(hdu.data)
                
                # Pretty print in terminal
                print_colored_table(t, table_count)
                
                # Export to CSV
                base_name = os.path.splitext(fits_filename)[0]
                csv_name = f"{base_name}_table_{table_count}.csv"
                t.write(csv_name, format="csv", overwrite=True)
                print(f"  → Exported table to {csv_name}\n")
            
            # ----------- If it's IMAGE data (2D or more) -----------
            elif len(hdu.data.shape) >= 2:
                image_count += 1
                base_name = os.path.splitext(os.path.basename(fits_filename))[0]
                
                # Flatten to 2D if needed (e.g., for simple cubes)
                data2d = hdu.data
                if len(data2d.shape) > 2:
                    print(f"  → Multi-dimensional data ({data2d.shape}). Showing first slice.")
                    data2d = data2d[0]  # Take first plane
                
                # Use astropy normalization for better contrast
                norm = simple_norm(data2d, 'sqrt', percent=99.5)  # Good for astro images
                
                # Plot with several colormaps
                n_cmaps = len(cmaps)
                cols = 3
                rows = (n_cmaps + cols - 1) // cols
                fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 3.5*rows))
                fig.suptitle(f"HDU {i} - {hdu.name} from {os.path.basename(fits_filename)}", fontsize=16, fontweight='bold')
                
                if rows == 1:
                    axes = axes.reshape(1, -1)
                
                for ax, cmap in zip(axes.flat, cmaps):
                    ax.imshow(data2d, cmap=cmap, norm=norm, origin='lower')
                    ax.set_title(cmap, fontsize=12)
                    ax.axis('off')
                
                # Hide empty subplots
                for ax in axes.flat[n_cmaps:]:
                    ax.axis('off')
                
                plt.tight_layout()
                plt.show()
                
                # Optionally save one (e.g., viridis) as PNG
                save_fig, save_ax = plt.subplots(figsize=(8, 7))
                save_ax.imshow(data2d, cmap='viridis', norm=norm, origin='lower')
                save_ax.set_title(f"{base_name} - HDU {i} ({hdu.name}) - viridis")
                save_ax.axis('off')
                png_name = f"{base_name}_hdu{i}_image.png"
                save_fig.savefig(png_name, bbox_inches='tight', dpi=150)
                plt.close(save_fig)
                print(f"  → Saved example image as {png_name}\n")
            
            else:
                print("  → Data has unusual dimensions (not table or image) - skipping visualization\n")
        
        print(f"{BOLD}Summary:{RESET}")
        print(f"  Tables found: {table_count} (printed + exported to CSV)")
        print(f"  Images visualized: {image_count} (multiple colormaps each + one PNG saved)")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
