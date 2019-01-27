# AWS Speech Transcribing
The template defines 
- Source and destination S3 buckets to handle source audio and transcription files
- AWS Lambda function to administrate Amazon Transcribe service
- Roles and Policies required for the application

By default source bucket for audio files named *tweexy-voice*. 
The destination one (to hold transcription files) is *tweexy-transcriptions*. 
Both could be renamed during the template import.  

Feel free to [launch the stack](https://console.aws.amazon.com/cloudformation/home?#/stacks/new?stackName=SpeechTranscribeStack&templateURL=https://s3-us-west-2.amazonaws.com/dtcimbal-cloudformation-templates/transcribe/template.yml)
with AWS CloudFormation
