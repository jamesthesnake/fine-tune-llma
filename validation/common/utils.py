import boto3


def fetch_ssm_vars():
    ssm_path = (
        "/tacos/hrd-data-science-training"  # move this to config/constants file later
    )
    # use ssm to fetch variables
    client = boto3.client("ssm", region_name="us-west-2")
    response = client.get_parameters_by_path(
        Path=ssm_path, Recursive=True, WithDecryption=True, MaxResults=10,
    )
    final_params = {}
    for param in response["Parameters"]:
        name = param["Name"].replace(f"{ssm_path}/", "")
        name = name.strip()
        final_params[name] = param["Value"]
    return final_params
