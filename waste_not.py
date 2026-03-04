"""
Waste-Not: Circular Economy Tracker
===================================

This system supports SDG 12 (Responsible Consumption and Production) by:
- Optimizing waste segregation through set-based contaminant detection
- Reducing transportation emissions via greedy algorithm truck loading
- Enabling data-driven circular economy decision making
- Minimizing landfill waste through intelligent material tracking

Benefits:
- Reduces contamination in recycling streams
- Optimizes logistics for lower carbon footprint
- Identifies material recovery opportunities
- Supports circular economy principles

CSV Input Format (waste_input_data.csv):
- site_id          : Single letter identifier (A, B, C ...)
- site_name        : Human readable name (Site_A, Site_B ...)
- site_type        : Zone type (Urban Residential, Industrial Zone ...)
- materials        : Pipe-separated list (plastic_bottles|cardboard|glass ...)
- total_weight_kg  : Total weight as a number
- contamination_pct: Contamination percentage as a number (0-100)
"""

import csv
import matplotlib.pyplot as plt
from matplotlib_venn import venn3
import random
from typing import Dict, List, Set, Tuple


DEFAULT_CSV_FILE = 'waste_input_data.csv'


def load_data_from_csv(filepath: str = DEFAULT_CSV_FILE) -> Dict[str, Dict]:
    """
    Load waste collection data from a CSV file.

    Expected CSV columns:
        site_id          - Single letter ID (A, B, C ...)
        site_name        - Display name (Site_A, Site_B ...)
        site_type        - Zone description (Urban Residential ...)
        materials        - Pipe-separated material list (mat1|mat2|mat3)
        total_weight_kg  - Numeric total weight
        contamination_pct- Numeric contamination percentage

    Args:
        filepath: Path to the CSV input file (default: waste_input_data.csv)

    Returns:
        Dictionary containing site data with material sets, weights, and contamination

    Raises:
        FileNotFoundError: If the CSV file does not exist
        ValueError: If a required column is missing or a row has invalid data
    """
    import os

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"[ERROR] CSV file not found: '{filepath}'\n"
            f"   Please ensure '{DEFAULT_CSV_FILE}' exists in the current directory,\n"
            f"   or pass a custom path to load_data_from_csv(filepath='your_file.csv')"
        )

    required_columns = {'site_id', 'site_name', 'site_type', 'materials',
                        'total_weight_kg', 'contamination_pct'}

    sites = {}

    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        # Validate headers
        if reader.fieldnames is None:
            raise ValueError(f"[ERROR] CSV file '{filepath}' appears to be empty.")

        missing_cols = required_columns - set(reader.fieldnames)
        if missing_cols:
            raise ValueError(
                f"[ERROR] Missing required columns in CSV: {missing_cols}\n"
                f"   Found columns: {set(reader.fieldnames)}"
            )

        for row_num, row in enumerate(reader, start=2):  # start=2 (header is row 1)
            try:
                site_name = row['site_name'].strip()
                site_id   = row['site_id'].strip()
                site_type = row['site_type'].strip()

                # Parse pipe-separated materials into a set
                raw_materials = row['materials'].strip()
                if not raw_materials:
                    raise ValueError(f"Row {row_num}: 'materials' column is empty.")
                material_set = {m.strip() for m in raw_materials.split('|') if m.strip()}

                # Parse numeric fields
                try:
                    weight = float(row['total_weight_kg'].strip())
                except ValueError:
                    raise ValueError(
                        f"Row {row_num}: 'total_weight_kg' must be a number, "
                        f"got '{row['total_weight_kg']}'"
                    )

                try:
                    contamination = float(row['contamination_pct'].strip())
                except ValueError:
                    raise ValueError(
                        f"Row {row_num}: 'contamination_pct' must be a number, "
                        f"got '{row['contamination_pct']}'"
                    )

                sites[site_name] = {
                    'site_id':         site_id,
                    'site_type':       site_type,
                    'material_list':   material_set,
                    'total_weight_kg': weight,
                    'contamination_pct': contamination
                }

            except KeyError as e:
                raise ValueError(f"Row {row_num}: Missing expected column {e}")

    if not sites:
        raise ValueError(f"[ERROR] No data rows found in '{filepath}'. Please add site data.")

    return sites


