

provincial_colors = {
    'Punjab': 'red',
    'Sindh': 'blue',
    'Balochistan': 'yellow',
    'Khyber-Pakhtunkhwa': 'orange',
    'Azad Kashmir': 'green',
    'Federally Administered Tribal Ar': 'brown',
    'Gilgit-Baltistan': 'brown',
    'Islamabad': 'green'
}

copernicus_lulc_flags = {
    '0': 'no_data',
    '10': 'cropland_rainfed',
    '11': 'cropland_rainfed_herbaceous_cover',
    '12': 'cropland_rainfed_tree_or_shrub_cover',
    '20': 'cropland_irrigated',
    '30': 'mosaic_cropland',
    '40': 'mosaic_natural_vegetation',
    '50': 'tree_broadleaved_evergreen_closed_to_open',
    '60': 'tree_broadleaved_deciduous_closed_to_open',
    '61': 'tree_broadleaved_deciduous_closed',
    '62': 'tree_broadleaved_deciduous_open',
    '70': 'tree_needleleaved_evergreen_closed_to_open',
    '71': 'tree_needleleaved_evergreen_closed',
    '72': 'tree_needleleaved_evergreen_open',
    '80': 'tree_needleleaved_deciduous_closed_to_open',
    '81': 'tree_needleleaved_deciduous_closed',
    '90': 'tree_needleleaved_deciduous_open',
    '82': 'tree_mixed',
    '100': 'mosaic_tree_and_shrub',
    '110': 'mosaic_herbaceous',
    '120': 'shrubland',
    '121': 'shrubland_evergreen',
    '122': 'shrubland_deciduous',
    '130': 'grassland',
    '140': 'lichens_and_mosses',
    '150': 'sparse_vegetation',
    '151': 'sparse_tree',
    '152': 'sparse_shrub',
    '153': 'sparse_herbaceous',
    '160': 'tree_cover_flooded_fresh_or_brakish_water',
    '170': 'tree_cover_flooded_saline_water',
    '180': 'shrub_or_herbaceous_cover_flooded',
    '190': 'urban',
    '200': 'bare_areas',
    '201': 'bare_areas_consolidated',
    '202': 'bare_areas_unconsolidated',
    '210': 'water',
    '220': 'snow_and_ice'
}

