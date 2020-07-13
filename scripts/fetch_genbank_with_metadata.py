#!/usr/bin/env python3
"""
Hacky GenBank metadatascript adapted by tomkinsc@broadinstitute 2020-06-11
 from: https://raw.githubusercontent.com/nextstrain/ncov-ingest/0ea529fa5c02fe4e1330e9636a08bca0aa8006c9/bin/fetch-from-genbank
Download all SARS-CoV-2 sequences and their curated metadata from GenBank via NCBI Virus.

Only output sequences with locations populated

Based on AJAX requests performed by:
    https://www.ncbi.nlm.nih.gov/labs/virus/vssi/#/virus?SeqType_s=Nucleotide&VirusLineage_ss=Severe%20acute%20respiratory%20syndrome%20coronavirus%202,%20taxid:2697049
"""


gmaps                             = googlemaps.Client(key=os.environ.get("GOOGLE_MAPS_API_KEY"))
USER_EMAIL                        = os.environ.get("MY_EMAIL")
VIRUS_TAXON_ID                    = "2697049" # NCBI taxon ID
VIRUS_COL                         = "ncov" # value for the "virus" column of output
normalize_homo_sapiens_to_human   = True

RETURN_COUNT_LIMIT=None #250 # None = return all

# parse will set M/D/Y respectively to these values if not set (if day is not specified, assume 1st of the month. January if no month)
placeholder_date_vals = datetime.strptime('01/01/01', '%m/%d/%y')

