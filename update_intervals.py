import boto3
import json

MIN_INTERVAL = 30

def update_interval(table, brand_key: int, model_key: int, new_interval_value: int):
    table.update_item(
        Key={'model_id': f"B{brand_key}:M{model_key}"},
        UpdateExpression="SET schedules.schedules[0].#interval = :interval",
        ExpressionAttributeNames={
            '#interval': 'interval'
        },
        ExpressionAttributeValues={
            ':interval': new_interval_value
        }
    )
 
def update_intervals_for_affected_models():
    """
    Update the intervals for the affected models in the interval_issues.json file.
    """
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
    brand_ddtable = dynamodb.Table("core-hosted-models-ddtable")

    with open('interval_issues.json') as f:
        affected_models_data = json.load(f)

    for model_data in affected_models_data:
        brand_key, model_key = model_data["model_id"].split(":")
        brand_key = int(brand_key.replace("B", ""))
        model_key = int(model_key.replace("M", ""))
        current_interval_value = int(model_data["interval"])
        if current_interval_value > MIN_INTERVAL:
            new_interval_value = max(MIN_INTERVAL, current_interval_value // 60)
        print("Updating interval for model: B%d:M%d to %d minutes" % (brand_key, model_key, new_interval_value))
        update_interval(brand_ddtable, brand_key, model_key, new_interval_value)

        # Verify the update
        updated_config = brand_ddtable.get_item(Key={'model_id': f"B{brand_key}:M{model_key}"})
        assert updated_config['Item']['schedules']['schedules'][0]['interval'] == new_interval_value, "Interval not updated correctly"
    
def create_updated_intervals_json():
    """
    Creates updated_intervals.json by reading current interval values directly from DynamoDB
    for all affected models in interval_issues.json.
    """
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
    brand_ddtable = dynamodb.Table("core-hosted-models-ddtable")

    with open('interval_issues.json') as f:
        affected_models_data = json.load(f)

    updated_data = []
    
    for model_data in affected_models_data:
        model_id = model_data["model_id"]
        schedule_index = model_data["schedule_index"]
        
        # Fetch current config from DynamoDB
        try:
            config = brand_ddtable.get_item(Key={'model_id': model_id})
            
            if 'Item' not in config:
                print(f"Warning: Model {model_id} not found in DynamoDB")
                continue
            
            # Get the interval value from the specific schedule index
            schedules = config['Item'].get('schedules', {}).get('schedules', [])
            
            if schedule_index >= len(schedules):
                print(f"Warning: Schedule index {schedule_index} not found for model {model_id}")
                continue
            
            updated_interval = schedules[schedule_index].get('interval')
            
            if updated_interval is None:
                print(f"Warning: Interval not found for model {model_id} at schedule index {schedule_index}")
                continue
            
            # Convert interval to string to match original format
            updated_interval_str = str(updated_interval)
            
            # Create updated entry with same structure (without as_seconds and as_minutes)
            updated_entry = {
                "model_id": model_id,
                "enabled": model_data.get("enabled", False),
                "interval": updated_interval_str,
                "schedule_index": schedule_index
            }
            
            updated_data.append(updated_entry)
            
        except Exception as e:
            print(f"Error processing model {model_id}: {e}")
            continue
    
    # Write to updated_intervals.json
    with open('updated_intervals.json', 'w') as f:
        json.dump(updated_data, f, indent=2)
    
    print(f"Created updated_intervals.json with {len(updated_data)} entries")
    return updated_data


if __name__ == "__main__":
    update_intervals_for_affected_models()
    create_updated_intervals_json()
    with open('updated_intervals.json') as f:
        updated_intervals_data = json.load(f)
    