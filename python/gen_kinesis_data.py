import pandas as pd
import argparse
import time 
import boto3 
from boto3.dynamodb.conditions import Key
import json


def create_kienesis_stream(options):
    stream_name = options.stream_name
    region = options.region_name

    kinesis = boto3.client('kinesis',region_name=region)
    response = kinesis.create_stream(
        StreamName=stream_name,
        ShardCount=1
    )

def exist_kinesis_stream(options) -> bool:
    stream_name = options.stream_name
    region = options.region_name   

    kinesis = boto3.client('kinesis',region_name=region)
    response = kinesis.list_streams()

    is_exist = any(kinesis_name == stream_name for kinesis_name in response['StreamNames'])

    return is_exist

def get_product_info(options, product_id):
    tablename=options.dynamodb_table_name
    region = options.region_name

    dynamodb = boto3.resource('dynamodb',region_name=region)
    table = dynamodb.Table(tablename)

    response = table.query(
        KeyConditionExpression=Key('product_cd').eq(str(product_id))
    )

    items = response['Items']
    for row in items:
        division_cd	= (row["division_cd"])
        division_name	= (row["division_name"])
        maincategory_cd	= (row["maincategory_cd"])
        maincategory_name	= (row["maincategory_name"])
        subcategory_cd	= (row["subcategory_cd"])
        subcategory_name	= (row["subcategory_name"])
        product_cd	= (row["product_cd"])
        product_name	= (row["product_name"])
        is_pb= (row["is_pb"])
    
    return division_cd, division_name, maincategory_cd, maincategory_name, subcategory_cd, subcategory_name, product_cd, product_name, is_pb

def put_records_to_kinesis(options):
    region = options.region_name
    stream_name = options.stream_name

    clientkinesis = boto3.client('kinesis',region_name=region)

    if not exist_kinesis_stream(options):
        create_kienesis_stream(options)
        time.sleep(2)

    transcation_df = pd.read_csv('../DATA/transaction_order.csv', encoding='utf8',
                dtype={'tr_date':str,'tr_time':str,'store_cd':str,'store_name':str,'pos_num':str,'receipt_num':str,'product_cd':str,'qty':int,'mount':float})

    for idx, row in transcation_df.iterrows():
        row_dict = row.to_dict()

        product_cd = row_dict['product_cd']
        tr_date = row_dict['tr_date']

        division_cd, division_name, maincategory_cd, maincategory_name, subcategory_cd, subcategory_name, product_cd, product_name, is_pb = get_product_info(options, product_cd)

        row_dict["division_cd"] = division_cd
        row_dict["division_name"] = division_name
        row_dict["maincategory_cd"] = maincategory_cd
        row_dict["maincategory_name"] = maincategory_name
        row_dict["subcategory_cd"] = subcategory_cd
        row_dict["subcategory_name"] = subcategory_name
        row_dict["product_name"] = product_name
        row_dict["is_pb"] = is_pb

        clientkinesis.put_record(
                        StreamName=stream_name,
                        Data=json.dumps(row_dict),
                        PartitionKey=tr_date)

        
        time.sleep(1)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--region-name', action='store', default='ap-northeast-2',
    help='aws region name (default: ap-northeast-2)')
    parser.add_argument('--dynamodb-table-name', default='products_info', help='The name of the dynamodb to put the data record into.')
    parser.add_argument('--stream-name', default='de-enhancement', required=True, help='The name of the stream to put the data record into.')

    options = parser.parse_args()

    put_records_to_kinesis(options)

if __name__ == "__main__":
    '''python gen_kinesis_data.py --region-name ap-northeast-2 --dynamodb-table-name products_info --stream-name de-enhancement'''
    main()