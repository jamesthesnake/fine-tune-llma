#!/usr/bin/env python3

"""
WORK IN PROGRESS. UNCLEAR IF THIS WILL BE NEEDED AT ALL
"""

from datetime import datetime
import io
import subprocess
import json
import gzip
import csv
import pandas as pd
import requests

from hrd_models.dna_predictor.dna_predictor import DNAPredictor
from validation.common.http_client import HttpClient
from validation.common.utils import fetch_ssm_vars
from data_products_sdk import ClientSettings, Client, OktaConfigProvider

# Global variables
data_products_api = "https://data-products.securetempus.com"
# data_products_api = "https://int-data-products.securetempus.com"
ssm_vars = fetch_ssm_vars()
http_client = HttpClient(ssm_vars)
HEADERS = {"Content-Type": "application/json"}
okta = {
    "url": ssm_vars["OKTA_BASE_URL"],
    "email": ssm_vars["OKTA_USERNAME"],
    "password": ssm_vars["OKTA_PASSWORD"],
    "client_id": ssm_vars["OKTA_CLIENT_ID"],
    "client_secret": ssm_vars["OKTA_CLIENT_SECRET"],
}
client_settings = ClientSettings(
    url=data_products_api, okta_setting=OktaConfigProvider(**okta), async_call=False,
)
client = Client(client_settings)

dt = datetime.now().strftime("%Y%m%d-%H%M%S")


def decode_dp(file_bytes):
    try:
        tsv_file_reader = csv.reader(
            io.StringIO(file_bytes.decode("utf-8")), delimiter="\t", lineterminator="\n"
        )
        metadata_obj = {}
        data = []
        isHeader = True
        for row in tsv_file_reader:
            if row[0] and row[0][0] == "#":
                metadata = row[0].replace(" ", "").split("=")
                header = metadata[0].replace("#", "")
                metadata_obj[header] = metadata[1]
                # data.append(metadata[1])
            elif isHeader == True:
                isHeader = False
                columns = row
            else:
                data.append(row)
        tsv_df = pd.DataFrame(data, columns=columns)
        return tsv_df
    except Exception as e:
        raise Exception(f"Failed to decode dp file. Returned error: {e}")


def decode_bioinf_file(file_bytes):
    try:
        file_reader = pd.read_csv(io.StringIO(file_bytes.decode("utf-8")))
        return file_reader
    except Exception as e:
        raise Exception(f"Failed to decode bioinf file. Returned error: {e}")


def get_variants_dp(order_id, analysis_id):
    search_body = {
        "terms": [
            {"key": "original-order-id", "value": order_id},
            {"key": "bioinformatics-analysis-id", "value": analysis_id},
        ],
        "types": ["hrd-dna-analysis-gene-mutation"],
    }
    # search_res = requests.post(search_url, data=search_body, headers=HEADERS).json()
    search_res = client.search_data_product(**search_body)
    # search_res = http_client.request('POST', search_url, data=search_body, headers=HEADERS).json()
    # Handle ammendments by taking latest
    latest_dp_index = 0
    dp_num = len(search_res["data_products"])
    print(search_res["data_products"])
    if dp_num > 1:
        dp_last_modified = search_res["data_products"][latest_dp_index]["lastModified"]
        for dp in range(dp_num):
            if dp_last_modified < search_res["data_products"][dp]["lastModified"]:
                dp_last_modified = search_res["data_products"][dp]["lastModified"]
                latest_dp_index = dp
    elif dp_num == 1:
        vars_dp = search_res["data_products"][latest_dp_index]
    else:
        print("Missing reported-dna-variants DP")
    vars_dp_id = vars_dp["id"]
    print(vars_dp_id)
    # dp_res = requests.get(get_url, headers=HEADERS).json()
    # dp_res = http_client.request('GET', get_url, headers=HEADERS).json()
    dp_res = client.get_data_product(vars_dp_id, response_type="signed_url")
    # dp = json.loads(dp_res)
    # dp_df = pd.DataFrame.from_dict(dp)
    dp_download = dp_res["data"]
    dp_file_io = requests.get(dp_download)
    # dp_file_io = http_client.request('GET', dp_download)
    dp_df = decode_dp(gzip.decompress(dp_file_io.content))
    # # remove patientId, pCaseId
    # dp_df = dp_df.drop(columns=['patientId', 'pCaseId'])

    return dp_df


def get_bioinf_file(file_type, analysis_id):
    url = "https://int-bioinf-db.tempusbioinformatics.com/v1/analyses/{}".format(
        analysis_id
    )
    # an_response = requests.get(url, headers=HEADERS).json()
    an_response = http_client.request("GET", url, headers=HEADERS).json()
    file = parse_for_file(an_response, file_type)
    # In case file is not present
    if file is not None:
        file_obj = download_file(file["signedUrl"])
        file_decoded = decode_bioinf_file(file_obj)
        # file_decoded.to_csv(f'test-{file_type}.csv')
    else:
        file_decoded = None
    return file_decoded


def parse_for_file(res, file_type):
    for file in res["outputs"]:
        if file["type"] == file_type:
            return file


def download_file(url):
    download_response = requests.get(url, timeout=10)
    # download_response = http_client.request('GET', url, timeout=10)
    if download_response.status_code == 200:
        return download_response.content
    else:
        raise ValueError(
            f"Download file Failed. Returned 'status_code' = {download_response.status_code}"
        )


def write_file(file_df, order_id, analysis_id, test):
    file = f"hrd_files/{test}-{order_id}-{analysis_id}.variants.tsv"
    file_df.to_csv(file, sep="\t", encoding="utf-8", index=False)


def main():
    orderhub_id = "21tcuydw"
    analysis_id = "af5gvxoukfgkdnkrtdxfut3xfm"
    variants_dp_df = get_variants_dp(orderhub_id, analysis_id)
    print(variants_dp_df)


main()