continent_for_country = { #see https://gist.github.com/nobuti/3816985
"AF":"Asia", # "Islamic Republic of Afghanistan 
"AX":"Europe", # "Åland Islands 
"AL":"Europe", # "Republic of Albania 
"DZ":"Africa", # "People's Democratic Republic of Algeria 
"AS":"Oceania", # "American Samoa 
"AD":"Europe", # "Principality of Andorra 
"AO":"Africa", # "Republic of Angola 
"AI":"North America", # "Anguilla 
"AQ":"Antarctica", # "Antarctica (the territory South of 60 deg S) 
"AG":"North America", # "Antigua and Barbuda 
"AR":"South America", # "Argentine Republic 
"AM":"Asia", # "Republic of Armenia 
"AW":"North America", # "Aruba 
"AU":"Oceania", # "Commonwealth of Australia 
"AT":"Europe", # "Republic of Austria 
"AZ":"Asia", # "Republic of Azerbaijan 
"BS":"North America", # "Commonwealth of the Bahamas 
"BH":"Asia", # "Kingdom of Bahrain 
"BD":"Asia", # "People's Republic of Bangladesh 
"BB":"North America", # "Barbados 
"BY":"Europe", # "Republic of Belarus 
"BE":"Europe", # "Kingdom of Belgium 
"BZ":"North America", # "Belize 
"BJ":"Africa", # "Republic of Benin 
"BM":"North America", # "Bermuda 
"BT":"Asia", # "Kingdom of Bhutan 
"BO":"South America", # "Plurinational State of Bolivia 
"BQ":"North America", # '535' 
"BA":"Europe", # "Bosnia and Herzegovina 
"BW":"Africa", # "Republic of Botswana 
"BV":"Antarctica", # "Bouvet Island (Bouvetoya) 
"BR":"South America", # "Federative Republic of Brazil 
"IO":"Asia", # "British Indian Ocean Territory (Chagos Archipelago) 
"VG":"North America", # "British Virgin Islands 
"BN":"Asia", # "Brunei Darussalam 
"BG":"Europe", # "Republic of Bulgaria 
"BF":"Africa", # "Burkina Faso 
"BI":"Africa", # "Republic of Burundi 
"KH":"Asia", # "Kingdom of Cambodia 
"CM":"Africa", # "Republic of Cameroon 
"CA":"North America", # "Canada 
"CV":"Africa", # "Republic of Cape Verde 
"KY":"North America", # "Cayman Islands 
"CF":"Africa", # "Central African Republic 
"TD":"Africa", # "Republic of Chad 
"CL":"South America", # "Republic of Chile 
"CN":"Asia", # "People's Republic of China 
"CX":"Asia", # "Christmas Island 
"CC":"Asia", # "Cocos (Keeling) Islands 
"CO":"South America", # "Republic of Colombia 
"KM":"Africa", # "Union of the Comoros 
"CD":"Africa", # "Democratic Republic of the Congo 
"CG":"Africa", # "Republic of the Congo 
"CK":"Oceania", # "Cook Islands 
"CR":"North America", # "Republic of Costa Rica 
"CI":"Africa", # "Republic of Cote d'Ivoire 
"HR":"Europe", # "Republic of Croatia 
"CU":"North America", # "Republic of Cuba 
"CW":"North America", # "Curaçao 
"CY":"Asia", # "Republic of Cyprus 
"CZ":"Europe", # "Czech Republic 
"DK":"Europe", # "Kingdom of Denmark 
"DJ":"Africa", # "Republic of Djibouti 
"DM":"North America", # "Commonwealth of Dominica 
"DO":"North America", # "Dominican Republic 
"EC":"South America", # "Republic of Ecuador 
"EG":"Africa", # "Arab Republic of Egypt 
"SV":"North America", # "Republic of El Salvador 
"GQ":"Africa", # "Republic of Equatorial Guinea 
"ER":"Africa", # "State of Eritrea 
"EE":"Europe", # "Republic of Estonia 
"ET":"Africa", # "Federal Democratic Republic of Ethiopia 
"FO":"Europe", # "Faroe Islands 
"FK":"South America", # "Falkland Islands (Malvinas) 
"FJ":"Oceania", # "Republic of Fiji 
"FI":"Europe", # "Republic of Finland 
"FR":"Europe", # "French Republic 
"GF":"South America", # "French Guiana 
"PF":"Oceania", # "French Polynesia 
"TF":"Antarctica", # "French Southern Territories 
"GA":"Africa", # "Gabonese Republic 
"GM":"Africa", # "Republic of the Gambia 
"GE":"Asia", # "Georgia 
"DE":"Europe", # "Federal Republic of Germany 
"GH":"Africa", # "Republic of Ghana 
"GI":"Europe", # "Gibraltar 
"GR":"Europe", # "Hellenic Republic Greece 
"GL":"North America", # "Greenland 
"GD":"North America", # "Grenada 
"GP":"North America", # "Guadeloupe 
"GU":"Oceania", # "Guam 
"GT":"North America", # "Republic of Guatemala 
"GG":"Europe", # "Bailiwick of Guernsey 
"GN":"Africa", # "Republic of Guinea 
"GW":"Africa", # "Republic of Guinea-Bissau 
"GY":"South America", # "Co-operative Republic of Guyana 
"HT":"North America", # "Republic of Haiti 
"HM":"Antarctica", # "Heard Island and McDonald Islands 
"VA":"Europe", # "Holy See (Vatican City State) 
"HN":"North America", # "Republic of Honduras 
"HK":"Asia", # "Hong Kong Special Administrative Region of China 
"HU":"Europe", # "Hungary 
"IS":"Europe", # "Republic of Iceland 
"IN":"Asia", # "Republic of India 
"ID":"Asia", # "Republic of Indonesia 
"IR":"Asia", # "Islamic Republic of Iran 
"IQ":"Asia", # "Republic of Iraq 
"IE":"Europe", # "Ireland 
"IM":"Europe", # "Isle of Man 
"IL":"Asia", # "State of Israel 
"IT":"Europe", # "Italian Republic 
"JM":"North America", # "Jamaica 
"JP":"Asia", # "Japan 
"JE":"Europe", # "Bailiwick of Jersey 
"JO":"Asia", # "Hashemite Kingdom of Jordan 
"KZ":"Asia", # "Republic of Kazakhstan 
"KE":"Africa", # "Republic of Kenya 
"KI":"Oceania", # "Republic of Kiribati 
"KP":"Asia", # "Democratic People's Republic of Korea 
"KR":"Asia", # "Republic of Korea 
"KW":"Asia", # "State of Kuwait 
"KG":"Asia", # "Kyrgyz Republic 
"LA":"Asia", # "Lao People's Democratic Republic 
"LV":"Europe", # "Republic of Latvia 
"LB":"Asia", # "Lebanese Republic 
"LS":"Africa", # "Kingdom of Lesotho 
"LR":"Africa", # "Republic of Liberia 
"LY":"Africa", # "Libya 
"LI":"Europe", # "Principality of Liechtenstein 
"LT":"Europe", # "Republic of Lithuania 
"LU":"Europe", # "Grand Duchy of Luxembourg 
"MO":"Asia", # "Macao Special Administrative Region of China 
"MK":"Europe", # "Republic of Macedonia 
"MG":"Africa", # "Republic of Madagascar 
"MW":"Africa", # "Republic of Malawi 
"MY":"Asia", # "Malaysia 
"MV":"Asia", # "Republic of Maldives 
"ML":"Africa", # "Republic of Mali 
"MT":"Europe", # "Republic of Malta 
"MH":"Oceania", # "Republic of the Marshall Islands 
"MQ":"North America", # "Martinique 
"MR":"Africa", # "Islamic Republic of Mauritania 
"MU":"Africa", # "Republic of Mauritius 
"YT":"Africa", # "Mayotte 
"MX":"North America", # "United Mexican States 
"FM":"Oceania", # "Federated States of Micronesia 
"MD":"Europe", # "Republic of Moldova 
"MC":"Europe", # "Principality of Monaco 
"MN":"Asia", # "Mongolia 
"ME":"Europe", # "Montenegro 
"MS":"North America", # "Montserrat 
"MA":"Africa", # "Kingdom of Morocco 
"MZ":"Africa", # "Republic of Mozambique 
"MM":"Asia", # "Republic of the Union of Myanmar 
"NA":"Africa", # "Republic of Namibia 
"NR":"Oceania", # "Republic of Nauru 
"NP":"Asia", # "Federal Democratic Republic of Nepal 
"NL":"Europe", # "Kingdom of the Netherlands 
"NC":"Oceania", # "New Caledonia 
"NZ":"Oceania", # "New Zealand 
"NI":"North America", # "Republic of Nicaragua 
"NE":"Africa", # "Republic of Niger 
"NG":"Africa", # "Federal Republic of Nigeria 
"NU":"Oceania", # "Niue 
"NF":"Oceania", # "Norfolk Island 
"MP":"Oceania", # "Commonwealth of the Northern Mariana Islands 
"NO":"Europe", # "Kingdom of Norway 
"OM":"Asia", # "Sultanate of Oman 
"PK":"Asia", # "Islamic Republic of Pakistan 
"PW":"Oceania", # "Republic of Palau 
"PS":"Asia", # "Occupied Palestinian Territory 
"PA":"North America", # "Republic of Panama 
"PG":"Oceania", # "Independent State of Papua New Guinea 
"PY":"South America", # "Republic of Paraguay 
"PE":"South America", # "Republic of Peru 
"PH":"Asia", # "Republic of the Philippines 
"PN":"Oceania", # "Pitcairn Islands 
"PL":"Europe", # "Republic of Poland 
"PT":"Europe", # "Portuguese Republic 
"PR":"North America", # "Commonwealth of Puerto Rico 
"QA":"Asia", # "State of Qatar 
"RE":"Africa", # "Réunion 
"RO":"Europe", # "Romania 
"RU":"Europe", # "Russian Federation 
"RW":"Africa", # "Republic of Rwanda 
"BL":"North America", # "Saint Barthélemy 
"SH":"Africa", # '654' 
"KN":"North America", # "Federation of Saint Kitts and Nevis 
"LC":"North America", # "Saint Lucia 
"MF":"North America", # "Saint Martin (French part) 
"PM":"North America", # "Saint Pierre and Miquelon 
"VC":"North America", # "Saint Vincent and the Grenadines 
"WS":"Oceania", # "Independent State of Samoa 
"SM":"Europe", # "Republic of San Marino 
"ST":"Africa", # "Democratic Republic of Sao Tome and Principe 
"SA":"Asia", # "Kingdom of Saudi Arabia 
"SN":"Africa", # "Republic of Senegal 
"RS":"Europe", # "Republic of Serbia 
"SC":"Africa", # "Republic of Seychelles 
"SL":"Africa", # "Republic of Sierra Leone 
"SG":"Asia", # "Republic of Singapore 
"SX":"North America", # "Sint Maarten (Dutch part) 
"SK":"Europe", # "Slovakia (Slovak Republic) 
"SI":"Europe", # "Republic of Slovenia 
"SB":"Oceania", # "Solomon Islands 
"SO":"Africa", # "Somali Republic 
"ZA":"Africa", # "Republic of South Africa 
"GS":"Antarctica", # "South Georgia and the South Sandwich Islands 
"SS":"Africa", # "Republic of South Sudan 
"ES":"Europe", # "Kingdom of Spain 
"LK":"Asia", # "Democratic Socialist Republic of Sri Lanka 
"SD":"Africa", # "Republic of Sudan 
"SR":"South America", # "Republic of Suriname 
"SJ":"Europe", # "Svalbard & Jan Mayen Islands 
"SZ":"Africa", # "Kingdom of Swaziland 
"SE":"Europe", # "Kingdom of Sweden 
"CH":"Europe", # "Swiss Confederation 
"SY":"Asia", # "Syrian Arab Republic 
"TW":"Asia", # "Taiwan 
"TJ":"Asia", # "Republic of Tajikistan 
"TZ":"Africa", # "United Republic of Tanzania 
"TH":"Asia", # "Kingdom of Thailand 
"TL":"Asia", # "Democratic Republic of Timor-Leste 
"TG":"Africa", # "Togolese Republic 
"TK":"Oceania", # "Tokelau 
"TO":"Oceania", # "Kingdom of Tonga 
"TT":"North America", # "Republic of Trinidad and Tobago 
"TN":"Africa", # "Tunisian Republic 
"TR":"Asia", # "Republic of Turkey 
"TM":"Asia", # "Turkmenistan 
"TC":"North America", # "Turks and Caicos Islands 
"TV":"Oceania", # "Tuvalu 
"UG":"Africa", # "Republic of Uganda 
"UA":"Europe", # "Ukraine 
"AE":"Asia", # "United Arab Emirates 
"GB":"Europe", # "United Kingdom of Great Britain & Northern Ireland 
"US":"North America", # "United States of America 
"UM":"Oceania", # "United States Minor Outlying Islands 
"VI":"North America", # "United States Virgin Islands 
"UY":"South America", # "Eastern Republic of Uruguay 
"UZ":"Asia", # "Republic of Uzbekistan 
"VU":"Oceania", # "Republic of Vanuatu 
"VE":"South America", # "Bolivarian Republic of Venezuela 
"VN":"Asia", # "Socialist Republic of Vietnam 
"WF":"Oceania", # "Wallis and Futuna 
"EH":"Africa", # "Western Sahara 
"YE":"Asia", # "Yemen 
"ZM":"Africa", # "Republic of Zambia 
"ZW":"Africa" # "Republic of Zimbabwe
}