newworld_political_map = {
    "NATO": [
        # Current NATO member countries
        # Source: NATO website
        "Albania", "Belgium", "Bulgaria", "Canada", "Croatia", "Czechia",
        "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", 
        "Hungary", "Iceland", "Italy", "Latvia", "Lithuania", "Luxembourg",
        "Montenegro", "Netherlands", "North Macedonia", "Norway", "Poland",
        "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden",
        "Türkiye", "United Kingdom", "United States of America", "Australia",
        "Japan", "South Korea", "New Zealand"
    ],
    "BRICS": [
        # Full BRICS members + partner states (2025)
        # Based on BRICS documents / expansion as of Jan 2025
        "Brazil", "Russia", "India", "China", "South Africa",
        "Egypt", "Ethiopia", "Iran", "United Arab Emirates", "Saudi Arabia",
        "Indonesia",  # full member (2025)
        # Partner countries as of 1 Jan 2025 (not full but relevant)
        "Belarus", "Bolivia", "Cuba", "Kazakhstan", "Malaysia", "Thailand", "Uganda", "Uzbekistan", "Nigeria"
    ],
    "NonAligned": [
        # Based on current NAM membership :contentReference[oaicite:4]{index=4}
        "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cameroon",
        "Cape Verde", "Central African Republic", "Chad", "Comoros", "Congo (Brazzaville)",
        "Congo, Democratic Republic of", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea",
        "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Ivory Coast",
        "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania",
        "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda",
        "São Tomé and Príncipe", "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Sudan",
        "South Africa", "Sudan", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe",
        "Afghanistan", "Bahrain", "Bangladesh", "Belarus", "Bhutan", "Brunei", "Burma (Myanmar)",
        "Cambodia", "Cyprus", "Fiji", "India", "Indonesia", "Iran", "Iraq", "Jamaica", "Jordan",
        "Kuwait", "Laos", "Lebanon", "Malaysia", "Maldives", "Nepal", "Oman", "Pakistan", "Palestine",
        "Papua New Guinea", "Qatar", "Syria", "Tajikistan", "Timor-Leste", "Turkmenistan",
        "United Arab Emirates", "Uzbekistan", "Yemen", "Vietnam", "Vanuatu"
        # … etc. (you’d want to complete this list fully)
    ],
    # "Global South": [
    #     # A broad “Global South” list — from SocSES source
    #     "Afghanistan", "Algeria", "Angola", "Argentina", "Armenia", "Azerbaijan",
    #     "Bangladesh", "Belize", "Benin", "Bolivia", "Botswana", "Brazil",
    #     "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Chad", "Chile",
    #     "Colombia", "Comoros", "Congo", "Costa Rica", "Côte d'Ivoire", "Djibouti",
    #     "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador",
    #     "Equatorial Guinea", "Eritrea", "Ethiopia", "Fiji", "Gabon", "Gambia",
    #     "Georgia", "Ghana", "Guinea", "Guinea-Bissau", "Guyana", "Haiti",
    #     "Honduras", "India", "Indonesia", "Iran", "Iraq", "Jordan",
    #     "Kazakhstan", "Kenya", "Kiribati", "Kyrgyzstan", "Laos", "Lebanon",
    #     "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Malaysia",
    #     "Maldives", "Mali", "Mauritania", "Mexico", "Moldova", "Mongolia",
    #     "Morocco", "Mozambique", "Myanmar", "Namibia", "Nepal", "Nicaragua",
    #     "Niger", "Nigeria", "Pakistan", "Palestine", "Panama", "Papua New Guinea",
    #     "Paraguay", "Peru", "Philippines", "Rwanda", "Samoa", "São Tomé & Príncipe",
    #     "Senegal", "Sierra Leone", "Solomon Islands", "Somalia", "South Africa",
    #     "South Sudan", "Sri Lanka", "Sudan", "Suriname", "Swaziland (Eswatini)",
    #     "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga",
    #     "Tunisia", "Turkey", "Turkmenistan", "Uganda", "Uzbekistan", "Vanuatu",
    #     "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
    # ],
    "Communist": [
        # Very rough / symbolic list — communist or formerly communist or strong socialist legacy
        "Cuba", "Vietnam", "Laos", "China", "North Korea", "Venezuela"
    ],
    "Islamic": [
        # Major / Muslim-majority countries by population or % Muslim
        # Based on top Muslim-population countries :contentReference[oaicite:5]{index=5}
        "Indonesia", "Pakistan", "Bangladesh", "Nigeria", "Egypt", "Iran", "Turkey", "Algeria", "Sudan", "Saudi Arabia", "Yemen", 
        "Iraq", "Afghanistan", "Uzbekistan", "Malaysia", "Morocco", "Mauritania", "Oman", "Tunisia", "Syria", "Jordan", "Burkina Faso",
        "United Arab Emirates", "Algeria", "Libya", "Kuwait", "Qatar", "Bahrain", "Brunei", "Comoros", "Djibouti", "Somalia", "Maldives",
        # Countries with significant Muslim populations
        "Tanzania", "Chad", "Cameroon", "Ivory Coast", "Ghana", "Senegal", "Niger", "Bosnia and Herzegovina", "Albania", "Gambia",
        "Lebanon", "Kenya", "Tajikistan", "Kyrgyzstan", "Azerbaijan", "Kazakhstan", "Turkmenistan", "Sierra Leone", "Guinea", "Kosovo",
        "Mali", "Ethiopia", "Northern Cyprus", 
    ],
    "Undecided": [
        # Countries not clearly in other categories
        # You can refine this later
        # (Later, you'll fill all countries, so this is a default “fallback”)
    ]
}
