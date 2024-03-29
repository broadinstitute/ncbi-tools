#!/usr/bin/env python3

__author__ = "dpark@broadinstitute.org"

import argparse
import csv
import json
import Bio.Entrez
import subprocess


def biosample_lookup(accessions, max_results=10000):

    # get list of primary db IDs
    primary_ids = Bio.Entrez.read(Bio.Entrez.esearch('biosample',
        '|'.join(f'"{a}"' for a in accessions), retmax=max_results))['IdList']

    if not primary_ids:
        return list()

    # fetch biosample entries
    # unfortunately Bio.Entrez.efetch doesn't work for BioSample, so call out
    js_result = subprocess.check_output(['efetch',
        '-id', ','.join(primary_ids),
        '-db', 'biosample', '-mode', 'xml', '-json'])
    biosamples = json.loads(js_result)

    # clean up / reorg structure
    if 'last_update' in biosamples['BioSampleSet']['BioSample']:
        # response is one entry
        biosamples = [biosamples['BioSampleSet']['BioSample']]
    else:
        # response is multiple entries
        biosamples = list(biosamples['BioSampleSet']['BioSample'].values())
    biosamples = list(
        dict(
            # biosample attributes
            [(attribute.get('harmonized_name', attribute['attribute_name']), attribute['content'])
            for attribute in bs['Attributes']['Attribute']]
            # links to other databases, collapsed to lists of IDs per link target. At a minimum a biosample should belong to a bioproject
            + [(link["target"], [l2['label'] for l2 in bs['Links']['Link'] if l2["target"]==link["target"]])
            for link in bs['Links']['Link'] if type(bs['Links']['Link'])==list]
            # if there's only one external db link, the value presents as a dict, so access the values accordingly
            + [(bs['Links']['Link']['target'], bs['Links']['Link']['label']) if type(bs['Links']['Link'])==dict else None]
            # append various other IDs for this sample (ex. SRA accession)
            # ToDo: determine if the IDs are ever not unique by db type, and collapse to list if so
            + [(sample_id["db"],sample_id["content"]) if "db" in sample_id else (sample_id["db_label"],sample_id["content"]) if "db_label" in sample_id else None for sample_id in bs['Ids']["Id"] ]
            + [
                ('accession', bs['accession']),
                ('message', 'Successfully loaded'),
                ('organism', bs['Description']['Organism']['OrganismName']),
            ]
        )
        for bs in biosamples
    )
    us_to_uk = {
        'collected_by': 'collecting institution',
    }
    for bs in biosamples:
        # clear missing values
        for k,v in bs.items():
            if v == 'not provided':
                bs[k] = ''
        ## prefer isolate name over sample_name
        #if bs.get('isolate'):
        #    bs['sample_name'] = bs['isolate']
        #else:
        #    bs['isolate'] = bs.get('sample_name','')
        # British to American conversions (NCBI vs ENA)
        for key_us, key_uk in us_to_uk.items():
            if not bs.get(key_us,''):
                bs[key_us] = bs.get(key_uk,'')

    return biosamples

def main(args):

    # fetch biosample info
    biosamples = biosample_lookup(args.accessions, max_results=args.max_results)

    # get full list of headers/keys and harmonize across all entries
    _required_keys = ('accession', 'message', 'sample_name', 'isolate',
            'collected_by', 'collection_date', 'geo_loc_name', 'host_subject_id',
            'bioproject_accession', 'organism', 'isolation_source', 'lat_lon', 'host',
            'host_sex', 'anatomical_material', 'collection_device', 'collection_method',
            'purpose_of_sampling', 'purpose_of_sequencing')
    keys = list(_required_keys)
    for bs in biosamples:
        for k,v in bs.items():
            if v and k not in keys:
                keys.append(k)
    for bs in biosamples:
        for k in keys:
            bs.setdefault(k, '')

    # write outputs in both json and tsv formats
    with open(args.out_basename+'.json', 'wt') as outf:
        json.dump(biosamples, outf)
    with open(args.out_basename+'.tsv', 'wt') as outf:
        writer = csv.DictWriter(outf, keys,
            extrasaction='ignore',
            delimiter='\t', dialect=csv.unix_dialect, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(biosamples)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve NCBI BioSample metadata')
    parser.add_argument('accessions', nargs='+', help='BioSample accession list')
    parser.add_argument('out_basename', help='output basename for tsv and json output files')
    parser.add_argument('--max_results', type=int, default=10000, help='max results per query (no more than 100000). default: %(default)s')
    args = parser.parse_args()
    main(args)