# memoize dict in global scope so we can dump at the end
memo = {}

def memoize(f):
    def helper(x):
        if x not in memo:     
            memo[x] = f(x)
        else:
            #print("cache hit!",x)
            pass
        return memo[x]
    return helper

endpoint = "https://www.ncbi.nlm.nih.gov/genomes/VirusVariation/vvsearch2/"
params = {
    # Search criteria
    'fq': [
        '{!tag=SeqType_s}SeqType_s:("Nucleotide")', # Nucleotide sequences (as opposed to protein)
        'VirusLineageId_ss:({})'.format(VIRUS_TAXON_ID),              # NCBI Taxon id for SARS-CoV-2
    ],

    # Unclear, but seems necessary.
    'q': '*:*',

    # Response format
    'cmd': 'download',
    'dlfmt': 'csv',
    'fl': ','.join(
        ':'.join(names) for names in [
            # Pairs of (output column name, source data field).  These are pulled
            # from watching requests from the UI.
            #
            # XXX TODO: Is the full set source data fields documented
            # somewhere?  Is there more info we could be pulling that'd be
            # useful?
            #   -trs, 13 May 2020
            ('genbank_accession',       'id'),
            ('database',                'SourceDB_s'),
            ('strain',                  'Isolate_s'),
            ('region',                  'Region_s'),
            ('location',                'CountryFull_s'),
            ('collected',               'CollectionDate_s'),
            ('submitted',               'CreateDate_dt'),
            ('length',                  'SLen_i'),
            ('host',                    'Host_s'),
            ('isolation_source',        'Isolation_csv'),
            ('biosample_accession',     'BioSample_s'),
            ('title',                   'Definition_s'),
            ('authors',                 'Authors_csv'),
            ('publications',            'PubMed_csv'),
            ('sequence',                'Nucleotide_seq'),
        ]
    ),

    # Stable sort with newest last so diffs work nicely.  Columns are source
    # data fields, not our output columns.
    'sort': 'SourceDB_s desc, CollectionDate_s asc, id asc',

    # This isn't Entrez, but include the same email parameter it requires just
    # to be nice.
    'email': USER_EMAIL,
}

