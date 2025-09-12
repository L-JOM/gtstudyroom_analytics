import boto3
import json

def save_json_snapshot(bucket_name, prefix, data, snapshot_time):
    s3 = boto3.client()
    
    timestamp = snapshot_time
    timestamp_prefix = f"year={timestamp.year}/month={timestamp.month}/day={timestamp.day}/hour={timestamp.hour}/minute={timestamp.minute}"
    json_data = json.dump(data)
    key = f"{prefix}/{timestamp_prefix}.json"
    
    s3.Bucket(bucket_name).put_object(Bucket=bucket_name, Key=key, Body=json_data, ContentType="application/json")
    
    (print(f"Snapshot saved: s3://{bucket_name}/{key}"))