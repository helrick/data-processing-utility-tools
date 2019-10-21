#!/usr/bin/env python3

import os
import sys
import json
import subprocess
from argparse import ArgumentParser
import uuid


def run_cmd(cmd):
    p, success = None, True
    try:
        p = subprocess.run(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=True)
    except Exception as e:
        print('Execution failed: %s' % e)
        success = False

    if p and p.returncode != 0:
        print('\nError occurred, return code: %s. Details: %s' % \
                (p.returncode, p.stderr.decode("utf-8")), file=sys.stderr)
        success = False

    if not success:
        sys.exit(p.returncode if p.returncode else 1)

    return


def get_uuid5(bid, fid):
    uuid5 = str(uuid.uuid5(uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"), "%s/%s" % (bid, fid)))
    return uuid5

def main(args):

    with open(args.metadata, 'r') as f:
        metadata = json.load(f)

    with open(args.payload, 'r') as f:
        payload = json.load(f)

    # generate bundle_id
    payload['id'] = str(uuid.uuid4())

    # generate info field
    payload['info'] = {
        "library_strategy": metadata.get("library_strategy", None),
        "program_id": metadata.get("program_id", None),
        "submitter_donor_id": metadata.get("submitter_donor_id", None),
        "submitter_sample_id": metadata.get("submitter_sample_id", None),
        "tumour_normal_designation": metadata.get("tumour_normal_designation", None)
    }

    # generate object_id
    for key, val in payload.get('files', {}).items():  # some payloads may not have file
        val['object_id'] = get_uuid5(payload['id'], val['name'])

    payload_fname = ".".join([payload['id'], 'json'])

    # payload bucket basepath
    tumour_normal_designation = 'normal' if 'normal' in metadata.get("tumour_normal_designation", '').lower() else 'tumour'
    payload_bucket_basepath = os.path.join(args.bucket_name, 'PCAWG2',
                                        payload['info']['library_strategy'],
                                        payload['info']['program_id'],
                                        payload['info']['submitter_donor_id'],
                                        payload['info']['submitter_sample_id']+'.'+tumour_normal_designation,
                                        payload['type'])

    if payload['type'] in ['sequencing_experiment', 'dna_alignment_qc']:
        payload_object = os.path.join(payload_bucket_basepath, payload_fname)
        if payload['type'] == 'sequencing_experiment':
            payload.pop('info', None)  # sequencing_experiment does not need it

    elif payload['type'] in ['lane_seq_submission', 'lane_seq_qc']:
        payload_object = os.path.join(payload_bucket_basepath, payload['inputs']['submitter_read_group_id'], payload_fname)

    elif payload['type'] in ['dna_alignment']:
        alignment_type = "bam" if payload['files']['aligned_seq']['name'].endswith('bam') else "cram"
        payload_object = os.path.join(payload_bucket_basepath, alignment_type, payload_fname)

    elif payload['type'] in ['somatic_variant_call']:
        wf_short_name = payload['analysis']['tool']['short_name']
        data_type = payload['files']['vcf']['name'].split('.')[-3]
        payload_object = os.path.join(payload_bucket_basepath, wf_short_name, data_type, payload_fname)

    else:
        sys.exit('Unknown payload type!')

    with open(payload_fname, 'w') as f:
        f.write(json.dumps(payload, indent=2))

    cmd = "aws --endpoint-url %s s3 cp %s s3://%s" % (args.endpoint_url, payload_fname, payload_object)
    run_cmd(cmd)



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-s", "--endpoint-url", dest="endpoint_url")
    parser.add_argument("-b", "--bucket-name", dest="bucket_name")
    parser.add_argument("-m", "--metadata", dest="metadata", help="Metadata file contains the information user submit")
    parser.add_argument("-p", "--payload", dest="payload", help="Payload file")
    args = parser.parse_args()

    main(args)