headers = {
    'User-Agent': 'https://github.com/broadinstitute/viral-pipelines ({})'.format(USER_EMAIL),
}

response = requests.get(endpoint, params = params, headers = headers, stream = True)
response.raise_for_status()

response_content = response.iter_lines(decode_unicode = True)

def get_continent(gmaps_response):
    """
        get the continent for a two-letter country code
    """
    # with the above scheme, we can't get the continent if the country is unknown (ex. contested territories)
    return continent_for_country.get(get_country(gmaps_response, short_name=True),"NA")

def get_types(gmaps_response):
    """
        Get the geocoded location "types" (precision levels, location designations, etc.)
        for a geocoded location
    """
    if len(gmaps_response):
        types = gmaps_response[0]["types"]
        while "political" in types: types.remove("political")
        return types
    return None

def get_precision(gmaps_response):
    """
    For information on granularity types, see:
      https://developers.google.com/maps/documentation/geocoding/intro#Types
    Numbers for level ranking are assigned somewhat arbitrarily
    """
    precision_levels = {
        "country": 1,
        "administrative_area_level_1": 2, # ~=state
        "administrative_area_level_2": 3, # ~=county
        "administrative_area_level_3": 4, # ~=locality
        "administrative_area_level_4": 5,
        "administrative_area_level_5": 6,
        "locality": 4,
        "sublocality": 5,
        "sublocality_level_1": 6,
        "sublocality_level_2": 7,
        "sublocality_level_3": 8,
        "sublocality_level_4": 9,
        "sublocality_level_5": 10,
    }

    types = get_types(gmaps_response)
    if types is not None:
        greatest_precision_seen=0
        most_precise_level=None
        types_present = list(set(precision_levels.keys()) & set(types))
        # return the last-seen most-precision location level
        for e in types_present:
            level_of_this_type=precision_levels.get(precision_levels[e],1)
            if level_of_this_type>greatest_precision_seen:
                greatest_precision_seen=level_of_this_type
                most_precise_level=e
        return (most_precise_level, greatest_precision_seen)
    return None

