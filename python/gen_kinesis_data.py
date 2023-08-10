import pandas as pd
import argparse
import time 
import boto3 
from boto3.dynamodb.conditions import Key
import json
import random
import traceback
import sys

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
    '''Single Record send to kinesis data stream'''
    MAX_RETRY_COUNT = 3
    region = options.region_name
    stream_name = options.stream_name

    clientkinesis = boto3.client('kinesis',region_name=region)

    if not exist_kinesis_stream(options):
        create_kienesis_stream(options)
        time.sleep(2)

    transcation_df = pd.read_csv('../DATA/transaction_order.csv', encoding='utf8',
                dtype={'tr_date':str,'tr_time':str,'store_cd':str,'store_name':str,'pos_num':str,'receipt_num':str,'product_cd':str,'qty':int,'mount':float})

    COUNT_STEP = 20
    counter = 0
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

        
        time.sleep(random.choices([0.01, 0.03, 0.05, 0.07, 0.1])[-1])
    
    print('[INFO] Total {} records are processed'.format(counter), file=sys.stderr)

# def get_batch_items_dynamodb(options, pk_list, pk_column_name):
#     # batch item 이 100개가 넘으면 에러를 뱉어낸다. 

#     dynamodb_table_name = options.dynamodb_table_name

#     keys_to_get = [{pk_column_name : pk} for pk in pk_list]

#     batch_keys = {
#         dynamodb_table_name : {
#             "Keys" : keys_to_get
#         }
#     }

#     print(batch_keys)

#     dynamodb = boto3.resource('dynamodb')
    
#     # try:
#     #     response = dynamodb.batch_get_item(
#     #         RequestItems=batch_keys,
#     #         ReturnConsumedCapacity='TOTAL'
#     #     )

#     #     products_df = pd.DataFrame(response['Responses'][dynamodb_table_name])
#     #     return products_df
    
#     # except Exception as e:
#     #     print(f"There is no {pk_column_name} values, Exception String : {str(e)}")
#     #     return pd.DataFrame(columns=[])

#     products_df = pd.DataFrame(response['Responses'][dynamodb_table_name])
#     return products_df
    
# def wrtie_max_cnt(current_line: int) -> bool:
#     try:
#         with open('max_cnt.txt','w') as f:
#             f.write(str(current_line))
        
#         return True
#     except Exception as e:
#         print(e)
#         return False
        
# def gen_records(options):
#     max_count = int(options.max_count)

#     try:
#         with open('max_cnt.txt', 'r') as f:
#             past_lines = f.read()

#             int_past_lines = int(past_lines)
#             current_line = int_past_lines + max_count
#     except Exception as e:
#         current_line = max_count
#         int_past_lines = 0

#     wrtie_max_cnt(current_line) # write watermark, current readed line

#     transcation_df = pd.read_csv('../DATA/transaction_order.csv', encoding='utf8',
#                 dtype={'tr_date':str,'tr_time':str,'store_cd':str,'store_name':str,'pos_num':str,'receipt_num':str,'product_cd':str,'qty':int,'mount':float})

#     transcation_df = transcation_df[int_past_lines:current_line]
#     product_cd_list = list(transcation_df['product_cd'].unique())

#     products_df = get_batch_items_dynamodb(options, product_cd_list, 'product_cd')
    
#     if len(products_df) > 0:
#         merged_df = transcation_df.merge(products_df, how='left', on=['product_cd'])
#     else:        
#         new_col_list = ['division_cd','division_name','maincategory_cd','maincategory_name','subcategory_cd','subcategory_name','product_name','is_pb']
#         for new_col in new_col_list:
#             transcation_df[new_col] = ""
        
#         merged_df = transcation_df
    
#     sorted_column_list = ['tr_date', 'tr_time', 'store_cd', 'store_name', 'pos_num', 'receipt_num', 'product_cd', 'qty', 'mount', 'division_cd', 'division_name', 'maincategory_cd', 'maincategory_name', 'subcategory_cd', 'subcategory_name', 'product_name', 'is_pb']

#     merged_df = merged_df[sorted_column_list]

#     ret = [[f"{json.dumps(row.to_dict())}\n"] for idx, row in merged_df.iterrows()]

#     return ret

# def put_records_with_bulk_to_kinesis(client, options, records):
#     MAX_RETRY_COUNT = 3

#     payload_list = []
#     for data in records:
#         partition_key = 'part-{:05}'.format(random.randint(1, 1024))
#         payload_list.append({'Data': data, 'PartitionKey': partition_key})

#     for _ in range(MAX_RETRY_COUNT):
#         try:
#             response = client.put_records(Records=payload_list, StreamName=options.stream_name)

#         except Exception as e:
#             traceback.print_exc()
#             time.sleep(random.randint(1,10))
#     else:
#         raise RuntimeError('[ERROR] Failed to put_records into stream: {}'.format(options.stream_name))

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