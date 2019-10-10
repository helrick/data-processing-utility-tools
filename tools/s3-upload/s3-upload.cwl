class: CommandLineTool
cwlVersion: v1.1
id: s3-upload
requirements:
- class: ShellCommandRequirement
- class: NetworkAccess
  networkAccess: true
- class: DockerRequirement
  dockerPull: 'quay.io/icgc-argo/s3-upload:s3-upload.0.1.4'

baseCommand: [ 's3-upload.py' ]

inputs:
  endpoint_url:
    type: string
    inputBinding:
      prefix: -s
  bucket_name:
    type: string
    inputBinding:
      prefix: -b
  bundle_type:
    type: string
    inputBinding:
      prefix: -t
  payload_jsons:
    type: File[]
    inputBinding:
      prefix: -p
  s3_credential_file:
    type: File
    inputBinding:
      prefix: -c
  upload_file:
    type: File
    secondaryFiles: [ ".bai?", ".crai?", ".tbi?", ".idx?" ]
    inputBinding:
      prefix: -f

outputs: []