def get_country(gmaps_response, short_name=False):
    if len(gmaps_response):
        if len(gmaps_response[0]["address_components"]):
            for level in gmaps_response[0]["address_components"]:
                if "country" in level["types"]:
                    if short_name:
                        return level["short_name"]
                    else:
                        return level["long_name"]
    return None

def get_most_precise_location(gmaps_response, level_spec, short_name=False):
    if len(gmaps_response):
        if len(gmaps_response[0]["address_components"]):
            for level in gmaps_response[0]["address_components"]:
                if level_spec in level["types"]:
                    if not short_name:
                        return level["long_name"]
                    else:
                        return level["short_name"]
    return None

@memoize
def geocode_location(location_str):
    reformatted_location_str=",".join([x.strip() for x in reversed(location_str.split(":"))]).replace(", ",",").replace(",",", ")
    geocode_result = gmaps.geocode(reformatted_location_str)

    if len(geocode_result)>0:
        location = geocode_result[0]["geometry"]["location"]
    else:
        pass

    found_continent = get_continent(geocode_result)
    found_country = get_country(geocode_result)

    loc_precision = get_precision(geocode_result)
    found_division = get_most_precise_location(geocode_result, "administrative_area_level_1") or found_country
    found_location = get_most_precise_location(geocode_result, loc_precision[0])

    return {    
            "lat": location["lat"],
            "lng": location["lng"],
            "continent": found_continent,
            "location_precision": loc_precision,
            "country": found_country,
            "division":found_division,
            "location": found_location if found_location!=found_division else found_division,
            }