def detect_common_contaminants(sites: Dict[str, Dict]) -> Set[str]:
    """
    Identify materials present in more than 80% of sites using set operations.
    
    Args:
        sites: Dictionary of site data
        
    Returns:
        Set of common contaminants
    """
    print("\n" + "="*50)
    print("CONTAMINANT IDENTIFICATION ANALYSIS")
    print("="*50)
    
    # Get all material sets
    material_sets = [site['material_list'] for site in sites.values()]
    
    # Find materials present in all sites
    common_to_all = set.intersection(*material_sets) if material_sets else set()
    
    # Find materials present in 80%+ of sites (dynamic threshold)
    threshold = max(1, int(len(sites) * 0.8))
    material_counts = {}
    for material in set().union(*material_sets):
        count = sum(1 for site_materials in material_sets if material in site_materials)
        material_counts[material] = count
    
    common_contaminants = {mat for mat, count in material_counts.items() if count >= threshold}
    
    print(f"Total sites analyzed: {len(sites)}")
    print(f"Materials present in ALL sites: {common_to_all}")
    print(f"Materials present in {threshold}+ sites (80%+): {common_contaminants}")
    
    # Detailed breakdown
    print("\nMaterial frequency analysis:")
    for material, count in sorted(material_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(sites)) * 100
        status = "[!] CONTAMINANT" if count >= threshold else "[OK] Normal"
        print(f"  {material}: {count}/{len(sites)} sites ({percentage:.1f}%) {status}")
    
    # Save to contaminant_report.txt
    with open('contaminant_report.txt', 'w', encoding='utf-8') as f:
        f.write("CONTAMINANT IDENTIFICATION REPORT\n")
        f.write("="*40 + "\n\n")
        f.write(f"Analysis Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Sites Analyzed: {len(sites)}\n")
        f.write(f"Threshold: >80% of sites ({threshold}+ sites)\n\n")
        
        f.write("COMMON CONTAMINANTS:\n")
        f.write("-" * 20 + "\n")
        for contaminant in sorted(common_contaminants):
            count = material_counts[contaminant]
            f.write(f"• {contaminant}: found in {count} sites ({(count/len(sites))*100:.1f}%)\n")
        
        f.write(f"\nMATERIALS IN ALL SITES:\n")
        f.write("-" * 25 + "\n")
        for material in sorted(common_to_all):
            f.write(f"• {material}\n")
        
        f.write(f"\nRECOMMENDATIONS:\n")
        f.write("-" * 15 + "\n")
        f.write("1. Implement targeted education for common contaminants\n")
        f.write("2. Set up separate collection bins for problematic materials\n")
        f.write("3. Consider site-specific sorting protocols\n")
    
    print(f"\n[OK] Contaminant report saved to: contaminant_report.txt")
    return common_contaminants


def find_unique_materials(sites: Dict[str, Dict]) -> Dict[str, Set[str]]:
    """
    Find unique materials between sites using set.difference().
    
    Args:
        sites: Dictionary of site data
        
    Returns:
        Dictionary of unique materials for each site comparison
    """
    print("\n" + "="*50)
    print("UNIQUE MATERIAL ANALYSIS")
    print("="*50)
    
    site_names = list(sites.keys())
    
    # Compare the first two sites if available
    if len(site_names) >= 2:
        first_name, second_name = site_names[0], site_names[1]
        site_a = sites[first_name]['material_list']
        site_b = sites[second_name]['material_list']
        
        unique_to_a = site_a - site_b
        unique_to_b = site_b - site_a
        common_to_both = site_a & site_b
        
        print(f"{first_name} materials: {len(site_a)} items")
        print(f"{second_name} materials: {len(site_b)} items")
        print(f"Common materials: {len(common_to_both)} items")
        
        print(f"\nMaterials unique to {first_name}: {unique_to_a}")
        print(f"Materials unique to {second_name}: {unique_to_b}")
        print(f"Materials common to both: {common_to_both}")
        
        print(f"\n[ANALYSIS]:")
        print(f"• {first_name} has {len(unique_to_a)} exclusive materials")
        print(f"• {second_name} has {len(unique_to_b)} exclusive materials")
        print(f"• {len(common_to_both)} materials are shared between both sites")
    
    # Calculate all unique materials for each site
    unique_materials = {}
    for site_name, site_data in sites.items():
        other_sites_materials = set()
        for other_name, other_data in sites.items():
            if other_name != site_name:
                other_sites_materials.update(other_data['material_list'])
        
        unique_materials[site_name] = site_data['material_list'] - other_sites_materials
    
    print(f"\nUnique materials by site:")
    for site_name, materials in unique_materials.items():
        if materials:
            print(f"• {site_name}: {materials}")
        else:
            print(f"• {site_name}: No unique materials")
    
    return unique_materials


