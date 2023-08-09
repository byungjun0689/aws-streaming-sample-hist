import boto3
import argparse
import pandas as pd
import time 

def exist_dynamodb_table(options) -> bool:
    region = options.region_name
    table_name = options.dynamodb_table_name

    dynamodb = boto3.resource('dynamodb',region_name=region)
    table_list = dynamodb.tables.all()

    is_exist = any(table.name == table_name for table in table_list)

    return is_exist

def create_dynamodb_table(options):
    region = options.region_name
    table_name = options.dynamodb_table_name

    dynamodb = boto3.resource('dynamodb',region_name=region)
    response = dynamodb.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': 'product_cd',
                'AttributeType': 'S'
            },
        ],
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'product_cd',
                'KeyType': 'HASH'
            },
        ],
        BillingMode='PAY_PER_REQUEST'
    )

def put_records_to_dynamodb(options):
    region = options.region_name
    table_name = options.dynamodb_table_name

    if not exist_dynamodb_table(options):
        create_dynamodb_table(options)
        time.sleep(2)

    dynamodb = boto3.client('dynamodb', region_name=region)

    df = pd.read_csv('../DATA/products.csv', encoding='utf8', dtype={'division_cd':str,'division_name':str,'maincategory_cd':str,'maincategory_name':str,'subcategory_cd':str,'subcategory_name':str,'product_cd':str,'product_name':str,'is_pb':str})
    
    i=0      
    for idx, row in df.iterrows():
        division_cd	= (row["division_cd"])
        division_name	= (row["division_name"])
        maincategory_cd	= (row["maincategory_cd"])
        maincategory_name	= (row["maincategory_name"])
        subcategory_cd	= (row["subcategory_cd"])
        subcategory_name	= (row["subcategory_name"])
        product_cd	= (row["product_cd"])
        product_name	= (row["product_name"])
        is_pb= (row["is_pb"])
    
        response = dynamodb.put_item(
            TableName=table_name,
            Item={
                'division_cd' : {'S':division_cd},	
                'division_name' : {'S':division_name},	
                'maincategory_cd' : {'S':maincategory_cd},	
                'maincategory_name' : {'S':maincategory_name},	
                'subcategory_cd' : {'S':subcategory_cd},	
                'subcategory_name' : {'S':subcategory_name},	
                'product_cd' : {'S':product_cd},	
                'product_name' : {'S':product_name},	
                'is_pb' : {'S':is_pb}
            }
        )

        i+=1
    
    print("Total insert : ", str(i))
    print("completed")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--region-name', action='store', default='ap-northeast-2',
    help='aws region name (default: ap-northeast-2)')
    parser.add_argument('--dynamodb-table-name', default='products_info', help='The name of the dynamodb to put the data record into.')

    options = parser.parse_args()

    put_records_to_dynamodb(options)

if __name__ == "__main__":
    '''python import_productsdata_to_dynamo.py --region-name ap-northeast-2 --dynamodb-table-name products_info'''
    main()
