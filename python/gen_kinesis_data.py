import pandas as pd
import argparse
import time 
import boto3 
from boto3.dynamodb.conditions import Key
import json
import random
import traceback
import sys
import datetime

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

def generate_random_mins_seconds():
    return random.randint(0,59) # gen random seconds 0~59

def put_records_to_kinesis(options):
    '''Single Record send to kinesis data stream'''
    MAX_RETRY_COUNT = 3
    region = options.region_name
    stream_name = options.stream_name

    clientkinesis = boto3.client('kinesis',region_name=region)

    if not exist_kinesis_stream(options):
        create_kienesis_stream(options)
        time.sleep(2)

    transcation_df = pd.read_csv('../DATA/transaction_order.csv', encoding='utf8',
                dtype={'tr_date':str,'tr_time':str,'store_cd':str,'store_name':str,'pos_num':str,'receipt_num':str,'product_cd':str,'qty':int,'mount':float, 'tr_datetime':str})

    #transcation_df['tr_time'] = transcation_df['tr_time'].apply(lambda x: f'{x:02}') # 또는 아래 코드에서 :02로 변경해줘도됨
    #transcation_df['tr_datetime'] = transcation_df.apply(lambda row: f"{row['tr_date']} {row['tr_time']}:{generate_random_mins_seconds():02}:{generate_random_mins_seconds():02}", axis=1)
    # 미리 적용한 데이터를 그대로 전송.

    transcation_df['tr_datetime'] = pd.to_datetime(transcation_df['tr_datetime'], format='%Y-%m-%d %H:%M:%S')

    COUNT_STEP = 20
    counter = 0
    for idx, row in transcation_df.iterrows():
        row_dict = row.to_dict()

        product_cd = row_dict['product_cd']
        tr_date = row_dict['tr_date']
        
        event_time=datetime.datetime.now().isoformat() # Eventtime 

        row_dict['tr_datetime'] = row_dict['tr_datetime'].isoformat()

        division_cd, division_name, maincategory_cd, maincategory_name, subcategory_cd, subcategory_name, product_cd, product_name, is_pb = get_product_info(options, product_cd)

        row_dict["division_cd"] = division_cd
        row_dict["division_name"] = division_name
        row_dict["maincategory_cd"] = maincategory_cd
        row_dict["maincategory_name"] = maincategory_name
        row_dict["subcategory_cd"] = subcategory_cd
        row_dict["subcategory_name"] = subcategory_name
        row_dict["product_name"] = product_name
        row_dict["is_pb"] = is_pb
        
        row_dict["event_time"] = event_time # 2023-08-10T06:23:13.708884

        payload_list = []
        partition_key = 'part-{:05}'.format(random.randint(1, 1024))
        payload_list.append({'Data': json.dumps(row_dict)+"\n", 'PartitionKey': partition_key})

        for _ in range(MAX_RETRY_COUNT):
            try:
                response = clientkinesis.put_records(Records=payload_list, StreamName=options.stream_name)
                
                break
            except Exception as ex:
                traceback.print_exc()
                time.sleep(random.randint(1, 10))
            else:
                raise RuntimeError('[ERROR] Failed to put_records into stream: {}'.format(options.stream_name))
        
        counter+=1
        if counter % COUNT_STEP == 0:
            print('[INFO] {} records are processed'.format(counter), file=sys.stderr)

        # clientkinesis.put_record(
        #                 StreamName=stream_name,
        #                 Data=json.dumps(row_dict)+"\n",
        #                 PartitionKey=tr_date)

        
        time.sleep(random.choices([1.1, 1.3, 1.5, 1.7, 2])[-1]) # -> time.sleep(random.choices([0.01, 0.03, 0.05, 0.07, 0.1])[-1]) # too fast input records
    
    print('[INFO] Total {} records are processed'.format(counter), file=sys.stderr)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--region-name', action='store', default='ap-northeast-2',
    help='aws region name (default: ap-northeast-2)')
    parser.add_argument('--dynamodb-table-name', default='products_info', help='The name of the dynamodb to put the data record into.')
    parser.add_argument('--stream-name', default='de-enhancement', required=True, help='The name of the stream to put the data record into.')
    #parser.add_argument('--max-count', default=100, type=int, help='The max number of records to put.')

    options = parser.parse_args()

    put_records_to_kinesis(options)
    
if __name__ == "__main__":
    '''python gen_kinesis_data.py --region-name ap-northeast-2 --dynamodb-table-name products_info --stream-name de-enhancement'''
    main()