def greedy_truck_loading(sites: Dict[str, Dict]) -> List[Dict]:
    """
    Implement greedy algorithm for optimal truck loading (Bin Packing).
    
    Args:
        sites: Dictionary of site data
        
    Returns:
        List of selected batches for loading
    """
    print("\n" + "="*50)
    print("GREEDY TRUCK LOADING ALGORITHM")
    print("="*50)
    
    TRUCK_CAPACITY = 1000  # kg
    
    # Create batches from all sites
    all_batches = []
    for site_name, site_data in sites.items():
        # Split each site's load into smaller batches for better packing
        num_batches = max(2, int(site_data['total_weight_kg']) // 200)
        batch_weight = site_data['total_weight_kg'] / num_batches
        
        for i in range(num_batches):
            all_batches.append({
                'site_id': site_data['site_id'],
                'batch_id': f"{site_data['site_id']}_batch_{i+1}",
                'weight_kg': round(batch_weight, 2),
                'contamination_pct': site_data['contamination_pct'],
                'priority_value': batch_weight * (1 - site_data['contamination_pct']/100)  # Greedy metric
            })
    
    # Sort by priority value (highest first) - Greedy approach
    all_batches.sort(key=lambda x: x['priority_value'], reverse=True)
    
    print(f"Truck capacity: {TRUCK_CAPACITY}kg")
    print(f"Total available batches: {len(all_batches)}")
    print(f"Total available weight: {sum(b['weight_kg'] for b in all_batches):.2f}kg")
    
    # Greedy selection
    selected_batches = []
    current_weight = 0
    
    print(f"\nLoading process (Greedy - highest priority first):")
    for i, batch in enumerate(all_batches):
        if current_weight + batch['weight_kg'] <= TRUCK_CAPACITY:
            selected_batches.append(batch)
            current_weight += batch['weight_kg']
            print(f"  Load {i+1}: {batch['batch_id']} ({batch['weight_kg']:.2f}kg) - "
                  f"Priority: {batch['priority_value']:.2f} | Total: {current_weight:.2f}kg")
        else:
            print(f"  Skip {batch['batch_id']}: {batch['weight_kg']:.2f}kg would exceed capacity")
    
    print(f"\n[OK] Loading complete!")
    print(f"  Batches loaded: {len(selected_batches)}/{len(all_batches)}")
    print(f"  Total weight: {current_weight:.2f}kg/{TRUCK_CAPACITY}kg ({(current_weight/TRUCK_CAPACITY)*100:.1f}% utilized)")
    print(f"  Remaining capacity: {TRUCK_CAPACITY - current_weight:.2f}kg")
    
    # Save to truck_loading_manifest.csv
    with open('truck_loading_manifest.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['batch_id', 'site_id', 'weight_kg', 'contamination_pct', 'priority_value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for batch in selected_batches:
            writer.writerow({
                'batch_id': batch['batch_id'],
                'site_id': batch['site_id'],
                'weight_kg': batch['weight_kg'],
                'contamination_pct': batch['contamination_pct'],
                'priority_value': round(batch['priority_value'], 2)
            })
    
    print(f"[OK] Truck loading manifest saved to: truck_loading_manifest.csv")
    return selected_batches


def generate_visualization(sites: Dict[str, Dict]) -> None:
    """
    Generate Venn diagram comparing up to three zones.
    
    Args:
        sites: Dictionary of site data
    """
    print("\n" + "="*50)
    print("VENN DIAGRAM VISUALIZATION")
    print("="*50)
    
    site_names = list(sites.keys())
    
    if len(site_names) < 3:
        print("[WARNING] Need at least 3 sites for Venn diagram. Skipping visualization.")
        return
    
    # Select the first three sites for comparison
    name_a, name_b, name_c = site_names[0], site_names[1], site_names[2]
    site_a = sites[name_a]['material_list']
    site_b = sites[name_b]['material_list']
    site_c = sites[name_c]['material_list']
    
    type_a = sites[name_a].get('site_type', name_a)
    type_b = sites[name_b].get('site_type', name_b)
    type_c = sites[name_c].get('site_type', name_c)
    
    print(f"Comparing material overlap between:")
    print(f"• {name_a} ({type_a}): {len(site_a)} materials")
    print(f"• {name_b} ({type_b}): {len(site_b)} materials")
    print(f"• {name_c} ({type_c}): {len(site_c)} materials")
    
    # Calculate overlap statistics
    ab_overlap = len(site_a & site_b)
    ac_overlap = len(site_a & site_c)
    bc_overlap = len(site_b & site_c)
    abc_overlap = len(site_a & site_b & site_c)
    
    print(f"\nOverlap Statistics:")
    print(f"  {name_a} & {name_b}: {ab_overlap} materials")
    print(f"  {name_a} & {name_c}: {ac_overlap} materials")
    print(f"  {name_b} & {name_c}: {bc_overlap} materials")
    print(f"  {name_a} & {name_b} & {name_c}: {abc_overlap} materials")
    
    # Create Venn diagram
    plt.figure(figsize=(12, 8))
    
    venn = venn3([site_a, site_b, site_c], 
                 set_labels=(f'{type_a}\n({name_a})', 
                            f'{type_b}\n({name_b})', 
                            f'{type_c}\n({name_c})'))
    
    # Customize appearance
    plt.title('Material Overlap Analysis\nWaste Collection Sites Comparison', 
              fontsize=16, fontweight='bold', pad=20)
    
    # Add subtitle with SDG reference
    plt.suptitle('Supporting SDG 12: Responsible Consumption and Production', 
                 fontsize=12, style='italic', y=0.02)
    
    # Save the plot
    plt.tight_layout()
    plt.savefig('waste_materials_venn_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()  # Close the figure instead of showing it (non-interactive backend)
    
    print(f"[OK] Venn diagram saved to: waste_materials_venn_diagram.png")
    
    # Additional analysis
    print(f"\nMaterial Flow Analysis:")
    all_materials = site_a | site_b | site_c
    print(f"• Total unique materials across 3 sites: {len(all_materials)}")
    print(f"• Materials in all 3 sites: {site_a & site_b & site_c}")
    
    # Site-specific insights
    print(f"\nSite-Specific Insights:")
    print(f"• {name_a} unique: {site_a - site_b - site_c}")
    print(f"• {name_b} unique: {site_b - site_a - site_c}")
    print(f"• {name_c} unique: {site_c - site_a - site_b}")


def main(csv_file: str = DEFAULT_CSV_FILE):
    """
    Main function to orchestrate the Waste-Not Circular Economy Tracker.

    Args:
        csv_file: Path to the input CSV file (default: waste_input_data.csv)
    """
    print("WASTE-NOT: CIRCULAR ECONOMY TRACKER")
    print("="*60)
    print("SDG 12 - Responsible Consumption and Production")
    print("Optimizing Waste Management Through Data Analytics")
    print("="*60)

    # Load data from CSV
    print(f"\nLoading waste collection data from: {csv_file}")
    try:
        sites = load_data_from_csv(csv_file)
    except (FileNotFoundError, ValueError) as e:
        print(e)
        return

    print(f"[OK] Loaded data for {len(sites)} collection sites:")
    for site_name, site_data in sites.items():
        site_type = site_data.get('site_type', 'Unknown')
        print(f"• {site_name} ({site_type}): {len(site_data['material_list'])} materials, "
              f"{site_data['total_weight_kg']}kg, {site_data['contamination_pct']}% contamination")
    
    # Execute all analyses
    common_contaminants = detect_common_contaminants(sites)
    unique_materials = find_unique_materials(sites)
    loaded_batches = greedy_truck_loading(sites)
    generate_visualization(sites)
    
    # Final summary
    print("\n" + "="*60)
    print("CIRCULAR ECONOMY IMPACT SUMMARY")
    print("="*60)
    print(f"• Contaminants identified: {len(common_contaminants)} common pollutants")
    print(f"• Unique material patterns: {sum(1 for mats in unique_materials.values() if mats)} sites with exclusives")
    print(f"• Transport optimization: {len(loaded_batches)} batches loaded efficiently")
    print(f"• Visualization: Material overlap analysis completed")
    
    print(f"\nOutput files generated:")
    print(f"  contaminant_report.txt - Contaminant analysis report")
    print(f"  truck_loading_manifest.csv - Optimized loading plan")
    print(f"  waste_materials_venn_diagram.png - Material overlap visualization")
    
    print(f"\nSDG 12 Contribution:")
    print(f"• Reduced waste contamination through data-driven segregation")
    print(f"• Optimized logistics lowering carbon emissions")
    print(f"• Enhanced material recovery for circular economy")
    print(f"• Evidence-based decision making for sustainable waste management")


if __name__ == "__main__":
    import sys
    # Optionally pass a custom CSV path as a command-line argument:
    # python waste_not.py my_custom_data.csv
    input_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV_FILE
    main(csv_file=input_file)
