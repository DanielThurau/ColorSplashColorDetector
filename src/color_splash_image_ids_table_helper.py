import boto3

class ColorSplashImageIdsTableHelper:
    def __init__(self, table_name):
        self.client = boto3.client('dynamodb')
        self.table_name = table_name
        self.image_ids_attribute_key = 'ImageId'
        self.full_url_attribute_key = 'FullURL'
        self.regular_url_attribute_key = 'RegularURL'
        self.small_url_attribute_key = 'SmallURL'
        self.thumbnail_url_attribute_key = 'ThumbnailURL'

    def get_key(self, key):
        '''Given a ImageId key, retrieve the remaing attributes and deserialize it into native 
        python types'''
        response = self.client.get_item(
            Key={
                self.image_ids_attribute_key: {
                    'S': key
                }
            },
            TableName=self.table_name
        )

        if 'Item' not in response:
            raise KeyError("No such key: " + key)
        else:
            return self.deserialize_urls(response['Item'])

    def deserialize_urls(self, serialized_items):
        ''' Given a row of the table, deserialize the DynamoDB specific format into python native types'''
        print(serialized_items)

        urls = {}
        for key, value in serialized_items.items():
            urls[key] = self.deserialize_string(value)

        return urls

    def deserialize_string(self, string_attribute):
        if 'S' not in string_attribute:
            raise ValueError("Missing String('S') data in attribute")  

        return string_attribute['S']

    def deserialize_imageids_attribute(self, serialized_data):
        '''Given the dynamoDB native format of the URLS attribute, deserialize it into its 
        native python type. Example input -> {'L': [{'S': 'WvlS1yWAu8c', 'S': 'zsgS1yxAu8c'}]}'''
        id_set = set()
        if 'L' not in serialized_data:
            raise KeyError('No such list key in serialized data provided')

        for item in serialized_data['L']:
            id_set.add(item['S']) 

        return id_set