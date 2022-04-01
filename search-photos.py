import json
import boto3
import urllib3

def singular(word):
    if not word:
        return
    if word.endswith('es'):
        return word[:-2]
    elif word.endswith('s'):
        return word[:-1]
    else:
        return word

def fetch_from_opensearch(keyword):
    url = "https://search-photo-album-es-cf1-pwyqbd2senqneb7wgmpqjarruy.us-east-1.es.amazonaws.com/photos/_search?q="+keyword
    ##changed
    awsauth = 'username1:Password2022!'
    http = urllib3.PoolManager()
    headers = urllib3.make_headers(basic_auth=awsauth)
    r = http.request('GET', url, headers=headers)
    return json.loads(r.data.decode('utf8'))

def search_photos(one, two, three):
    results = []
    results.append(fetch_from_opensearch(one))
    if two is not None:
        results.append(fetch_from_opensearch(two))
    if three is not None:
        results.append(fetch_from_opensearch(three))
    output = []
    unique_keys = set()
    for r in results:
        if 'hits' in r:
             for val in r['hits']['hits']:
                key = val['_source']['objectKey']
                if key not in unique_keys:
                    labels = val['_source']['labels']
                    output.append((key, labels))
                    unique_keys.add(key)
    return output
   
def generate_response(images):
    bucket_url = 'http://photo-store-cf.s3.us-east-1.amazonaws.com/'
    results = []
    for img in images:
        name, labels = img
        results.append({
            "url": bucket_url+name,
            "labels": labels
        })
    return {
        "results": results
    }

def lambda_handler(event, context):
    client = boto3.client('lex-runtime', region_name='us-east-1')
    
    response_lex = client.post_text(
    botName='photo_bot',
    botAlias="bot",
    userId="random_str",
    inputText = event["search_query"]
    )
    
    print(response_lex)
    
    dialog_state = response_lex["dialogState"]
    print(dialog_state)
    if dialog_state == 'ReadyForFulfillment' and 'slots' in response_lex:
        pass
    else:
        return {
        'statusCode': 404,
        'body': json.dumps({"message": "Elicit slots again"})
    }
    one = response_lex["slots"]["one"]
    two = response_lex["slots"]["two"]
    three = response_lex["slots"]["three"]
    one = singular(one)
    two = singular(two)
    three = singular(three)
    photos = search_photos(one, two, three)
    return generate_response(photos)