fields_to_write=OrderedDict([
                ("strain",None),
                ("virus",None),
                ("gisaid_epi_isl",None),
                ("genbank_accession",None),
                ("database",None),
                ("date",None),
                ("region",None),
                ("country",None),
                ("division",None),
                ("location",None),
                ("gb_raw_location",None),
                ("geocode_precision",None),
                ("region_exposure",None),
                ("country_exposure",None),
                ("division_exposure",None),
                ("length",None),
                ("host",None),
                ("age",None),
                ("sex",None),
                ("originating_lab",None),
                ("submitting_lab",None),
                ("date_submitted",None),
                ("biosample_accession",None),
                ("geocat",None),
                ("authors",None),
                ("url",None),
                ("title",None),
                 ])

with open("genbank_seqs.fasta","w") as outfasta:
    with open("genbank_seq_metadata.tsv","w") as outf:

        dw = csv.DictWriter(outf, delimiter='\t', fieldnames=fields_to_write)
        dw.writeheader()

        for idx, row in enumerate(csv.DictReader(response_content)):

            # if location is null, continue to the next sequence
            if len(row["location"])==0:
                continue

            loc = geocode_location(row["location"])

            if row["host"]=="Homo sapiens" and normalize_homo_sapiens_to_human:
                host = "Human"
            else:
                host = row["host"].replace(" ","-")

            fields_to_write["strain"]              = row["genbank_accession"] # or maybe row["strain"]
            fields_to_write["virus"]               = VIRUS_COL
            fields_to_write["gisaid_epi_isl"]      = None
            fields_to_write["genbank_accession"]   = row["genbank_accession"]
            fields_to_write["database"]            = row["database"]
            fields_to_write["date"]                = dateutil.parser.parse(row["collected"], default=placeholder_date_vals).strftime('%Y-%m-%d') # parse().isoformat()
            fields_to_write["region"]              = loc["continent"]
            fields_to_write["country"]             = loc["country"]
            fields_to_write["division"]            = loc["division"]
            fields_to_write["location"]            = loc["location"]
            fields_to_write["gb_raw_location"]     = row["location"]
            fields_to_write["geocode_precision"]   = loc["location_precision"][0]
            fields_to_write["region_exposure"]     = loc["continent"] # should perhaps be set to None
            fields_to_write["country_exposure"]    = loc["country"] # should perhaps be set to None
            fields_to_write["division_exposure"]   = loc["location"] # should perhaps be set to None
            fields_to_write["length"]              = len(row["sequence"])
            fields_to_write["host"]                = host
            fields_to_write["age"]                 = None
            fields_to_write["sex"]                 = None
            fields_to_write["originating_lab"]     = None
            fields_to_write["submitting_lab"]      = None
            fields_to_write["date_submitted"]      = dateutil.parser.parse(row["submitted"], default=placeholder_date_vals).strftime('%Y-%m-%d') # parse().isoformat()
            fields_to_write["biosample_accession"] = row["biosample_accession"]
            fields_to_write["geocat"]              = loc["loc_category"]
            fields_to_write["authors"]             = row["authors"]
            fields_to_write["url"]                 = None
            fields_to_write["title"]               = row["title"]
            
            fields_to_write={key:"NA" if (val is None or val=="") else val for key,val in fields_to_write.items() }
            dw.writerow(fields_to_write)

            # write sequence to output fasta
            outfasta.write(">{accession}\n{seq}\n\n".format(accession=row["genbank_accession"],seq=row["sequence"]))

            #print(fields_to_write)

            if (idx+1)%50==0:
                print("Found data for %s seqs" % (idx+1))

            # to dump reply from GenBank
            #print(json.dumps(row, allow_nan = False, indent = None, separators = ',:'))

            # to halt after so many records
            if RETURN_COUNT_LIMIT is not None:
                if idx >= RETURN_COUNT_LIMIT-1:
                    break

with open("genbank_locations_map.tsv", "w") as outf:
    outf.write("name\tlat\tlon\tprecision\n")
    for location in sorted(memo):
        outf.write("\t".join([location]+[ str(memo[location]["lat"]), str(memo[location]["lng"]) ])+"\n")

print("number of geo API calls:",len(memo))
