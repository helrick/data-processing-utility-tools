#!/usr/bin/env python3

"""
 Copyright (c) 2019-2020, Ontario Institute for Cancer Research (OICR).

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published
 by the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program. If not, see <https://www.gnu.org/licenses/>.

 Authors:
   Junjun Zhang <junjun.zhang@oicr.on.ca>
 """

import os
import sys
import uuid
import json
import hashlib
from argparse import ArgumentParser


def calculate_size(file_path):
    return os.stat(file_path).st_size


def calculate_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            md5.update(chunk)
    return md5.hexdigest()


def get_files_info(file_to_upload):
    return {
        'fileName': os.path.basename(file_to_upload),
        'fileType': file_to_upload.split(".")[-1].upper(),
        'fileSize': calculate_size(file_to_upload),
        'fileMd5sum': calculate_md5(file_to_upload),
        'fileAccess': 'controlled',
        'dataType': 'SSM' if not file_to_upload.split(".")[-1] in ('tbi', 'idx') else 'vcf_index'
    }


def main(args):
    normal_analysis = {}
    with open(args.normal_analysis, 'r') as f:
        normal_analysis = json.load(f)

    tumour_analysis = {}
    if args.tumour_analysis:
        with open(args.tumour_analysis, 'r') as f:
            tumour_analysis = json.load(f)

    somatic_or_germline = 'somatic'
    if args.wf_short_name == 'sanger-wgs':
        metadata = tumour_analysis
    elif args.wf_short_name == 'sanger-wxs':
        metadata = tumour_analysis
    elif args.wf_short_name == 'HaplotypeCaller':
        metadata = tumour_analysis
        somatic_or_germline = 'germline'
    else:
        sys.exit("Unsupported variant caller: %s" % args.wf_short_name)

    payload = {
        'analysisType': {
            'name': 'variant_calling'
        },
        'studyId': metadata.get('program_id'),
        'experiment': {},
        'samples': [],
        'files': [],
        'inputs': []
    }

    # get sample of the payload
    sample = {
        'submitterSampleId': metadata.get('submitter_sample_id'),
        'matchedNormalSubmitterSampleId': metadata.get('submitter_matched_normal_sample_id'),
        'sampleType': metadata.get('sample_type'),
        'specimen': {
            'submitterSpecimenId': metadata.get('submitter_specimen_id'),
            'tumourNormalDesignation': metadata.get('tumour_normal_designation'),
            'specimenTissueSource': metadata.get('specimen_tissue_source'),
            'specimenType': metadata.get('specimen_type')
        },
        'donor': {
            'submitterDonorId': metadata.get('submitter_donor_id'),
            'gender': metadata.get('gender')
        }
    }

    payload['samples'].append(sample)


    for f in args.files_to_upload:
      payload['files'].append(get_files_info(f))

    with open("%s.variant_calling.payload.json" % str(uuid.uuid4()), 'w') as f:
        f.write(json.dumps(payload, indent=2))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-n", dest="normal_analysis", required=True,
                        help="json file containing sequencing_alignment SONG analysis for normal sample")
    parser.add_argument("-t", dest="tumour_analysis", required=False,
                        help="json file containing sequencing_alignment SONG analysis for tumour sample")
    parser.add_argument("-f", dest="files_to_upload", type=str, nargs="+", help="Files to be uploaded", required=True)
    parser.add_argument("-w", dest="wf_name", type=str, help="workflow full name", required=True)
    parser.add_argument("-s", dest="wf_short_name", type=str, help="workflow short name", required=True)
    parser.add_argument("-v", dest="wf_version", type=str, required=True, help="workflow version")
    parser.add_argument("-r", dest="wf_run", type=str, required=True, help="workflow run ID")
    args = parser.parse_args()

    main(args)
