import boto3


AWS_REGION = "us-east-1"


def get_parameters(path: str) -> dict:
    """
    讀取 AWS Systems Manager Parameter Store
    例如:
        /stock/prod/db
    """

    client = boto3.client(
        "ssm",
        region_name=AWS_REGION
    )

    paginator = client.get_paginator("get_parameters_by_path")

    parameters = {}

    for page in paginator.paginate(
        Path=path,
        Recursive=False,
        WithDecryption=True
    ):
        for parameter in page["Parameters"]:
            key = parameter["Name"].split("/")[-1]
            parameters[key] = parameter["Value"]

    return parameters