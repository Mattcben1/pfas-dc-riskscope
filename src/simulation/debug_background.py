from pfas_background import load_background

def main():
    bg = load_background()
    print(f"Regions loaded: {len(bg)}")

    # Print some info for VA and US
    for region in ["VA", "US"]:
        chem_map = bg.get(region, {})
        print(f"\n=== {region} ===")
        print(f"Num chemicals: {len(chem_map)}")
        # Show first 10 chemicals + values
        for chem, val in list(chem_map.items())[:10]:
            print(f"  {chem}: {val} ppt")

if __name__ == "__main__":
    main()
